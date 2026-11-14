import importlib.util
import re
from pathlib import Path

import pytest

from conftest import EARTH_OK, FLIGHT_OK


def test_health_and_root(client):
    for url in ("/", "/api/health"):
        r = client.get(url)
        assert r.status_code == 200
        assert r.get_json()["status"] == "ok"


def test_model_cards_are_public_and_complete(client):
    cards = client.get("/api/models").get_json()
    assert set(cards) == {"earth", "flight"}
    for card in cards.values():
        assert {"outcome", "inputs", "coefficients", "coefficient_summary", "priors", "references",
                "validation"} <= set(card)


def test_string_values_are_accepted(client):
    """The site sends values as strings and reads the risk field."""
    for payload in (EARTH_OK, FLIGHT_OK):
        r = client.post("/predict", json=payload)
        assert r.status_code == 200
        body = r.get_json()
        assert isinstance(body["risk"], float) and 0 < body["risk"] < 100
        assert body["interpretation"]["headline"]


def test_cors_header_present(client):
    r = client.post("/predict", json=EARTH_OK, headers={"Origin": "https://example.org"})
    assert r.headers.get("Access-Control-Allow-Origin") in ("*", "https://example.org")


def test_zero_or_missing_baseline_does_not_crash(client):
    for patch in ({"il6_b": "0"}, {"cortb": "0", "nlr_b": "0"}, {"il6_b": "", "nlr_b": "", "cortb": ""}):
        r = client.post("/predict", json=dict(FLIGHT_OK, **patch))
        assert r.status_code == 200, r.get_json()
        assert r.get_json()["warnings"]


def test_missing_required_field_is_a_clear_400(client):
    r = client.post("/predict", json=dict(EARTH_OK, vo2max=""))
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "validation_error"
    assert body["details"][0]["field"] == "vo2max" and body["details"][0]["code"] == "required"


def test_non_numeric_and_out_of_range_values(client):
    r = client.post("/predict", json=dict(EARTH_OK, vo2max="abc", pushups="-5"))
    assert r.status_code == 400
    codes = {d["field"]: d["code"] for d in r.get_json()["details"]}
    assert codes == {"vo2max": "not_a_number", "pushups": "below_min"}


def test_decimal_comma_is_accepted(client):
    r = client.post("/predict", json=dict(FLIGHT_OK, nlr_a="4,2"))
    assert r.status_code == 200
    assert r.get_json()["inputs"]["nlr_a"] == 4.2


def test_implausible_values_warn_but_work(client):
    r = client.post("/predict", json=dict(EARTH_OK, vo2max="105"))  # above the maximum (100)
    assert r.status_code == 400 and r.get_json()["details"][0]["code"] == "above_max"
    r = client.post("/predict", json=dict(EARTH_OK, vo2max="88"))  # allowed, but outside the usual 15–85
    assert r.status_code == 200
    assert r.get_json()["input_warnings"][0]["code"] == "implausible"


def test_sex_aliases(client):
    for alias in ("f", "female", "Ж", "женский"):
        r = client.post("/predict", json=dict(EARTH_OK, sex=alias))
        assert r.status_code == 200 and r.get_json()["inputs"]["sex"] == "F"
    r = client.post("/predict", json=dict(EARTH_OK, sex="x"))
    assert r.status_code == 400


def test_bad_bodies(client):
    assert client.post("/predict", data="not json", content_type="text/plain").status_code == 400
    assert client.post("/predict", json=[1, 2]).status_code == 400
    r = client.post("/predict", json={})
    assert r.status_code == 400 and r.get_json()["error"] == "no_inputs"
    r = client.post("/predict", json={"sex": "M"})  # empty earth form
    assert r.status_code == 400
    assert client.post("/predict", json=dict(EARTH_OK, model="mars")).status_code == 400


def test_both_models_in_one_request(client):
    r = client.post("/predict", json=dict(EARTH_OK, **FLIGHT_OK))
    assert r.status_code == 200
    assert set(r.get_json()["results"]) == {"earth", "flight"}


def test_language_selection(client):
    cyr = re.compile("[а-яА-Я]")
    ru = client.post("/predict?lang=ru", json=EARTH_OK).get_json()["interpretation"]
    en = client.post("/predict", json=dict(EARTH_OK, lang="en")).get_json()["interpretation"]
    assert cyr.search(ru["headline"]) and not cyr.search(en["headline"])
    err = client.post("/predict?lang=ru", json=dict(EARTH_OK, vo2max="")).get_json()
    assert cyr.search(err["details"][0]["message"])


def test_consultant_prompt_package(client):
    r = client.post("/api/consultant/prompt?lang=ru", json=dict(FLIGHT_OK, corta="650", question="Что делать?"))
    assert r.status_code == 200
    pkg = r.get_json()
    assert pkg["system"] and pkg["messages"][0]["role"] == "user"
    assert "FACTS" in pkg["messages"][0]["content"] and "Что делать?" in pkg["messages"][0]["content"]
    assert pkg["facts"]["risk_percent"] > 0


def test_unknown_route_and_method_are_json(client):
    assert client.get("/nope").get_json()["error"] == "not_found"
    assert client.get("/predict").get_json()["error"] == "method_not_allowed"


REPO = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(not (REPO / "wsgi.py").exists(), reason="site and API live in separate repositories")
def test_site_and_api_on_one_address():
    spec = importlib.util.spec_from_file_location("wsgi", REPO / "wsgi.py")
    wsgi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wsgi)
    c = wsgi.app.test_client()
    page = c.get("/")
    assert page.status_code == 200 and b"IMMOONITY" in page.data
    assert c.get("/astronaut.png").status_code == 200
    assert c.get("/api/health").get_json()["status"] == "ok"
    assert c.get("/api/unknown").status_code == 404
    assert c.post("/predict", json={"sex": "M", "vo2max": 48, "pullups": 15, "pushups": 60}).status_code == 200


@pytest.mark.skipif(not (REPO / "immoonity-site" / "index.html").exists(), reason="the site lives in a separate repository")
def test_site_assets_exist_and_have_latin_names():
    """Cyrillic file names break when an archive is extracted on Windows."""
    site = REPO / "immoonity-site"
    html = (site / "index.html").read_text(encoding="utf-8")
    refs = re.findall(r"""(?:src|href)\s*=\s*["']([^"'#?]+)["']|url\(\s*["']?([^"')]+)["']?\s*\)""", html)
    local = {a or b for a, b in refs} - {""}
    local = {r for r in local if not r.startswith(("http", "data:", "mailto:", "javascript", "/"))}
    assert local and all((site / r).is_file() for r in local), sorted(r for r in local if not (site / r).is_file())
    assert all(f.name.isascii() for f in site.iterdir())

