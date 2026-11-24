import pytest

from conftest import EARTH_OK, FLIGHT_OK
from immoonity_core.evidence import FIELDS, assess_visit, load_registry, validate_registry


def artificial_registry(model="flight"):
    # Dimensionless test numbers are fixtures, never reference ranges for patients.
    intervals = [
        dict(field=k, phase=p, unit=u, sex="any", protocol="form_default", species="Homo sapiens",
             source="test fixture", status="approved", population="unit test only",
             reference_id=k, p05="10", p95="20")
        for k, (p, u, _) in FIELDS[model].items()
    ]
    reg = {"version": "test-only", "population":"unit test only", "intervals": intervals}
    validate_registry(reg)
    return reg


def measured():
    return {k: 15 for k, (_, _, required) in FIELDS["flight"].items() if required}


@pytest.mark.parametrize(("value", "status", "model"), [
    ("9.99999", "below", "human_plus_animal"), (10, "inside", "human_only"),
    (15, "inside", "human_only"), (20, "inside", "human_only"), ("20.00001", "above", "human_plus_animal")
])
def test_closed_bounds_without_display_rounding(value, status, model):
    infos = assess_visit("flight", dict(measured(), nlr_a=value), {"day": 87}, artificial_registry())
    assert infos["route"] == model
    assert next(r for r in infos["markers"] if r["field"] == "nlr_a")["status"] == status
    assert infos["total"] == infos["assessed"] == 4
    assert infos["composite"]["probability"] is None


def test_missing_does_not_erase_a_verified_outlier():
    registry = artificial_registry()
    registry["intervals"] = [r for r in registry["intervals"] if r["field"] != "nlr_a"]
    assert assess_visit("flight", measured(), {"day": 4}, registry)["route"] == "undetermined"
    info = assess_visit("flight", dict(measured(), ebv=0), {"day": 4}, registry)
    assert (info["route"], info["outside"], info["assessed"]) == ("human_plus_animal", ["ebv"], 3)
    assert assess_visit("flight", {"ebv": 15}, {"day": 4}, artificial_registry())["route"] == "undetermined"


def test_decimal_precision_at_api_boundary(monkeypatch):
    import app

    monkeypatch.setattr(app, "load_registry", lambda: artificial_registry("earth"))
    client = app.create_app().test_client()
    payload = dict(sex="F", vo2max="20,00000000000000001", pushups=15, pullups=15, series_visit={})
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    evidence = response.json["series_assessment"]
    assert evidence["route"] == "human_plus_animal"
    assert evidence["outside"] == ["vo2max"]
    assert client.post("/predict", json=dict(payload, vo2max="20,000")).json["series_assessment"]["route"] == "human_only"


def test_optional_original_sample_compared_in_its_own_phase():
    reg = artificial_registry()
    info = assess_visit("flight", dict(measured(), nlr_b=30), {"day": 3}, reg)
    assert info["outside"] == ["nlr_b"] and info["total"] == 5
    assert info["markers"][-1]["phase"] == "preflight"
    assert assess_visit("flight", dict(measured(), nlr_b=None), {"day": 3}, reg)["route"] == "human_only"


def test_protocol_time_window_and_ambiguous_references():
    reg = artificial_registry()
    band = next(r for r in reg["intervals"] if r["field"] == "corta")
    band.update(protocol="unit_test_assay", day_min=10, day_max=60)
    assert assess_visit("flight", measured(), {"day": 10}, reg)["route"] == "undetermined"
    visit = {"day": 60, "protocols": {"corta": "unit_test_assay"}}
    assert assess_visit("flight", measured(), visit, reg)["route"] == "human_only"
    assert assess_visit("flight", measured(), dict(visit, day=61), reg)["route"] == "undetermined"
    reg["intervals"].append(dict(band, reference_id="overlap"))
    assert assess_visit("flight", measured(), visit, reg)["route"] == "undetermined"


def test_fitness_sex_is_a_stratum_and_duration_is_not_a_marker():
    reg = artificial_registry("earth")
    for band in reg["intervals"]:
        band["sex"] = "F"
    vals = {"sex": "F", "vo2max": 15, "pullups": 15, "pushups": 15, "days": 200}
    got = assess_visit("earth", vals, {}, reg)
    assert got["route"] == "human_only" and got["total"] == 3
    assert assess_visit("earth", dict(vals, sex="M"), {}, reg)["route"] == "undetermined"


@pytest.mark.parametrize("change", [
    {"species":"rat"}, {"status":"exploratory"}, {"source":""}, {"p95":9}, {"p05":"NaN"},
    {"unit":"mg/dL"}, {"phase":"recovery"}, {"day_min":18,"day_max":3}
])
def test_reject_ineligible_reference_rows(change):
    reg = artificial_registry()
    reg["intervals"][0].update(change)
    with pytest.raises(ValueError):
        validate_registry(reg)


@pytest.mark.parametrize("bad", [None, 0, -1, True, 1.5, "21"])
def test_day_is_required_only_on_opted_in_flight_calls(client, bad):
    response = client.post("/predict", json=dict(FLIGHT_OK, series_visit={"day": bad}))
    assert response.status_code == 400 and response.json["details"][0]["field"] == "series_visit"


def test_api_days_and_outcomes_are_independent(monkeypatch):
    import app
    registry = {"version":"test-empty", "population":"unit test only", "intervals":[]}
    monkeypatch.setattr(app, "load_registry", lambda: registry)
    client = app.create_app().test_client()
    old = client.post("/predict", json=FLIGHT_OK).json
    assert "series_assessment" not in old
    for d in (1, 180, 193):
        response = client.post("/predict", json=dict(FLIGHT_OK, series_visit={"day":d}))
        assert response.status_code == 200
        body = response.json
        info = body["series_assessment"]
        assert body["risk"] == old["risk"] and body["inputs"]["days"] == 180
        assert info["route"] == "undetermined" and info["assessed"] == 0
        assert info["composite"]["as_of_flight_day"] == d
        assert info["composite"]["probability"] is None
    assert client.post("/predict", json=dict(EARTH_OK, series_visit={})).json["series_assessment"]["composite"]["status"] == "preflight"
    validate_registry(load_registry())


def test_protocol_parameter_is_validated(client):
    invalid = ([], {"protocols": ["A"]}, {"protocols": {"corta": 4}}, {"protocols": {"unknown": "field"}})
    for v in invalid:
        visit = dict(v, day=1) if isinstance(v, dict) else v
        assert client.post("/predict", json=dict(FLIGHT_OK, series_visit=visit)).status_code == 400
