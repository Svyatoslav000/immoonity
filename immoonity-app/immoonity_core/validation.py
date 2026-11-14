"""Разбор и проверка входных данных по описанию полей в models/*.json."""

from __future__ import annotations

import math
from typing import Any

EARTH_KEYS = ("vo2max", "pullups", "pushups")  # одного поля sex недостаточно для выбора модели
FLIGHT_KEYS = ("il6_b", "il6_a", "nlr_b", "nlr_a", "ebv", "cortb", "corta", "days")

SEX_ALIASES = {
    "m": "M", "male": "M", "man": "M", "м": "M", "муж": "M", "мужской": "M", "мужчина": "M",
    "f": "F", "female": "F", "woman": "F", "ж": "F", "жен": "F", "женский": "F", "женщина": "F",
}

MESSAGES = {
    "en": {
        "required": "{label}: a value is required.",
        "not_a_number": "{label}: “{value}” is not a number.",
        "below_min": "{label}: must be at least {min} {unit}.",
        "above_max": "{label}: must be at most {max} {unit}.",
        "invalid_sex": "Sex must be “M” (male) or “F” (female).",
        "implausible": "{label} = {value} {unit} is outside the usual range ({lo}–{hi} {unit}) — please double-check the value and units.",
        "no_inputs": "No model inputs found. Send Earth fields (sex, vo2max, pullups, pushups) or In-Flight fields (il6_a, nlr_a, ebv, corta, days; il6_b, nlr_b, cortb optional).",
        "unknown_model": "Unknown model “{value}”. Use “earth” or “flight”.",
        "bad_json": "The request body must be a JSON object.",
    },
    "ru": {
        "required": "{label}: требуется значение.",
        "not_a_number": "{label}: «{value}» — не число.",
        "below_min": "{label}: значение должно быть не меньше {min} {unit}.",
        "above_max": "{label}: значение должно быть не больше {max} {unit}.",
        "invalid_sex": "Пол должен быть «M» (мужской) или «F» (женский).",
        "implausible": "{label} = {value} {unit} — вне обычного диапазона ({lo}–{hi} {unit}); проверьте значение и единицы.",
        "no_inputs": "Не найдено входных данных. Передайте поля земной модели (sex, vo2max, pullups, pushups) или полётной (il6_a, nlr_a, ebv, corta, days; il6_b, nlr_b, cortb — по желанию).",
        "unknown_model": "Неизвестная модель «{value}». Используйте «earth» или «flight».",
        "bad_json": "Тело запроса должно быть JSON-объектом.",
    },
}

UNITS_RU = {"ml/kg/min": "мл/кг/мин", "reps": "раз", "pg/mL": "пг/мл", "copies/mL": "копий/мл",
            "nmol/L": "нмоль/л", "days": "сут", "": ""}


def normalise_lang(lang: Any) -> str:
    return "ru" if str(lang or "").lower().startswith("ru") else "en"


def unit_label(unit: str | None, lang: str) -> str:
    unit = unit or ""
    return UNITS_RU.get(unit, unit) if lang == "ru" else unit


def _msg(lang: str, code: str, **kw) -> str:
    text = MESSAGES[lang][code].format(**kw)
    return " ".join(text.split()).replace(" .", ".")


def is_blank(raw: Any) -> bool:
    return raw is None or (isinstance(raw, str) and raw.strip() == "")


def parse_number(raw: Any) -> float:
    """Число или строка с числом; допускаются запятая и пробелы: "4,5", "1 200"."""
    if isinstance(raw, bool):
        raise ValueError("boolean")
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        text = str(raw).strip().replace(" ", "").replace(" ", "").replace(",", ".")
        value = float(text)
    if not math.isfinite(value):
        raise ValueError("not finite")
    return value


def _fmt(v: float) -> str:
    return f"{v:g}"


def detect_models(payload: dict[str, Any]) -> list[str]:
    requested = payload.get("model")
    if not is_blank(requested):
        return [str(requested).strip().lower()]
    has_earth = any(not is_blank(payload.get(k)) for k in EARTH_KEYS)
    has_flight = any(not is_blank(payload.get(k)) for k in FLIGHT_KEYS)
    return [m for m, present in (("earth", has_earth), ("flight", has_flight)) if present]


def validate(inputs_spec: dict[str, Any], payload: dict[str, Any], lang: str):
    """Возвращает (values, errors, warnings); пустые необязательные поля в values не попадают."""
    values: dict[str, Any] = {}
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    for field, spec in inputs_spec.items():
        label = spec.get("label", {}).get(lang, field)
        unit = unit_label(spec.get("unit"), lang)
        raw = payload.get(field)
        if is_blank(raw):
            if spec.get("required"):
                errors.append({"field": field, "code": "required", "message": _msg(lang, "required", label=label)})
            continue
        if spec["type"] == "sex":
            sex = SEX_ALIASES.get(str(raw).strip().lower())
            if sex is None:
                errors.append({"field": field, "code": "invalid_sex", "message": _msg(lang, "invalid_sex")})
            else:
                values[field] = sex
            continue
        try:
            v = parse_number(raw)
        except (TypeError, ValueError):
            errors.append({"field": field, "code": "not_a_number",
                           "message": _msg(lang, "not_a_number", label=label, value=str(raw)[:40])})
            continue
        if v < spec["min"]:
            errors.append({"field": field, "code": "below_min",
                           "message": _msg(lang, "below_min", label=label, min=_fmt(spec["min"]), unit=unit)})
            continue
        if v > spec["max"]:
            errors.append({"field": field, "code": "above_max",
                           "message": _msg(lang, "above_max", label=label, max=_fmt(spec["max"]), unit=unit)})
            continue
        lo, hi = spec.get("plausible", (spec["min"], spec["max"]))
        if not lo <= v <= hi:
            warnings.append({"field": field, "code": "implausible",
                             "message": _msg(lang, "implausible", label=label, value=_fmt(v), unit=unit,
                                             lo=_fmt(lo), hi=_fmt(hi))})
        values[field] = v
    return values, errors, warnings


def generic_error(code: str, lang: str, **kw) -> dict[str, str]:
    return {"code": code, "message": _msg(lang, code, **kw)}
