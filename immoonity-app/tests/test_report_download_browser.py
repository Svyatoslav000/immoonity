from pathlib import Path
from shutil import which
from threading import Thread

import pytest
from werkzeug.serving import make_server

from app import create_app


def test_measurement_downloads_in_chrome(tmp_path):
    webdriver = pytest.importorskip("selenium.webdriver")
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as expected
    from selenium.webdriver.support.ui import WebDriverWait

    chrome = which("google-chrome") or which("chromium") or which("chrome")
    if not chrome:
        pytest.skip("Chrome or Chromium is required for the browser test")

    options = webdriver.ChromeOptions()
    options.binary_location = chrome
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--force-prefers-reduced-motion")
    options.add_experimental_option("prefs", {
        "download.default_directory": str(tmp_path),
        "download.prompt_for_download": False,
        "profile.default_content_setting_values.automatic_downloads": 1,
    })

    site = Path(__file__).resolve().parents[2] / "immoonity-site"
    with make_server("127.0.0.1", 0, create_app(site_dir=site), threaded=True) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with webdriver.Chrome(options=options) as browser:
                wait = WebDriverWait(browser, 20)

                def click(selector):
                    element = wait.until(expected.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    browser.execute_script("arguments[0].scrollIntoView({block:'center',behavior:'instant'})", element)
                    element.click()

                def measure(form, values):
                    for field, value in values.items():
                        element = browser.find_element(By.CSS_SELECTOR, f"{form} {field}")
                        element.clear()
                        element.send_keys(str(value))
                    click(f"{form} .calc-btn")
                    wait.until(expected.visibility_of_element_located((By.CSS_SELECTOR, f"{form} .consultant-panel")))

                browser.get(f"http://127.0.0.1:{server.server_port}/?lang=ru#demo")
                measure("#earth-form", {"[data-field=vo2max]": 48, "[data-field=pullups]": 8, "[data-field=pushups]": 25})
                click("#visit-tab-1")
                measure("#flight-form", {"[data-field=il6_a]": 5.4, "[data-field=nlr_a]": 2.5,
                                         "[data-field=corta]": 500, "[data-field=ebv]": 100,
                                         "[data-field=days]": 180, "[data-visit-day]": 35})

                for lang in ("ru", "en", "zh"):
                    click(f".lang-btn[data-lang={lang}]")
                    for tab, form, visit in ((0, "earth", "Earth"), (1, "flight", "F1-day-35")):
                        click(f"#visit-tab-{tab}")
                        click(f"#{form}-form .pdf-download-btn")
                        target = tmp_path / f"IMMOONITY-{visit}-{lang}.pdf"
                        wait.until(lambda _: target.is_file() and target.read_bytes().rstrip().endswith(b"%%EOF"))
                        report = target.read_bytes()
                        assert report.startswith(b"%PDF-") and b"/FontFile2" in report
                        assert b"mailto:immoonity@immoonity.ru" in report
                        assert b"https://t.me/immoonity" in report
        finally:
            server.shutdown()
            worker.join()
