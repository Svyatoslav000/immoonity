"""Build the models: python training/train_models.py

The earth model is fitted to Agha et al. 2020; the in-flight model is assembled from the parameters in config.py.
Output: models/*.json, reports/metrics.json, reports/figures/*.png.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np

import bayes
import checks
import config as C
import data as D

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from immoonity_core.engine import EarthModel, FlightModel, load_model

DATA = ROOT / "data"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"
FIG = REPORTS / "figures"

# exp overflow under near-complete separation is expected
warnings.filterwarnings("ignore", category=RuntimeWarning)


def priors_for(cfg: dict, override: dict | None = None, scale: float = 1.0):
    pri = copy.deepcopy(cfg["priors"])
    for term, val in (override or {}).items():
        if term in pri:
            pri[term].update(val)
    mu = np.array([pri[t]["mean"] for t in cfg["terms"]], float)
    sd = np.array([pri[t]["sd"] for t in cfg["terms"]], float) * scale
    return mu, sd


def parse_variant(spec):
    """Sensitivity variant -> (prior overrides, SD multiplier, weights)."""
    if isinstance(spec, str) and spec.startswith("scale_sd:"):
        return None, float(spec.split(":")[1]), None
    spec = dict(spec)
    weights = spec.pop("weights", None)
    return (spec or None), 1.0, weights


def brier(p, y):
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def logloss(p, y):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def auc(p, y):
    """ROC AUC via the Mann-Whitney statistic (ties count as 1/2)."""
    p = np.asarray(p, float)
    y = np.asarray(y).astype(int)
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    greater = (pos[:, None] > neg[None, :]).sum()
    ties = (pos[:, None] == neg[None, :]).sum()
    return float((greater + 0.5 * ties) / (len(pos) * len(neg)))


def bootstrap_ci(p, y, fn, n=2000, seed=C.RANDOM_SEED):
    rng = np.random.default_rng(seed)
    p, y = np.asarray(p), np.asarray(y)
    vals = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        if 0 < y[idx].sum() < len(idx):
            vals.append(fn(p[idx], y[idx]))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def metrics_block(p, y):
    return {
        "auc": auc(p, y), "auc_ci95": bootstrap_ci(p, y, auc),
        "brier": brier(p, y), "brier_ci95": bootstrap_ci(p, y, brier),
        "logloss": logloss(p, y),
        "calibration_in_the_large": float(np.mean(p) - np.mean(y)),
    }


def flight_posterior(cfg: dict, **override) -> bayes.Posterior:
    """In-flight model parameters from config.py as a Posterior."""
    mean, cov = C.flight_parameters(**override)
    pm = np.array([cfg["priors"][t]["mean"] for t in cfg["terms"]], float)
    ps = np.array([cfg["priors"][t]["sd"] for t in cfg["terms"]], float)
    return bayes.Posterior(terms=cfg["terms"], mean=np.array(mean, float), cov=np.array(cov, float),
                           prior_mean=pm, prior_sd=ps, n_iter=0, converged=True, loglik=float("nan"),
                           n=0, events=0)


METHODS = {
    "earth": "Bayesian logistic regression: MAP estimate, Laplace-approximation intervals.",
    "flight": "Knowledge-based model: parameters come from published studies and explicit assumptions "
              "(training/config.py), no fitting; the interval reflects the uncertainty of these assumptions "
              "and widens further beyond the longest spaceflight.",
}


def make_spec(name: str, cfg: dict, post: bayes.Posterior, weights: dict | None = None,
              training: dict | None = None, validation: dict | None = None) -> dict:
    z95 = 1.959963984540054
    summary = {}
    for i, t in enumerate(cfg["terms"]):
        m, s = float(post.mean[i]), float(post.sd[i])
        summary[t] = {"mean": round(m, 4), "sd": round(s, 4),
                      "ci95": [round(m - z95 * s, 4), round(m + z95 * s, 4)],
                      "odds_ratio": round(math.exp(m), 4)}
        if name == "earth":
            summary[t]["prior"] = {"mean": float(post.prior_mean[i]), "sd": float(post.prior_sd[i])}
    spec = {
        "model": name,
        "version": C.MODEL_VERSION,
        "created": dt.date.today().isoformat(),
        "outcome": cfg["outcome"],
        "inputs": cfg["inputs"],
        "terms": cfg["terms"],
        "coefficients": [float(v) for v in post.mean],
        "covariance": [[float(v) for v in row] for row in post.cov],
        "coefficient_summary": summary,
        "interval_level": C.INTERVAL_LEVEL,
        "risk_levels": cfg["risk_levels"],
        "priors": cfg["priors"],
        "method": METHODS[name],
    }
    refs = set()
    for p in cfg["priors"].values():
        refs.update(p.get("refs", []))
    if name == "earth":
        comps = copy.deepcopy(cfg["components"])
        for k, w in (weights or {}).items():
            comps[k]["weight"] = w
        spec["components"] = comps
        refs.update({"agha2020", "chastin2021"})
    else:
        marks = copy.deepcopy(cfg["markers"])
        for k, w in (weights or {}).items():
            marks[k]["weight"] = w
        for mk in marks.values():
            mk.pop("column", None)
            refs.update(mk.get("refs", []))
        spec["markers"] = marks
        for key in ("duration", "evidence", "radiation"):
            spec[key] = cfg[key]
            refs.update(cfg[key].get("refs", []))
        refs.update({"crucian2018", "pierson2005", "rooney2019"})
    spec["references"] = {k: C.REFERENCES[k] for k in sorted(refs)}
    if training:
        spec["training"] = training
    if validation:
        spec["validation"] = validation
    return spec


def engine_for(name, cfg, post, weights=None):
    spec = make_spec(name, cfg, post, weights)
    return EarthModel(spec) if name == "earth" else FlightModel(spec)


# Typical profiles for sensitivity analysis and interval checks
EARTH_PROFILES = {
    "M_fit": {"sex": "M", "vo2max": 48, "pullups": 15, "pushups": 60},
    "M_aerobic": {"sex": "M", "vo2max": 48, "pullups": 4, "pushups": 25},
    "M_strength": {"sex": "M", "vo2max": 38, "pullups": 15, "pushups": 60},
    "M_at": {"sex": "M", "vo2max": 43, "pullups": 10, "pushups": 45},
    "M_unfit": {"sex": "M", "vo2max": 35, "pullups": 3, "pushups": 20},
    "F_fit": {"sex": "F", "vo2max": 42, "pullups": 6, "pushups": 30},
    "F_unfit": {"sex": "F", "vo2max": 30, "pullups": 0, "pushups": 10},
}
FLIGHT_BASE = {"il6_b": 2.0, "il6_a": 2.2, "nlr_b": 1.8, "nlr_a": 2.0, "ebv": 40.0, "cortb": 400.0,
               "corta": 420.0, "days": 180.0}
FLIGHT_PROFILES = {
    "stable": {},
    "stable_437": {"days": 437.0},
    "stable_2000": {"days": 2000.0},
    "neuro": {"corta": 600.0},
    "immune": {"nlr_a": 4.0},
    "cyto": {"il6_a": 9.0},
    "viral417": {"ebv": 417.0},
    "neuro_2000": {"corta": 600.0, "days": 2000.0},
    "neuro_viral": {"corta": 600.0, "ebv": 417.0},
    "cyto_immune": {"il6_a": 9.0, "nlr_a": 4.0},
    "all": {"il6_a": 9.0, "nlr_a": 4.0, "ebv": 1000.0, "corta": 650.0},
    "neuro_14": {"corta": 600.0, "days": 14.0},
}


def flight_values(delta):
    return dict(FLIGHT_BASE, **delta)


def earth_validation(E, earth_rows):
    """Leave-one-out cross-validation."""
    X, y = D.earth_table(earth_rows, E)
    mu, sd = priors_for(E)
    loo = np.zeros(len(y))
    for i in range(len(y)):
        tr = np.arange(len(y)) != i
        loo[i] = bayes.predict(bayes.fit_map(X[tr], y[tr], E["terms"], mu, sd), X[i:i + 1])[0]
    return {"scheme": f"leave-one-out ({len(y)} folds)", "cv": metrics_block(loo, y)}


def earth_sensitivity(E, earth_rows):
    out = {}
    for vname, vspec in [("main", {})] + list(E["sensitivity"].items()):
        ov, scale, weights = parse_variant(vspec)
        X, y = D.earth_table(earth_rows, E, weights)
        mu, sd = priors_for(E, ov, scale)
        post = bayes.fit_map(X, y, E["terms"], mu, sd)
        eng = engine_for("earth", E, post, weights)
        out[vname] = {"coef": post.mean.round(3).tolist(), "sd": post.sd.round(3).tolist(),
                      "profiles": {k: eng.predict(v)["risk"] for k, v in EARTH_PROFILES.items()}}
    return out


def flight_scenarios(F):
    """Risks of typical profiles under alternative assumptions."""
    out = {}
    for vname, vspec in [("main", {})] + list(F["scenarios"].items()):
        vspec = dict(vspec)
        weights = vspec.pop("weights", None)
        post = flight_posterior(F, **vspec)
        eng = engine_for("flight", F, post, weights)
        out[vname] = {"coef": post.mean.round(3).tolist(),
                      "profiles": {k: eng.predict(flight_values(d))["risk"] for k, d in FLIGHT_PROFILES.items()}}
    return out


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    E, F = C.EARTH, C.FLIGHT

    earth_rows = D.read_csv(DATA / E["data_file"])
    agg_rows = D.read_csv(DATA / F["data_file"])
    i4_rows = {k: D.read_csv(DATA / f) for k, f in F["check_files"].items()}

    Xe, ye = D.earth_table(earth_rows, E)
    mu_e, sd_e = priors_for(E)
    post_e = bayes.fit_map(Xe, ye, E["terms"], mu_e, sd_e)
    assert post_e.converged
    post_f = flight_posterior(F)

    val_e = earth_validation(E, earth_rows)
    val_e["apparent"] = metrics_block(bayes.predict(post_e, Xe), ye)
    flight_checks = checks.run_all(agg_rows, i4_rows, engine_for("flight", F, post_f))
    lk = flight_checks["leakage"]
    val_f = {
        "scheme": "not applicable: no independent outcome data",
        "reason": f"In {F['data_file']} the outcome equals the sum of the input flags in {lk['score_equals_flag_sum']} of "
                  f"{lk['rows']} rows (target leakage), so accuracy metrics on it are not informative.",
        "checks": "reports/metrics.json -> flight_checks",
    }

    training = {
        "earth": {"data_file": "data/" + E["data_file"], "n": post_e.n, "events": post_e.events,
                  "source": "Agha et al. 2020 (doi 10.1096/fj.201902327R), 22 ISS crew members"},
        "flight": {"method": "not fitted",
                   "check_files": ["data/" + F["data_file"]] + ["data/" + f for f in F["check_files"].values()]},
    }
    cv = val_e["cv"]
    validations = {"earth": {"scheme": val_e["scheme"], **{k: round(cv[k], 4) for k in ("auc", "brier", "logloss")}},
                   "flight": val_f}
    for name, cfg, post in (("earth", E, post_e), ("flight", F, post_f)):
        spec = make_spec(name, cfg, post, training=training[name], validation=validations[name])
        (MODELS / f"{name}_model.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    em = load_model(MODELS / "earth_model.json")
    fm = load_model(MODELS / "flight_model.json")

    x_e = {k: np.array(em.featurize(v)[0]) for k, v in EARTH_PROFILES.items()}
    profiles = {
        "earth": {k: {"inputs": v, **{f: em.predict(v)[f] for f in ("risk", "risk_interval", "level")}}
                  for k, v in EARTH_PROFILES.items()},
        "flight": {k: {"inputs": flight_values(d), **{f: fm.predict(flight_values(d))[f]
                                                      for f in ("risk", "risk_interval", "level")}}
                   for k, d in FLIGHT_PROFILES.items()},
    }
    metrics = {
        "version": C.MODEL_VERSION,
        "created": dt.date.today().isoformat(),
        "posterior": {"earth": {t: {"mean": float(post_e.mean[i]), "sd": float(post_e.sd[i]),
                                    "prior_mean": float(post_e.prior_mean[i]), "prior_sd": float(post_e.prior_sd[i])}
                                for i, t in enumerate(E["terms"])}},
        "flight_parameters": {
            "coefficients": dict(zip(F["terms"], post_f.mean.tolist())),
            "sd": dict(zip(F["terms"], post_f.sd.tolist())),
            "assumptions": {"q_late": C.Q_LATE, "p_met": C.P_MET,
                            "duration_effects_per_doubling": C.DURATION_EFFECTS},
        },
        "validation": {"earth": val_e, "flight": val_f},
        "flight_checks": flight_checks,
        "laplace_check": {"earth": bayes.importance_check(post_e, Xe, ye, x_e, seed=C.RANDOM_SEED)},
        "profiles": profiles,
        "sensitivity": {"earth": earth_sensitivity(E, earth_rows)},
        "scenarios": {"flight": flight_scenarios(F)},
    }
    (REPORTS / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    figures(em, fm, post_e, post_f)

    print("earth: " + ", ".join(f"{t} {m:+.3f}" for t, m in zip(post_e.terms, post_e.mean))
          + f" | LOO AUC {cv['auc']:.3f}, Brier {cv['brier']:.3f}")
    print("flight: " + ", ".join(f"{t} {m:+.3f}" for t, m in zip(post_f.terms, post_f.mean)) + " | not fitted")
    d = flight_checks["duration"]
    print(f"checks: leakage {lk['score_equals_flag_sum']}/{lk['rows']}; duration slope in data "
          f"{d['multisystem']['slope_per_doubling']:+.2f} (viral {d['viral']['slope_per_doubling']:+.2f}) vs model "
          f"{C.DURATION_MEAN:+.2f}; " + "; ".join(
              f"{k} CV {v['observed_within_person_cv']:.3f} vs {v['assumed_total_cv']:.3f}, R+1 flagged "
              f"{flight_checks['inspiration4'][k]['flagged']}/4" for k, v in flight_checks["variability"].items()))
    print("saved:", MODELS / "earth_model.json", MODELS / "flight_model.json", REPORTS / "metrics.json")


# Figure style
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"


def _style(ax, title=None):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(1)
    ax.grid(True, color=GRID, linewidth=1, linestyle="-")
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelcolor=INK2, labelsize=9)
    if title:
        ax.set_title(title, color=INK, fontsize=11, loc="left", pad=10)


def figures(em, fm, post_e, post_f):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE})

    # risk vs VO2max
    fig, ax = plt.subplots(figsize=(8, 4.2))
    _style(ax, "Earth model: risk vs VO₂max (90% interval)")
    grid = np.arange(25, 60.01, 0.1)
    setups = {"M": ({"pullups": 15, "pushups": 60}, S1, "Men"), "F": ({"pullups": 6, "pushups": 30}, S2, "Women")}
    for sex, (fixed, colr, lab) in setups.items():
        ys, lo, hi = [], [], []
        for x in grid:
            xv = em.featurize(dict(fixed, sex=sex, vo2max=float(x)))[0]
            ys.append(em.risk_of(xv) * 100)
            a, b = em.interval_of(xv)
            lo.append(a * 100)
            hi.append(b * 100)
        ax.fill_between(grid, lo, hi, color=colr, alpha=0.10, linewidth=0)
        ax.plot(grid, ys, color=colr, lw=2, label=lab)
        ax.annotate(lab, (grid[-1], ys[-1]), xytext=(4, 0), textcoords="offset points", va="center", fontsize=9, color=INK2)
    ax.set_xlim(25, 63)
    ax.set_ylim(0, 100)
    ax.set_xlabel("VO₂max, ml/kg/min (pull-ups and push-ups above targets)", color=INK2, fontsize=9)
    ax.set_ylabel("Reactivation risk, %", color=INK2, fontsize=9)
    ax.legend(loc="lower left", frameon=False, fontsize=9, labelcolor=INK2)
    fig.tight_layout()
    fig.savefig(FIG / "earth_vo2max.png", dpi=150)
    plt.close(fig)

    # coefficients: earth — prior and posterior, in-flight — set values
    labels = {"intercept": "Intercept", "fitness_index": "Fitness index", "sex_male": "Male",
              "dysregulation_score": "Subsystem score", "duration_log2": "Mission length (per doubling)"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    panels = ((axes[0], post_e, "Earth model (fitted to 22 astronauts)", True),
              (axes[1], post_f, "In-flight model (parameters from literature)", False))
    for ax, post, title, fitted in panels:
        _style(ax, title)
        terms = post.terms[::-1]
        for j, t in enumerate(terms):
            i = post.terms.index(t)
            qm, qs = post.mean[i], post.sd[i]
            off = -0.17 if fitted else 0.0
            if fitted:
                pm, ps = post.prior_mean[i], post.prior_sd[i]
                ax.plot([pm - 1.96 * ps, pm + 1.96 * ps], [j + 0.17] * 2, color=S2, lw=2, solid_capstyle="round")
                ax.plot(pm, j + 0.17, "o", ms=8, color=S2, mec=SURFACE, mew=2,
                        label="Prior (95%)" if j == 0 else None)
            ax.plot([qm - 1.96 * qs, qm + 1.96 * qs], [j + off] * 2, color=S1, lw=2, solid_capstyle="round")
            ax.plot(qm, j + off, "o", ms=8, color=S1, mec=SURFACE, mew=2,
                    label="Posterior / set value (95%)" if (j == 0 and fitted) else None)
            ax.annotate(f"{qm:+.2f}", (qm, j + off), xytext=(0, -13), textcoords="offset points", ha="center",
                        fontsize=8, color=INK2)
        ax.set_yticks(range(len(terms)))
        ax.set_yticklabels([labels[t] for t in terms], color=INK2)
        ax.axvline(0, color=AXIS, lw=1)
        ax.set_xlabel("Coefficient (log-odds)", color=INK2, fontsize=9)
        ax.set_ylim(-0.7, len(terms) - 0.3)
    handles, labs = axes[0].get_legend_handles_labels()
    fig.legend(handles, labs, loc="lower center", ncol=2, frameon=False, fontsize=9, labelcolor=INK2)
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(FIG / "weights_prior_vs_posterior.png", dpi=150)
    plt.close(fig)

    # risk vs mission length
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    _style(ax, "In-flight model: risk and 90% interval vs mission length")
    longest = fm.evidence["longest_flight_days"]
    ax.axvspan(longest, 3000, color=GRID, alpha=0.6, linewidth=0)
    ax.annotate("beyond the longest\nspaceflight", (longest * 1.08, 4), fontsize=8, color=INK2)
    ax.axvline(180, color=AXIS, lw=1, linestyle="--")
    days = np.unique(np.round(np.logspace(0, math.log10(3000), 220)))
    curves = [("No shifts", {}, S1, True), ("Cortisol ↑", {"corta": 600.0}, S2, False),
              ("EBV 417 copies/mL", {"ebv": 417.0}, S3, False), ("Cortisol ↑ + EBV", {"corta": 600.0, "ebv": 417.0}, S4, True)]
    for lab, delta, colr, band in curves:
        xs = [fm.featurize(flight_values(dict(delta, days=float(d))))[0] for d in days]
        ys = [fm.risk_of(x) * 100 for x in xs]
        if band:
            iv = [fm.interval_of(x) for x in xs]
            ax.fill_between(days, [a * 100 for a, _ in iv], [b * 100 for _, b in iv], color=colr, alpha=0.10,
                            linewidth=0)
        ax.plot(days, ys, color=colr, lw=2, label=lab)
    ax.set_xscale("log")
    ax.set_xlim(1, 3000)
    ax.set_xticks([1, 3, 10, 30, 90, 180, 437, 1000, 2000])
    ax.set_xticklabels(["1", "3", "10", "30", "90", "180", "437", "1000", "2000"])
    ax.set_ylim(0, 100)
    ax.set_xlabel("Mission length, days (log scale)", color=INK2, fontsize=9)
    ax.set_ylabel("Risk, %", color=INK2, fontsize=9)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=4, frameon=False, fontsize=8, labelcolor=INK2)
    fig.tight_layout()
    fig.savefig(FIG / "flight_duration.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
