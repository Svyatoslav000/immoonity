"""LLM request for the consultant: rules and facts from the interpreter. The LLM call itself runs server-side."""

from __future__ import annotations

import json
from typing import Any
from .validation import normalise_lang

SYSTEM = {
    "zh": (
        "你是 IMMOONITY 航天免疫学研究项目的助手。根据 FACTS 解释模型结果、主要影响因素及其限制。"
        "只使用提供的事实和来源。不要新增诊断、药物、剂量或未经验证的预测。"
        "同时说明风险估计和不确定区间。高风险时建议与乘组医生优先讨论。"
        "用简体中文简明作答，并说明本工具用于研究。"
    ),
    "ru": (
        "Ты — ИИ-консультант исследовательского проекта IMMOONITY (астроиммунология). Ты объясняешь "
        "результат модели риска человеку, который ввёл свои показатели на сайте.\n\n"
        "Опирайся только на факты из блока FACTS: оценку риска, интервал, уровень, факторы, сценарии "
        "«что если», рекомендации и источники. Не добавляй новых медицинских утверждений, диагнозов, "
        "препаратов и дозировок. Если вопрос выходит за рамки FACTS, честно скажи, что модель этого не "
        "оценивает, и предложи обсудить вопрос с врачом.\n\n"
        "Объясняй простым языком: что означает число, что сильнее всего на него влияет и что можно "
        "сделать. Говоря о риске, называй интервал неопределённости. При уровне «высокий» спокойно, но ясно "
        "порекомендуй обсудить результаты с врачом экипажа. Заверши ответ одной фразой о том, что это "
        "исследовательский демонстратор, а не медицинское заключение.\n\n"
        "Отвечай на языке пользователя, не длиннее 180 слов, без таблиц."
    ),
    "en": (
        "You are the AI consultant of IMMOONITY, an astroimmunology research project. You explain a risk "
        "model's result to the person who entered their values on the website.\n\n"
        "Rely only on the facts in the FACTS block: the risk estimate, interval, level, drivers, what-if "
        "scenarios, recommendations and references. Do not add new medical claims, diagnoses, drugs or doses. "
        "If a question goes beyond FACTS, say plainly that the model does not assess it and suggest discussing "
        "it with a physician.\n\n"
        "Use plain language: what the number means, what drives it most, and what can be done. When you state "
        "the risk, also state its uncertainty interval. At the “high” level, calmly but clearly recommend "
        "discussing the results with the crew physician. End with one sentence noting this is a research "
        "demonstrator, not a medical opinion.\n\n"
        "Answer in the user's language, in at most 180 words, without tables."
    ),
}

DEFAULT_QUESTION = {
    "zh": "请解释我的结果和可与医生讨论的后续措施。",
    "ru": "Объясни мой результат и что мне стоит сделать.",
    "en": "Explain my result and what I should do.",
}


def build_facts(prediction: dict[str, Any], interpretation: dict[str, Any]) -> dict[str, Any]:
    ri = prediction["risk_interval"]
    facts: dict[str, Any] = {
        "model": prediction["model"],
        "model_version": prediction["model_version"],
        "outcome": interpretation["outcome"],
        "risk_percent": prediction["risk"],
        "interval_90_percent": [ri["low"], ri["high"]],
        "level": interpretation["level"]["label"],
        "level_meaning": interpretation["level"]["explanation"],
        "context": interpretation["context"],
    }
    if "drivers" in interpretation:
        facts["drivers"] = [d["text"] for d in interpretation["drivers"]]
    if "markers" in interpretation:
        facts["biomarkers"] = [m["text"] + " " + m["reference"] for m in interpretation["markers"]]
        facts["pattern"] = interpretation["pattern"]
        facts["duration"] = interpretation["duration"]
    facts["what_if"] = [w["text"] for w in interpretation["what_if"]]
    facts["recommendations"] = [f"{r['title']}: {r['text']}" for r in interpretation["recommendations"]]
    facts["limitations"] = interpretation["notes"]
    facts["disclaimer"] = interpretation["disclaimer"]
    facts["references"] = [r["citation"] for r in interpretation["references"]]
    return facts


def build_consultant_request(prediction: dict[str, Any], interpretation: dict[str, Any], lang: str = "en",
                             question: str | None = None) -> dict[str, Any]:
    lang = normalise_lang(lang)
    facts = build_facts(prediction, interpretation)
    question = (question or "").strip()[:1000] or DEFAULT_QUESTION[lang]
    user = ("FACTS:\n```json\n" + json.dumps(facts, ensure_ascii=False, indent=2) + "\n```\n\n" + question)
    return {"system": SYSTEM[lang], "messages": [{"role": "user", "content": user}], "facts": facts,
            "language": lang}
