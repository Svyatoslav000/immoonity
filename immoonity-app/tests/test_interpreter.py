from immoonity_core.interpreter import interpret


def test_earth_interpretation_structure_and_logic(models):
    m = models["earth"]
    pred = m.predict({"sex": "M", "vo2max": 48.0, "pullups": 5.0, "pushups": 60.0})
    out = interpret(pred, m, "ru")
    assert out["language"] == "ru"
    assert {"headline", "level", "drivers", "what_if", "recommendations", "notes", "disclaimer", "references"} <= set(out)
    # подтягивания ниже цели -> сценарий и рекомендация по верхнему плечевому поясу
    assert [w["factor"] for w in out["what_if"]] == ["pullups"]
    assert out["what_if"][0]["risk_after"] < pred["risk"]
    assert "upper_body" in [r["id"] for r in out["recommendations"]]
    assert "aerobic" not in [r["id"] for r in out["recommendations"]]  # VO2max уже выше цели
    assert out["references"][0]["key"] == "agha2020"


def test_earth_fully_fit_gets_no_improvement_scenarios(models):
    m = models["earth"]
    pred = m.predict({"sex": "F", "vo2max": 50.0, "pullups": 10.0, "pushups": 40.0})
    out = interpret(pred, m, "en")
    assert out["what_if"] == []
    assert {r["id"] for r in out["recommendations"]} == {"maintain", "basics"}


def test_flight_pattern_and_recommendations(models):
    m = models["flight"]
    pred = m.predict({"il6_b": 2.0, "il6_a": 2.0, "nlr_b": 2.0, "nlr_a": 2.0, "ebv": 600.0, "cortb": 400.0,
                      "corta": 650.0, "days": 180.0})
    out = interpret(pred, m, "en")
    assert out["level"]["code"] == "high"
    ids = [r["id"] for r in out["recommendations"]]
    assert ids[0] == "priority" and "viral" in ids and "neuroendocrine" in ids
    assert any("Stowe" in p for p in out["pattern"])
    assert {w["factor"] for w in out["what_if"]} == {"viral", "neuroendocrine"}


def test_flight_all_normal_suggests_prevention_only(models):
    m = models["flight"]
    pred = m.predict({"il6_b": 2.0, "il6_a": 2.1, "nlr_b": 2.0, "nlr_a": 2.1, "ebv": 30.0, "cortb": 400.0,
                      "corta": 410.0, "days": 30.0})
    out = interpret(pred, m, "ru")
    assert out["level"]["code"] == "low"
    assert [r["id"] for r in out["recommendations"]] == ["prevention"]
    assert out["what_if"] == []


def test_missing_baseline_is_explained(models):
    m = models["flight"]
    pred = m.predict({"il6_a": 3.0, "nlr_a": 2.0, "ebv": 30.0, "corta": 420.0, "days": 30.0})
    out = interpret(pred, m, "ru")
    assert sum("исходного значения" in n for n in out["notes"]) == 3


def test_duration_wording_and_russian_plurals(models):
    f = models["flight"]
    storm = {"il6_b": 2.0, "il6_a": 12.0, "nlr_b": 2.0, "nlr_a": 5.0, "ebv": 2000.0, "cortb": 400.0, "corta": 700.0}
    assert "опорная" in interpret(f.predict(dict(storm, days=180.0)), f, "ru")["duration"]
    assert "почти не меняет" in interpret(f.predict(dict(storm, days=365.0)), f, "ru")["duration"]
    e = models["earth"]
    out = interpret(e.predict({"sex": "F", "vo2max": 33.0, "pullups": 2.0, "pushups": 22.0}), e, "ru")
    texts = " ".join(d["text"] for d in out["drivers"])
    assert "22 раза" in texts and "2 раза" in texts and "ориентира 3 раза" in texts and "ориентира 20 раз" in texts


def test_headline_rounds_like_the_site(models):
    """Сайт выводит интервал через toFixed(0) (половина вверх) — заголовок должен совпадать: 38.5 -> 39."""
    m = models["earth"]
    pred = m.predict({"sex": "M", "vo2max": 48.0, "pullups": 15.0, "pushups": 60.0})
    pred["risk"], pred["risk_interval"] = 62.5, {"low": 38.5, "high": 82.9, "level": 0.9}
    out = interpret(pred, m, "ru")
    assert "63% (90% интервал 39–83%)" in out["headline"]
    assert any("интервал 39–83%" in n for n in out["notes"])


def test_very_long_mission_is_flagged_and_explained(models):
    f = models["flight"]
    values = {"il6_b": 2.0, "il6_a": 2.2, "nlr_b": 1.8, "nlr_a": 2.0, "ebv": 40.0, "cortb": 400.0, "corta": 420.0,
              "days": 2000.0}
    out = interpret(f.predict(values), f, "ru")
    notes = " ".join(out["notes"])
    assert "экстраполяция" in notes and "мЗв" in notes and "600 мЗв" in notes
    assert "Стабильные маркеры" in out["duration"]
    keys = [r["key"] for r in out["references"]]
    assert {"manzey1998", "zeitlin2013", "feuerecker2019"} <= set(keys)
    short = interpret(f.predict(dict(values, days=180.0)), f, "en")
    assert "extrapolation" not in " ".join(short["notes"]) and "mSv" not in " ".join(short["notes"])

