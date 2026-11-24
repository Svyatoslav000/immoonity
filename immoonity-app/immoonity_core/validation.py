"""Parsing and validation of inputs against the field specs in models/*.json."""

from __future__ import annotations

import math
from typing import Any
from .chinese import FIELD_LABELS

EARTH_KEYS = ("vo2max", "pullups", "pushups")  # sex alone is not enough to pick a model
FLIGHT_KEYS = ("il6_b", "il6_a", "nlr_b", "nlr_a", "ebv", "cortb", "corta", "days")

SEX_ALIASES = {
    "男": "M", "男性": "M", "女": "F", "女性": "F",
    "m": "M", "male": "M", "man": "M", "м": "M", "муж": "M", "мужской": "M", "мужчина": "M",
    "f": "F", "female": "F", "woman": "F", "ж": "F", "жен": "F", "женский": "F", "женщина": "F",
}

MESSAGES = {
    "zh": {
        "required": "请填写{label}。", "not_a_number": "{label}必须是有效数值，当前为“{value}”。",
        "below_min": "{label}应至少为 {min} {unit}。", "above_max": "{label}应至多为 {max} {unit}。",
        "invalid_sex": "请选择男性（M）或女性（F）。",
        "implausible": "{label}为 {value} {unit}，超出通常范围（{lo}–{hi} {unit}）。请核对数值和单位。",
        "no_inputs": "请提供飞行前或飞行中模型的输入指标。", "unknown_model": "未知模型“{value}”。请选择 earth 或 flight。",
        "bad_json": "请求正文应为 JSON 对象。",
    },
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
    primary = str(lang or "").lower().strip().split(",", 1)[0].split(";", 1)[0].replace("_", "-").split("-", 1)[0]
    return primary if primary in MESSAGES else "en"


def field_label(spec: dict, field: str, lang: str) -> str:
    if lang == "zh":
        return FIELD_LABELS.get(field, field)
    return spec.get("label", {}).get(lang, field)


def unit_label(unit: str | None, lang: str) -> str:
    unit = unit or ""
    if lang == "zh":
        return {"reps": "次", "days": "天", "copies/mL":"拷贝/mL"}.get(unit, unit)
    return UNITS_RU.get(unit, unit) if lang == "ru" else unit


def _msg(lang: str, code: str, **kw) -> str:
    text = MESSAGES[lang][code].format(**kw)
    return " ".join(text.split()).replace(" .", ".")


def is_blank(raw: Any) -> bool:
    return raw is None or (isinstance(raw, str) and raw.strip() == "")


def number_text(raw: Any) -> str:
    return str(raw).strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")


def parse_number(raw: Any) -> float:
    """A number or a numeric string; a decimal comma and spaces are allowed: "4,5", "1 200"."""
    if isinstance(raw, bool):
        raise ValueError("boolean")
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        value = float(number_text(raw))
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
    """Returns (values, errors, warnings); empty optional fields are left out of values."""
    values: dict[str, Any] = {}
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    for field, spec in inputs_spec.items():
        label = field_label(spec, field, lang)
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
