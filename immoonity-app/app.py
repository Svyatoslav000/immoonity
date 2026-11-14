"""API IMMOONITY.

    GET  /, /api/health          health check
    GET  /api/models             model cards: inputs, thresholds, weights, checks, sources
    POST /predict, /api/predict  prediction and interpretation
    POST /api/consultant/prompt  request for the LLM consultant

Locally: python app.py. API only on a host: gunicorn app:app.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from immoonity_core import __version__ as API_VERSION
from immoonity_core import validation as V
from immoonity_core.engine import load_models
from immoonity_core.interpreter import interpret
from immoonity_core.llm import build_consultant_request

log = logging.getLogger("immoonity")


def create_app(site_dir: str | Path | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    origins = os.environ.get("ALLOWED_ORIGINS", "*").strip()
    CORS(app, origins="*" if origins == "*" else [o.strip() for o in origins.split(",") if o.strip()])

    models = load_models()
    site = Path(site_dir).resolve() if site_dir else None

    def lang_of(payload: dict | None) -> str:
        return V.normalise_lang(request.args.get("lang") or (payload or {}).get("lang")
                                or request.headers.get("Accept-Language", "en"))

    def fail(status: int, code: str, message: str, details: list | None = None):
        body = {"error": code, "message": message}
        if details:
            body["details"] = details
        return jsonify(body), status

    def read_payload():
        payload = request.get_json(silent=True)
        return payload if isinstance(payload, dict) else None

    def predict_one(name: str, payload: dict, lang: str):
        model = models[name]
        values, errors, warnings = V.validate(model.inputs, payload, lang)
        if errors:
            return None, [dict(e, model=name) for e in errors]
        pred = model.predict(values)
        pred["input_warnings"] = warnings
        pred["interpretation"] = interpret(pred, model, lang)
        return pred, []

    def run(payload: dict | None):
        lang = lang_of(payload)
        if payload is None:
            return None, fail(400, "bad_json", V.generic_error("bad_json", lang)["message"]), lang
        names = V.detect_models(payload)
        if not names:
            return None, fail(400, "no_inputs", V.generic_error("no_inputs", lang)["message"]), lang
        unknown = [n for n in names if n not in models]
        if unknown:
            return None, fail(400, "unknown_model", V.generic_error("unknown_model", lang, value=unknown[0])["message"]), lang
        results, errors = {}, []
        for name in names:
            pred, errs = predict_one(name, payload, lang)
            errors += errs
            if pred:
                results[name] = pred
        if errors:
            msg = "Проверьте введённые данные." if lang == "ru" else "Please check the entered values."
            return None, fail(400, "validation_error", msg, errors), lang
        return results, None, lang

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "api_version": API_VERSION,
                        "models": {n: m.version for n, m in models.items()}})

    @app.get("/")
    def index():
        if site and (site / "index.html").is_file():
            return send_from_directory(site, "index.html")
        return jsonify({"service": "IMMOONITY API", "status": "ok", "api_version": API_VERSION,
                        "docs": "POST /predict, GET /api/models"})

    @app.get("/api/models")
    def model_cards():
        return jsonify({n: m.spec for n, m in models.items()})

    @app.post("/predict")
    @app.post("/api/predict")
    def predict():
        results, error, _lang = run(read_payload())
        if error:
            return error
        if len(results) == 1:
            (pred,) = results.values()
            return jsonify(dict(pred, api_version=API_VERSION))
        return jsonify({"api_version": API_VERSION, "results": results})

    @app.post("/api/consultant/prompt")
    def consultant_prompt():
        payload = read_payload()
        results, error, lang = run(payload)
        if error:
            return error
        question = (payload or {}).get("question")
        packages = {n: build_consultant_request(p, p["interpretation"], lang, question) for n, p in results.items()}
        return jsonify(next(iter(packages.values())) if len(packages) == 1 else packages)

    if site:
        @app.get("/<path:filename>")
        def static_site(filename: str):
            # with run_local.py or wsgi.py the site and the API share one address
            if filename.startswith("api/"):
                abort(404)
            return send_from_directory(site, filename)

    @app.errorhandler(404)
    def not_found(_e):
        return fail(404, "not_found", "Not found")

    @app.errorhandler(405)
    def not_allowed(_e):
        return fail(405, "method_not_allowed", "Method not allowed")

    @app.errorhandler(413)
    def too_large(_e):
        return fail(413, "payload_too_large", "Request body is too large")

    @app.errorhandler(Exception)
    def unexpected(e):
        if isinstance(e, HTTPException):
            return fail(e.code or 500, "http_error", str(e))
        log.exception("unhandled error")
        return fail(500, "internal_error", "Internal server error")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
