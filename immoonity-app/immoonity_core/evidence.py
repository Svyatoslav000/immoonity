"""Human p05–p95 evidence selection and status of the day-specific composite endpoint."""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .validation import number_text


# Field and sample phase are explicit: optional pre-flight values never use in-flight limits.
# Units are the canonical units enforced by /predict, including the time limit on exercise tests.
FIELDS = {
    "earth": {
        "vo2max": ("preflight", "mL/kg/min", True),
        "pullups": ("preflight", "reps/2min", True),
        "pushups": ("preflight", "reps/2min", True),
    },
    "flight": {
        "il6_a": ("inflight", "pg/mL", True), "nlr_a": ("inflight", "ratio", True),
        "ebv": ("inflight", "copies/mL", True), "corta": ("inflight", "nmol/L", True),
        "il6_b": ("preflight", "pg/mL", False), "nlr_b": ("preflight", "ratio", False),
        "cortb": ("preflight", "nmol/L", False),
    },
}
CLINICAL_ENDPOINT = "first_mission_failure_or_confirmed_disease_with_immunodeficiency"


def load_registry():
    path = Path(__file__).resolve().parents[1] / "models" / "human_reference_intervals.json"
    with path.open(encoding="utf-8") as stream:
        registry = json.load(stream)
    validate_registry(registry)
    return registry


def number(value):
    if isinstance(value, bool):
        raise ValueError("A quantitative measurement is required")
    try:
        value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("A finite quantitative measurement is required") from exc
    if not value.is_finite():
        raise ValueError("A finite quantitative measurement is required")
    return value


def validate_registry(registry):
    fields = {**FIELDS["earth"], **FIELDS["flight"]}
    if not registry.get("version") or not isinstance(registry.get("intervals"), list):
        raise ValueError("Missing registry version or interval list")
    keys = set()
    for band in registry["intervals"]:
        field = band["field"]
        if field not in fields or (band["phase"], band["unit"]) != fields[field][:2]:
            raise ValueError("Reference field, phase or unit mismatch")
        if band["species"] != "Homo sapiens" or band["status"] != "approved" or not band["source"]:
            raise ValueError("Only sourced approved human reference distributions are eligible")
        if (not registry.get("population") or band.get("population") != registry["population"]
                or not band.get("protocol") or not band.get("reference_id")
                or band.get("sex") not in ("any", "M", "F")):
            raise ValueError("Missing reference context")
        if number(band["p05"]) > number(band["p95"]):
            raise ValueError("Invalid p05/p95 order")
        lo, hi = band.get("day_min"), band.get("day_max")
        if (any(n is not None and (type(n) is not int or n < 1) for n in (lo, hi))
                or (lo is not None and hi is not None and hi < lo)
                or (band["phase"] != "inflight" and (lo is not None or hi is not None))):
            raise ValueError("Invalid flight-day window")
        if band["reference_id"] in keys:
            raise ValueError("Duplicate reference identifier")
        keys.add(band["reference_id"])


def assess_visit(model, inputs, visit, registry, *, raw_inputs=None):
    """Caller supplies validated model inputs. Return route, coverage, and explicit endpoint status."""
    day = visit.get("day") if model == "flight" else None
    protocols = visit.get("protocols", {})
    rows = []
    for field, (phase, unit, required) in FIELDS[model].items():
        value = inputs.get(field)
        if value is None and not required:
            continue
        if value is not None and raw_inputs and isinstance(raw_inputs.get(field), str):
            entered = number_text(raw_inputs[field])
            if number(entered) != number(value):
                value = entered
        row = {"field": field, "phase": phase, "unit": unit, "value": value, "status": "no_reference"}
        rows.append(row)
        if value is None:
            row["status"] = "missing_value"
            continue
        candidates = [b for b in registry["intervals"] if b["field"] == field
                      and b["sex"] in ("any", inputs.get("sex"))
                      and (b.get("day_min") is None or (day is not None and day >= b["day_min"]))
                      and (b.get("day_max") is None or (day is not None and day <= b["day_max"]))]
        # "form_default" can be approved only when the form already captures all conditions.
        protocol = protocols.get(field, "form_default")
        matched = [b for b in candidates if b["protocol"] == protocol]
        if len(matched) != 1:
            if candidates:
                row["status"] = "context_required" if not matched else "ambiguous_reference"
            continue
        band = matched[0]
        v, lo, hi = (number(x) for x in (value, band["p05"], band["p95"]))
        row.update(p05=str(lo), p95=str(hi), source=band["source"], reference_id=band["reference_id"])
        row["status"] = "below" if v < lo else "above" if v > hi else "inside"

    outside = [r["field"] for r in rows if r["status"] in ("below", "above")]
    assessed = sum(r["status"] in ("inside", "below", "above") for r in rows)
    if outside:
        route = "human_plus_animal"
    elif assessed == len(rows):
        route = "human_only"
    else:
        route = "undetermined"
    return {
        "registry_version": registry["version"], "route": route, "markers": rows,
        "outside": outside, "assessed": assessed, "total": len(rows),
        "composite": {"endpoint": CLINICAL_ENDPOINT, "as_of_flight_day": day,
                      "status": "not_estimable" if model == "flight" else "preflight",
                      "probability": None},
    }


def visit_error(model, visit, lang):
    def message(en, ru, zh):
        return {"en": en, "ru": ru, "zh": zh}[lang]
    if not isinstance(visit, dict):
        return message("Provide a visit object.", "Укажите параметры замера.", "请提供本次测量的参数。")
    if model == "flight" and (type(visit.get("day")) is not int or not 1 <= visit["day"] <= 2**53-1):
        return message("Enter a positive integer flight day.", "Укажите целый положительный день полёта.", "飞行日必须为正整数。")
    protocols = visit.get("protocols", {})
    if not isinstance(protocols, dict) or not all(
        k in FIELDS[model] and isinstance(v, str) and 0 < len(v) <= 120 for k, v in protocols.items()
    ):
        return message("Check measurement protocol codes.", "Проверьте коды протоколов измерения.", "请检查测量方案的编码。")
    return None
