import pytest

from conftest import EARTH_OK, FLIGHT_OK


@pytest.mark.parametrize("lang", ["en", "ru", "zh"])
@pytest.mark.parametrize("values,visit", [(EARTH_OK, {}), (FLIGHT_OK, {"day": 18})])
def test_visit_pdf(client, lang, values, visit):
    response = client.post("/api/report.pdf", json=dict(values, series_visit=visit, lang=lang))
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF-")
    assert "attachment;" in response.headers["Content-Disposition"]
    assert f"-{lang}.pdf" in response.headers["Content-Disposition"]
    if visit:
        assert "day-18" in response.headers["Content-Disposition"]
    assert "no-store" in response.headers["Cache-Control"]
    assert b"/ToUnicode" in response.data and b"/Subtype /Image" in response.data
    assert b"mailto:immoonity@immoonity.ru" in response.data
    assert b"https://t.me/immoonity" in response.data


@pytest.mark.parametrize("extra,status,code", [
    ({"series_visit": {"day": 0}}, 400, "validation_error"),
    ({"expected_model_version": "obsolete"}, 409, "model_version_changed"),
    ({"cell_counts": {"anc": 2, "alc": 0}}, 400, "cell_counts"),
    ({"cell_counts": {"anc": 12, "alc": 2}}, 400, "cell_counts"),
])
def test_pdf_requires_consistent_inputs(client, extra, status, code):
    response = client.post("/api/report.pdf", json=dict(FLIGHT_OK, **extra))
    assert response.status_code == status
    assert response.get_json()["error"] == code


def test_pdf_uses_same_sample_cell_counts(client):
    data = dict(FLIGHT_OK, cell_counts={"anc": 4, "alc": 2})
    assert client.post("/api/report.pdf", json=data).status_code == 200
    assert client.post("/api/report.pdf", json={**EARTH_OK, **FLIGHT_OK}).status_code == 400


@pytest.mark.parametrize("lang", ["ru", "en", "zh"])
def test_baseline_note_distinguishes_absent_partial_and_complete(client, lang):
    def note(values):
        response = client.post("/predict", json=dict(values, lang=lang))
        assert response.status_code == 200
        return response.get_json()["interpretation"]["baseline_note"]

    without = {k: v for k, v in FLIGHT_OK.items() if k not in ("il6_b", "nlr_b", "cortb")}
    assert note(without) and note(dict(without, il6_b=0)) == note(without)
    assert "NLR" in note(dict(without, il6_b=2, cortb=400))
    assert note(FLIGHT_OK) is None
