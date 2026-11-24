import pytest

from conftest import EARTH_OK, FLIGHT_OK


@pytest.mark.parametrize("lang", ["en", "ru", "zh"])
@pytest.mark.parametrize("values,visit", [
    (dict(EARTH_OK, sex="F"), {}),
    (dict(FLIGHT_OK, nlr_a=7.2, il6_a=18, ebv=3000, corta=850), {"day": 75}),
    ({"nlr_a": 1, "il6_a": 1, "ebv": 0, "corta": 300, "days": 90}, {"day": 8}),
])
def test_series_language_switch_uses_the_same_prediction(client, lang, values, visit):
    payload = dict(values, series_visit=visit, lang=lang)
    response = client.post("/predict", json=dict(payload, include_translations=True))
    assert response.status_code == 200
    result = response.get_json()
    assert result["interpretation"]["language"] == lang
    assert set(result["translations"]) == {"en", "ru", "zh"} - {lang}
    for other, translated in result["translations"].items():
        comparison = client.post("/predict", json=dict(payload, lang=other)).get_json()
        assert "translations" not in comparison
        assert translated["interpretation"] == comparison["interpretation"]
        assert translated["input_warnings"] == comparison["input_warnings"]
        for field in ("risk", "risk_interval", "factors", "series_assessment"):
            assert comparison[field] == result[field]


def test_chinese_prompt_validation_and_gender(client):
    success = client.post("/predict?lang=zh-CN", json=dict(EARTH_OK, sex="女性")).get_json()
    assert success["inputs"]["sex"] == "F"
    assert "风险" in success["interpretation"]["headline"]
    error = client.post("/predict?lang=zh", json=dict(FLIGHT_OK, series_visit={"day": 0}))
    assert error.status_code == 400
    assert "飞行日" in error.get_json()["details"][0]["message"]
    prompt = client.post("/api/consultant/prompt", json=dict(EARTH_OK, lang="zh")).get_json()
    assert "中文" in prompt["system"]
