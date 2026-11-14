"""Domain properties: monotonicity, smoothness, signs, ranges."""

import json
from pathlib import Path

import pytest

from immoonity_core.engine import soft_step

ROOT = Path(__file__).resolve().parent.parent


def risk(model, values):
    return model.predict(values)["risk"]


def frange(a, b, step):
    x = a
    while x <= b + 1e-9:
        yield round(x, 6)
        x += step


@pytest.mark.parametrize("sex,base", [("M", {"vo2max": 48, "pullups": 15, "pushups": 60}),
                                      ("F", {"vo2max": 42, "pullups": 6, "pushups": 30})])
@pytest.mark.parametrize("field,grid", [("vo2max", list(frange(20, 70, 0.5))), ("pullups", list(range(0, 31))),
                                        ("pushups", list(range(0, 101)))])
def test_earth_more_fitness_never_increases_risk(models, sex, base, field, grid):
    m = models["earth"]
    risks = [m.risk_of(m.featurize(dict(base, sex=sex, **{field: float(x)}))[0]) for x in grid]
    assert all(b <= a + 1e-12 for a, b in zip(risks, risks[1:])), f"{field} increased risk"


@pytest.mark.parametrize("field,grid", [("il6_a", list(frange(0.5, 20, 0.1))), ("nlr_a", list(frange(0.5, 8, 0.05))),
                                        ("ebv", list(frange(0, 2000, 5))), ("corta", list(frange(100, 900, 2))),
                                        ("days", list(frange(1, 1000, 1)))])
def test_flight_worse_marker_or_longer_mission_never_decreases_risk(models, field, grid):
    m = models["flight"]
    base = {"il6_b": 2.0, "il6_a": 2.2, "nlr_b": 1.8, "nlr_a": 2.0, "ebv": 40.0, "cortb": 400.0, "corta": 420.0,
            "days": 180.0}
    risks = [m.risk_of(m.featurize(dict(base, **{field: float(x)}))[0]) for x in grid]
    assert all(b >= a - 1e-12 for a, b in zip(risks, risks[1:])), f"{field} decreased risk"


def test_no_jumps_at_thresholds(models):
    m = models["earth"]
    base = {"sex": "M", "pullups": 15, "pushups": 60}
    jumps = [abs(risk(m, dict(base, vo2max=x + 0.25)) - risk(m, dict(base, vo2max=x))) for x in frange(30, 60, 0.25)]
    assert max(jumps) < 1.0


def test_coefficient_signs_match_theory(models):
    e, f = models["earth"], models["flight"]
    assert e.coef("fitness_index") < 0
    assert f.coef("dysregulation_score") > 0
    assert f.coef("duration_log2") > 0
    assert all(c["weight"] > 0 for c in e.components.values())
    assert all(mk["weight"] > 0 for mk in f.markers.values())


def test_risk_ranges_are_sensible(models):
    e, f = models["earth"], models["flight"]
    fit = risk(e, {"sex": "F", "vo2max": 45, "pullups": 8, "pushups": 35})
    unfit = risk(e, {"sex": "M", "vo2max": 30, "pullups": 0, "pushups": 5})
    assert 40 < fit < 70 and 80 < unfit < 98 and fit < unfit
    calm = risk(f, {"il6_b": 2, "il6_a": 2, "nlr_b": 2, "nlr_a": 2, "ebv": 20, "cortb": 400, "corta": 400, "days": 180})
    storm = risk(f, {"il6_b": 2, "il6_a": 12, "nlr_b": 2, "nlr_a": 5, "ebv": 2000, "cortb": 400, "corta": 700, "days": 180})
    assert calm < 15 and storm > 95


def test_two_systems_outweigh_one(models):
    f = models["flight"]
    base = {"il6_b": 2, "il6_a": 2, "nlr_b": 2, "nlr_a": 2, "ebv": 20, "cortb": 400, "corta": 400, "days": 180}
    one = risk(f, dict(base, corta=650))
    two = risk(f, dict(base, corta=650, ebv=600))
    assert two > one + 30


def test_relative_rise_within_normal_variation_is_not_flagged(models):
    """A 20% IL-6 rise is within normal variation (CVi 30–48%)."""
    f = models["flight"]
    p = f.predict({"il6_b": 2.0, "il6_a": 2.4, "nlr_b": 2, "nlr_a": 2, "ebv": 20, "cortb": 400, "corta": 400, "days": 180})
    assert p["details"]["markers"]["cytokine"]["status"] == "below"


def test_soft_step_basics():
    assert soft_step(10, 10, 1) == pytest.approx(0.5)
    assert soft_step(14, 10, 1) > 0.98 and soft_step(6, 10, 1) < 0.02


def test_interval_contains_point_estimate(models):
    for name, values in (("earth", {"sex": "M", "vo2max": 40, "pullups": 9, "pushups": 40}),
                         ("flight", {"il6_a": 8, "nlr_a": 3, "ebv": 150, "corta": 500, "days": 90})):
        p = models[name].predict(values)
        assert p["risk_interval"]["low"] <= p["risk"] <= p["risk_interval"]["high"]


def test_json_models_match_training_output(models):
    from training import config
    metrics = json.loads((ROOT / "reports" / "metrics.json").read_text(encoding="utf-8"))
    earth = models["earth"]
    for term in earth.terms:
        assert earth.coef(term) == pytest.approx(metrics["posterior"]["earth"][term]["mean"], abs=1e-9)
    mean, cov = config.flight_parameters()
    flight = models["flight"]
    assert flight.beta == pytest.approx(mean, abs=1e-9)
    assert flight.cov == [pytest.approx(row, abs=1e-12) for row in cov]


def test_flight_duration_effect_comes_from_published_shedding_rates(models):
    """Rooney 2019: viral shedding on short flights vs the ISS -> effect per doubling of mission length."""
    from training import config
    assert config.DURATION_EFFECTS == pytest.approx({"any": 0.089, "VZV": 0.266, "EBV": 0.45, "CMV": 0.154}, abs=1e-3)
    assert models["flight"].coef("duration_log2") == pytest.approx(0.21)


STABLE = {"il6_b": 2.0, "il6_a": 2.2, "nlr_b": 1.8, "nlr_a": 2.0, "ebv": 40.0, "cortb": 400.0, "corta": 420.0}


def test_stable_markers_on_a_very_long_mission(models):
    f = models["flight"]
    stable_180, stable_2000 = risk(f, dict(STABLE, days=180)), risk(f, dict(STABLE, days=2000))
    shifted_180 = risk(f, dict(STABLE, corta=600, days=180))
    shifted_2000 = risk(f, dict(STABLE, corta=600, days=2000))
    assert stable_180 < stable_2000 < 25
    assert stable_2000 - stable_180 < shifted_2000 - shifted_180


def test_interval_widens_beyond_the_longest_flight(models):
    f = models["flight"]
    preds = {d: f.predict(dict(STABLE, days=float(d))) for d in (180, 300, 437, 2000)}
    width = {d: p["risk_interval"]["high"] - p["risk_interval"]["low"] for d, p in preds.items()}
    codes = {d: [w["code"] for w in p["warnings"]] for d, p in preds.items()}
    assert codes[180] == [] and codes[300] == ["duration_limited_evidence"]
    assert codes[2000] == ["duration_beyond_evidence"]
    x = f.featurize(dict(STABLE, days=2000.0))[0]
    assert f._eta_sd(x) > super(type(f), f)._eta_sd(x) * 1.1
    assert width[2000] > width[437] > width[180]


def test_committed_report_checks_pass():
    checks = json.loads((ROOT / "reports" / "metrics.json").read_text(encoding="utf-8"))["flight_checks"]
    assert checks["leakage"]["share"] > 0.8
    assert checks["duration"]["multisystem"]["model_within_90"] and checks["duration"]["viral"]["model_within_90"]
    for marker in ("nlr", "il6"):
        v = checks["variability"][marker]
        assert abs(v["observed_within_person_cv"] - v["assumed_total_cv"]) < 0.05, marker
    assert checks["inspiration4"]["nlr"]["flagged"] == 0
    assert checks["inspiration4"]["il6"]["flagged"] == 2
