"""Checks of the in-flight model on data without target leakage."""

from __future__ import annotations

import math
import statistics as st

import numpy as np

import bayes
import config as C

FLAG_COLUMNS = ("has_cytokine_response", "has_immune_cell_shift", "has_viral_reactivation",
                "has_neuroendocrine_change")
NOT_A_GROUP_RESULT = ("mission_days_0", "review_article_not_primary", "mission_days_includes_postflight",
                      "non_spaceflight")
PREFLIGHT = ("L-92", "L-44", "L-3")

# Inspiration4 markers (NASA OSDR): file column, model fields and subsystem
I4_MARKERS = {
    "nlr": {"column": "nlr", "before": "nlr_b", "after": "nlr_a", "subsystem": "immune_shift"},
    "il6": {"column": "il6_pg_ml", "before": "il6_b", "after": "il6_a", "subsystem": "cytokine"},
}


def leakage(rows: list[dict]) -> dict:
    same = sum(int(r["outcome_severity_score"]) == sum(int(r[c]) for c in FLAG_COLUMNS) for r in rows)
    return {"rows": len(rows), "score_equals_flag_sum": same, "share": round(same / len(rows), 3)}


def spaceflight_groups(rows: list[dict]) -> list[dict]:
    keep = [r for r in rows if r["mission_type"].startswith("Spaceflight")
            and not any(flag in r["qc_flags"] for flag in NOT_A_GROUP_RESULT)]
    return keep


def duration(rows: list[dict]) -> dict:
    groups = spaceflight_groups(rows)
    # Inspiration4 (4 people) appears in several papers, so it counts as one group
    same = [r for r in groups if "same_cohort" in r["qc_flags"]]
    w = np.array([1.0 / len(same) if r in same else 1.0 for r in groups])
    x = np.array([math.log2((float(r["mission_days"]) + 1) / (C.FLIGHT["duration"]["reference_days"] + 1))
                  for r in groups])
    X = np.column_stack([np.ones(len(x)), x])
    out = {"groups": len(groups), "weighted_n": round(float(w.sum()), 2),
           "model_value": {"mean": C.DURATION_MEAN, "sd": C.DURATION_SD}}
    for name, y in (("multisystem", [int(int(r["outcome_severity_score"]) >= 2) for r in groups]),
                    ("viral", [int(r["has_viral_reactivation"]) for r in groups])):
        post = bayes.fit_map(X, np.array(y), ["intercept", "duration_log2"], np.zeros(2), np.full(2, 2.5), weights=w)
        slope, sd = float(post.mean[1]), float(post.sd[1])
        out[name] = {"slope_per_doubling": round(slope, 3), "sd": round(sd, 3),
                     "model_within_90": abs(slope - C.DURATION_MEAN) <= 1.645 * math.hypot(sd, C.DURATION_SD)}
    return out


def _by_subject(rows: list[dict], column: str) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for r in rows:
        out.setdefault(r["subject_id"], {})[r["timepoint"]] = float(r[column])
    return out


def variability(rows: list[dict], marker: str) -> dict:
    """Within-person variability over three pre-flight draws vs the variability assumed in the RCV."""
    cvs = []
    for series in _by_subject(rows, I4_MARKERS[marker]["column"]).values():
        pre = [series[t] for t in PREFLIGHT if t in series]
        cvs.append(st.stdev(pre) / st.mean(pre))
    observed = math.sqrt(sum(c * c for c in cvs) / len(cvs))
    assumed = math.hypot(C.BIOVAR[marker]["cvi"], C.ASSAY_CV)
    return {"subjects": len(cvs), "draws_per_subject": len(PREFLIGHT),
            "observed_within_person_cv": round(observed, 3), "assumed_total_cv": round(assumed, 3),
            "per_subject_cv": [round(c, 3) for c in cvs]}


def inspiration4(rows: list[dict], marker: str, model) -> dict:
    """Value at R+1 vs the mean of three pre-flight draws, and the model's decision for the subsystem."""
    m = I4_MARKERS[marker]
    crew, flagged_l3 = [], 0
    for sid, series in sorted(_by_subject(rows, m["column"]).items()):
        before, after = st.mean(series[t] for t in PREFLIGHT), series["R+1"]
        state = model._marker_states({m["before"]: before, m["after"]: after})[m["subsystem"]]
        crew.append({"subject": sid, "before": round(before, 3), "r1": round(after, 3),
                     "change_pct": round((after / before - 1) * 100, 1), "membership": round(state["membership"], 3)})
        # with the draw 3 days before launch as the baseline
        last = model._marker_states({m["before"]: series["L-3"], m["after"]: after})[m["subsystem"]]
        flagged_l3 += last["membership"] >= 0.5
    return {"mission_days": 3, "threshold_pct": round(C.RCV[marker] * 100, 1), "crew": crew,
            "flagged": sum(c["membership"] >= 0.5 for c in crew), "flagged_with_baseline_L-3": flagged_l3}


def run_all(agg_rows: list[dict], i4_rows: dict[str, list[dict]], flight_model) -> dict:
    return {
        "leakage": leakage(agg_rows),
        "duration": duration(agg_rows),
        "variability": {k: variability(rows, k) for k, rows in i4_rows.items()},
        "inspiration4": {k: inspiration4(rows, k, flight_model) for k, rows in i4_rows.items()},
    }
