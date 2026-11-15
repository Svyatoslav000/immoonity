"""Interpretation of a model result (EN/RU): level, drivers, what-if scenarios, recommendations."""

from __future__ import annotations

import math
from typing import Any

from .engine import EarthModel, FlightModel, RiskModel
from .validation import unit_label

T: dict[str, dict[str, Any]] = {
    "ru": {
        "interval": "90% интервал",
        "pp": "п.п.",
        "disclaimer": "Решения о здоровье должны приниматься вместе с врачом.",
        "sex": {"M": "мужской", "F": "женский"},
        "earth": {
            "outcome_short": "Риск реактивации латентных вирусов в полёте",
            "levels": {"low": "ниже среднего", "moderate": "средний", "elevated": "выше среднего", "high": "высокий"},
            "level_explain": {
                "low": "Профиль сопоставим с наиболее подготовленными членами экипажа в исходном исследовании.",
                "moderate": "Часть нормативов выполнена — есть резерв для снижения риска.",
                "elevated": "Большинство нормативов не выполнено или на границе.",
                "high": "Профиль соответствует членам экипажа с низкой предполётной подготовкой, у которых "
                        "реактивация наблюдалась практически всегда.",
            },
            "context": "Реактивация латентных герпесвирусов (ВЭБ, VZV, ЦМВ) — частый и обычно бессимптомный "
                       "признак ослабления иммунного контроля в длительном полёте: в исходной когорте МКС она "
                       "отмечена у 77% членов экипажа. Модель оценивает, как предполётная физическая "
                       "подготовка сдвигает этот риск.",
            "names": {"vo2max": "VO₂max", "pushups": "Отжимания", "pullups": "Подтягивания"},
            "names_acc": {"vo2max": "VO₂max", "pushups": "число отжиманий", "pullups": "число подтягиваний"},
            "driver": {
                "above": "{name}: {value} {unit} — выше ориентира {thr} {thr_unit}; снижает риск на {eff} п.п.",
                "borderline": "{name}: {value} {unit} — на границе ориентира {thr} {thr_unit}; защитный эффект "
                              "реализован частично (−{eff} п.п.).",
                "below": "{name}: {value} {unit} — ниже ориентира {thr} {thr_unit}; защитный эффект почти не реализован.",
            },
            "sex_driver": "Пол: {sex}. В данных у мужчин риск немного выше, чем у женщин (разница {eff} п.п.), "
                          "но этот эффект статистически неопределённый.",
            "what_if": "Если {name} достигнет {target} {unit}, оценка риска может снизиться примерно до {risk}% "
                       "(−{pot} п.п.).",
            "recs": {
                "aerobic": ("Аэробная выносливость",
                            "Систематические тренировки на выносливость (в том числе интервальные) с целью "
                            "VO₂max не ниже {target} мл/кг/мин. Высокая предполётная кардиореспираторная "
                            "выносливость ассоциирована с ~29% меньшим риском реактивации (Agha et al., 2020)."),
                "upper_body": ("Выносливость верхнего плечевого пояса",
                               "Тренировка мышечной выносливости: цели — отжимания не меньше {push}, подтягивания "
                               "не меньше {pull}. Высокая выносливость верхнего плечевого пояса ассоциирована с "
                               "~39% меньшим риском, более поздней реактивацией и меньшей вирусной нагрузкой "
                               "(Agha et al., 2020)."),
                "maintain": ("Сохранение формы в полёте",
                             "Регулярные тренировки на борту: чаще всего реактивация возникала у членов экипажа с "
                             "низкой исходной выносливостью и наибольшей потерей формы к возвращению "
                             "(Agha et al., 2020)."),
                "basics": ("Базовые меры",
                           "Сон, питание и управление стрессом поддерживают иммунную функцию; индивидуальный план "
                           "профилактики (включая вакцинальный статус) обсуждается с врачом (Crucian et al., 2018)."),
                "consult": ("Медицинская служба",
                            "При таком уровне риска стоит обсудить программу предполётной подготовки и "
                            "мониторинга с врачом экипажа."),
            },
            "notes": [
                "Учёт возрастных параметров — в разработке.",
            ],
        },
        "flight": {
            "outcome_short": "Риск многосистемной иммунной дисрегуляции",
            "levels": {"low": "низкий", "moderate": "умеренный", "elevated": "повышенный", "high": "высокий"},
            "level_explain": {
                "low": "Вовлечённых подсистем нет или изменения минимальны.",
                "moderate": "Изолированный сдвиг одной подсистемы или пограничные значения — важна динамика.",
                "elevated": "Выраженный сдвиг одной подсистемы (особенно реактивация ВЭБ) или две подсистемы "
                            "на границе порогов.",
                "high": "Вовлечены две и более подсистемы — многосистемная дисрегуляция: нужны оценка врача "
                        "экипажа и наблюдение в динамике.",
            },
            "context": "Модель объединяет четыре подсистемы, которые первыми реагируют на микрогравитацию, "
                       "радиацию, изоляцию и сбой циркадных ритмов: воспаление (IL-6), клеточный сдвиг (NLR), "
                       "реактивацию латентного ВЭБ и стресс-гормоны (кортизол). Вклад каждой взвешен по "
                       "клинической значимости. Параметры заданы по опубликованным исследованиям: открытых "
                       "индивидуальных данных «маркеры → исход» пока нет.",
            "names": {"cytokine": "Воспаление (IL-6)", "immune_shift": "Сдвиг лейкоцитов (NLR)",
                      "viral": "Реактивация ВЭБ", "neuroendocrine": "Стресс-ось (кортизол)"},
            "names_lower": {"cytokine": "уровень IL-6", "immune_shift": "NLR", "viral": "уровень ДНК ВЭБ",
                            "neuroendocrine": "кортизол"},
            "measure": {"cytokine": ("IL-6", "pg/mL"), "immune_shift": ("NLR", ""),
                        "viral": ("ДНК ВЭБ", "copies/mL"), "neuroendocrine": ("Кортизол", "nmol/L")},
            "status": {"above": "выше порога", "borderline": "пограничное значение", "below": "в пределах нормы"},
            "why": {
                "absolute": "ориентир {thr} {unit}",
                "relative": "критическая разница +{thr}%",
                "log10": "порог реактивации ≈{thr} {unit}",
            },
            "anchor": {
                "cytokine": "Ориентир: до 7 пг/мл (95-й перцентиль здоровых).",
                "immune_shift": "Норма NLR у здоровых взрослых: 0.78–3.53.",
                "viral": "Ориентир: у здоровых ~40 копий/мл слюны, в полёте у астронавтов с реактивацией ~417.",
                "neuroendocrine": "Значимым считается рост больше +39% от исходного или уровень выше 550 нмоль/л.",
            },
            "was": "было {before} → стало {after} {unit} ({change:+.0f}%)",
            "pattern": {
                0: "Ни одна подсистема не выходит за пороги.",
                1: "Изолированный сдвиг одной подсистемы ({names}): по градации исследований это лёгкая степень, "
                   "но важна динамика.",
                "n": "Вовлечены подсистемы: {names} — многосистемная дисрегуляция. Обычно она протекает без "
                     "симптомов: в обзоре NASA по 112 астронавтам симптомы реактивации вирусов были у 6, все "
                     "лёгкие (Rooney et al., 2019).",
                "stress_viral": "Сочетание стресс-реакции и реактивации ВЭБ соответствует описанному механизму "
                                "стресс-индуцированной реактивации латентных вирусов (Stowe et al., 2001).",
                "inflammation": "Рост IL-6 вместе с NLR указывает на системный воспалительный сдвиг "
                                "(Paul et al., 2020; Crucian et al., 2018).",
            },
            "duration_ref": "Длительность миссии {days:g} сут — опорная (типичная миссия на МКС, откуда основные "
                            "данные). Большинство иммунных сдвигов возникают в первые недели полёта и затем "
                            "сохраняются (Crucian et al., 2015), а реактивация вирусов с длительностью нарастает: "
                            "53% экипажа в полётах 10–16 сут против 61% на МКС (Rooney et al., 2019).",
            "duration_flat": "Длительность миссии {days:g} сут почти не меняет оценку: при таком профиле риск уже "
                             "определяется биомаркерами.",
            "duration": "Длительность миссии {days:g} сут: относительно 180 сут риск {eff} п.п. Риск растёт с "
                        "длительностью, но всё медленнее: основная часть сдвигов возникает в начале полёта "
                        "(Crucian et al., 2015), а реактивация вирусов продолжает нарастать (Rooney et al., 2019).",
            "duration_stable": "Стабильные маркеры — благоприятный признак: при таком профиле риск растёт с "
                               "длительностью медленнее, чем при уже начавшихся сдвигах. Но поздние изменения не "
                               "исключены: в изоляции на год иммунные реакции усиливались после 3–4 месяцев "
                               "(Feuerecker et al., 2019).",
            "what_if": "Если {name} нормализуется, оценка риска может снизиться примерно до {risk}% (−{pot} п.п.).",
            "what_if_all": "Если все сместившиеся маркеры нормализуются, оценка риска может снизиться примерно до "
                           "{risk}% (−{pot} п.п.).",
            "recs": {
                "viral": ("Вирусная реактивация",
                          "Сообщить врачу экипажа; наблюдать за симптомами (высыпания на коже, поражения "
                          "слизистых, лихорадка, утомляемость); повторить определение ДНК ВЭБ в динамике. "
                          "Решения о лечении принимает только врач (Mehta et al., 2017)."),
                "neuroendocrine": ("Стресс и циркадные ритмы",
                                   "Режим сна и освещения, контроль рабочей нагрузки, психологическая поддержка; "
                                   "повторить кортизол в то же время суток — он меняется в течение дня "
                                   "(Stowe et al., 2001; Crucian et al., 2018)."),
                "cytokine": ("Воспаление",
                             "Повторить IL-6 и другие маркеры воспаления в динамике, оценить признаки инфекции; "
                             "поддерживать режим упражнений, сна и питания (Crucian et al., 2018)."),
                "immune_shift": ("Лейкоцитарная формула",
                                 "Повторить общий анализ крови с лейкоформулой в стандартное время: NLR "
                                 "чувствителен к острому стрессу и времени забора (Paul et al., 2020)."),
                "monitoring": ("Мониторинг в динамике",
                               "Для длительной миссии важен регулярный мониторинг этих маркеров по графику, "
                               "согласованному с медицинской службой: динамика информативнее единичного значения."),
                "priority": ("Приоритетно",
                             "Высокий уровень риска: рекомендуется приоритетно обсудить результаты с врачом экипажа."),
                "prevention": ("Профилактика",
                               "Поддерживать профилактические меры: физическая активность, сон, питание, управление "
                               "стрессом (Crucian et al., 2018)."),
            },
            "notes": [
                "Параметры модели заданы по опубликованным исследованиям, а не обучены: открытых индивидуальных "
                "данных «маркеры → исход» нет, а в групповом датасете команды исход совпадает с суммой входов. "
                "Интервал {low}–{high}% отражает неопределённость этих допущений.",
            ],
            "baseline_timing": "«До полёта» лучше измерять за 1–2 месяца до старта: в последние дни показатели уже "
                               "смещены — у всех четырёх членов экипажа Inspiration4 за 3 сут до старта лимфоциты "
                               "были на 30–73% выше, чем за 1,5–3 месяца, а IL-6 у одного — в 2,2 раза выше.",
            "radiation": "Радиация в модели не учтена. За {days:g} сут доза составит ~{leo_lo}–{leo_hi} мЗв на орбите "
                         "МКС (0,2–0,5 мЗв/сут) или ~{deep} мЗв в межпланетном полёте (≈1,8 мЗв/сут, Zeitlin et al., "
                         "2013); карьерный лимит NASA — {limit} мЗв.",
            "warn": {
                "baseline_missing": "Нет исходного значения ({field}) — для «{name}» оценён только абсолютный уровень.",
                "baseline_not_positive": "Исходное значение ({field}) ≤ 0 — относительный критерий для «{name}» не применён.",
                "duration_limited_evidence": "Иммунных данных о полётах дольше полугода мало (NASA Twins Study — "
                                             "340 сут, один человек): оценка менее надёжна.",
                "duration_beyond_evidence": "{days:g} сут — дольше самого длинного полёта в истории (437 сут, "
                                            "В. Поляков, 1994–1995): оценка — экстраполяция, интервал расширен.",
            },
        },
    },
    "en": {
        "interval": "90% interval",
        "pp": "pp",
        "disclaimer": "Health decisions must be made together with a physician.",
        "sex": {"M": "male", "F": "female"},
        "earth": {
            "outcome_short": "Risk of latent virus reactivation in flight",
            "levels": {"low": "below average", "moderate": "average", "elevated": "above average", "high": "high"},
            "level_explain": {
                "low": "The profile matches the best-prepared crew members of the source study.",
                "moderate": "Some fitness targets are met — there is room to lower the risk.",
                "elevated": "Most fitness targets are missed or borderline.",
                "high": "The profile matches crew members with low pre-flight fitness, who reactivated almost "
                        "without exception.",
            },
            "context": "Reactivation of latent herpesviruses (EBV, VZV, CMV) is a common and usually silent sign "
                       "of weakened immune control during long missions: it occurred in 77% of the ISS cohort "
                       "behind this model. The model estimates how pre-flight physical fitness shifts that risk.",
            "names": {"vo2max": "VO₂max", "pushups": "Push-ups", "pullups": "Pull-ups"},
            "names_acc": {"vo2max": "VO₂max", "pushups": "push-ups", "pullups": "pull-ups"},
            "driver": {
                "above": "{name}: {value} {unit} — above the {thr} {thr_unit} target; lowers the risk by {eff} pp.",
                "borderline": "{name}: {value} {unit} — at the {thr} {thr_unit} target; the protective effect is only "
                              "partly realised (−{eff} pp).",
                "below": "{name}: {value} {unit} — below the {thr} {thr_unit} target; little protective effect yet.",
            },
            "sex_driver": "Sex: {sex}. In the data men had a slightly higher risk than women ({eff} pp apart), "
                          "but this effect is statistically uncertain.",
            "what_if": "With {name} at {target} {unit}, the estimate could fall to about {risk}% (−{pot} pp).",
            "recs": {
                "aerobic": ("Aerobic endurance",
                            "Structured endurance training (including intervals) aiming at VO₂max ≥ {target} "
                            "ml/kg/min. High pre-flight cardiorespiratory fitness was associated with ~29% lower "
                            "reactivation risk (Agha et al., 2020)."),
                "upper_body": ("Upper-body endurance",
                               "Muscular-endurance training: targets — push-ups ≥ {push}, pull-ups ≥ {pull}. High "
                               "upper-body endurance was associated with ~39% lower risk, later reactivation and "
                               "lower viral load (Agha et al., 2020)."),
                "maintain": ("Keep fit in flight",
                             "Train regularly on board: reactivation was most frequent in crew with low baseline "
                             "fitness and the largest fitness loss on return (Agha et al., 2020)."),
                "basics": ("Basics",
                           "Sleep, nutrition and stress management support immune function; an individual "
                           "prevention plan (incl. vaccination status) is agreed with a physician "
                           "(Crucian et al., 2018)."),
                "consult": ("Medical team",
                            "At this risk level, discuss the pre-flight conditioning and monitoring plan with the "
                            "crew physician."),
            },
            "notes": [
                "Age adjustment is in development.",
            ],
        },
        "flight": {
            "outcome_short": "Risk of multi-system immune dysregulation",
            "levels": {"low": "low", "moderate": "moderate", "elevated": "elevated", "high": "high"},
            "level_explain": {
                "low": "No subsystem is involved, or changes are minimal.",
                "moderate": "An isolated shift of one subsystem or borderline values — the trend matters.",
                "elevated": "A pronounced shift of one subsystem (especially EBV reactivation) or two borderline "
                            "subsystems.",
                "high": "Two or more subsystems are involved — multi-system dysregulation: needs review by the "
                        "crew physician and follow-up.",
            },
            "context": "The model combines four subsystems that respond first to microgravity, radiation, isolation "
                       "and circadian disruption: inflammation (IL-6), cell shift (NLR), latent EBV reactivation and "
                       "stress hormones (cortisol). Each is weighted by clinical significance. The parameters are "
                       "set from published studies: open individual-level marker → outcome data do not exist yet.",
            "names": {"cytokine": "Inflammation (IL-6)", "immune_shift": "Leukocyte shift (NLR)",
                      "viral": "EBV reactivation", "neuroendocrine": "Stress axis (cortisol)"},
            "names_lower": {"cytokine": "IL-6", "immune_shift": "NLR", "viral": "EBV DNA",
                            "neuroendocrine": "cortisol"},
            "measure": {"cytokine": ("IL-6", "pg/mL"), "immune_shift": ("NLR", ""),
                        "viral": ("EBV DNA", "copies/mL"), "neuroendocrine": ("Cortisol", "nmol/L")},
            "status": {"above": "above threshold", "borderline": "borderline", "below": "within normal range"},
            "why": {
                "absolute": "reference {thr} {unit}",
                "relative": "reference change value +{thr}%",
                "log10": "reactivation threshold ≈{thr} {unit}",
            },
            "anchor": {
                "cytokine": "Reference: up to 7 pg/mL (95th percentile of healthy people).",
                "immune_shift": "Normal NLR in healthy adults: 0.78–3.53.",
                "viral": "Reference: ~40 copies/mL saliva in healthy people, ~417 in astronauts with in-flight reactivation.",
                "neuroendocrine": "Significant: a rise above +39% from baseline or a level above 550 nmol/L.",
            },
            "was": "{before} → {after} {unit} ({change:+.0f}%)",
            "pattern": {
                0: "No subsystem exceeds its threshold.",
                1: "Isolated shift of one subsystem ({names}): mild on the studies' severity scale, but the trend "
                   "matters.",
                "n": "Subsystems involved: {names} — multi-system dysregulation. It is usually asymptomatic: in "
                     "NASA's review of 112 astronauts only 6 had symptoms of viral reactivation, all mild "
                     "(Rooney et al., 2019).",
                "stress_viral": "Stress response together with EBV reactivation matches the described mechanism of "
                                "stress-induced reactivation of latent viruses (Stowe et al., 2001).",
                "inflammation": "IL-6 rising together with NLR points to a systemic inflammatory shift "
                                "(Paul et al., 2020; Crucian et al., 2018).",
            },
            "duration_ref": "Mission length {days:g} days is the reference (a typical ISS mission, where most data "
                            "come from). Most immune shifts appear in the first weeks of flight and then persist "
                            "(Crucian et al., 2015), while viral reactivation grows with mission length: 53% of crew "
                            "on 10–16-day flights vs 61% on the ISS (Rooney et al., 2019).",
            "duration_flat": "Mission length {days:g} days barely changes the estimate: with this profile the risk is "
                             "driven by the biomarkers.",
            "duration": "Mission length {days:g} days: {eff} pp vs. a 180-day mission. The risk grows with mission "
                        "length, but ever more slowly: most shifts appear early in flight (Crucian et al., 2015), "
                        "while viral reactivation keeps growing (Rooney et al., 2019).",
            "duration_stable": "Stable markers are a good sign: with this profile the risk grows with mission length "
                               "more slowly than once shifts have started. Late changes are still possible: during a "
                               "year of isolation immune responses intensified after 3–4 months (Feuerecker et al., "
                               "2019).",
            "what_if": "If {name} returns to normal, the estimate could fall to about {risk}% (−{pot} pp).",
            "what_if_all": "If all shifted markers return to normal, the estimate could fall to about {risk}% "
                           "(−{pot} pp).",
            "recs": {
                "viral": ("Viral reactivation",
                          "Inform the crew physician; watch for symptoms (skin rash, mucosal lesions, fever, "
                          "fatigue); repeat EBV DNA testing over time. Treatment decisions are made by a physician "
                          "only (Mehta et al., 2017)."),
                "neuroendocrine": ("Stress and circadian rhythm",
                                   "Sleep and lighting schedule, workload control, psychological support; repeat "
                                   "cortisol at the same time of day — it varies over the day "
                                   "(Stowe et al., 2001; Crucian et al., 2018)."),
                "cytokine": ("Inflammation",
                             "Repeat IL-6 and other inflammation markers over time and check for signs of infection; "
                             "keep up exercise, sleep and nutrition (Crucian et al., 2018)."),
                "immune_shift": ("Blood count",
                                 "Repeat a complete blood count with differential at a standard time: NLR is "
                                 "sensitive to acute stress and sampling time (Paul et al., 2020)."),
                "monitoring": ("Track the trend",
                               "On a long mission, monitor these markers regularly on a schedule agreed with the "
                               "medical team: the trend is more informative than a single value."),
                "priority": ("Priority",
                             "High risk: discuss these results with the crew physician as a priority."),
                "prevention": ("Prevention",
                               "Keep up preventive measures: physical activity, sleep, nutrition, stress management "
                               "(Crucian et al., 2018)."),
            },
            "notes": [
                "The model's parameters are set from published studies, not trained: there are no open "
                "individual-level marker → outcome data, and in the team's group-level dataset the outcome equals "
                "the sum of the inputs. The {low}–{high}% interval reflects the uncertainty of these assumptions.",
            ],
            "baseline_timing": "Measure the “before” values 1–2 months before launch: in the last days they are "
                               "already shifted — all four Inspiration4 crew members had 30–73% higher lymphocyte "
                               "counts 3 days before launch than 1.5–3 months earlier, and one had 2.2 times higher IL-6.",
            "radiation": "Radiation is not included in the model. Over {days:g} days the dose would be ~{leo_lo}–"
                         "{leo_hi} mSv in ISS orbit (0.2–0.5 mSv/day) or ~{deep} mSv in interplanetary flight "
                         "(≈1.8 mSv/day, Zeitlin et al., 2013); NASA's career limit is {limit} mSv.",
            "warn": {
                "baseline_missing": "No baseline value ({field}) — “{name}” was assessed by its absolute level only.",
                "baseline_not_positive": "Baseline value ({field}) ≤ 0 — the relative criterion for “{name}” was not applied.",
                "duration_limited_evidence": "Immune data for flights longer than six months are scarce (NASA Twins "
                                             "Study — 340 days, one person): the estimate is less reliable.",
                "duration_beyond_evidence": "{days:g} days is longer than the longest spaceflight ever (437 days, "
                                            "V. Polyakov, 1994–1995): the estimate is an extrapolation and the "
                                            "interval is widened.",
            },
        },
    },
}

REC_PRIORITY = {"priority": 0, "viral": 1, "aerobic": 1, "upper_body": 1, "neuroendocrine": 2, "cytokine": 2,
                "immune_shift": 3, "consult": 2, "monitoring": 4, "maintain": 4, "basics": 5, "prevention": 5}


def _num(v: float) -> str:
    """48 -> '48', 2.25 -> '2.25', 417.0 -> '417'."""
    if v is None:
        return "—"
    if abs(v) >= 100:
        return f"{v:.0f}"
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _pct(v: float) -> str:
    """Whole percent, rounding half up like toFixed(0) on the site: 38.5 -> '39'."""
    return str(math.floor(v + 0.5))


def _reps(value: float, unit: str, lang: str) -> str:
    """Russian plural forms for repetitions (1 раз / 2 раза / 5 раз); 1 rep / 2 reps."""
    if unit not in ("раз", "reps"):
        return unit
    if lang == "en":
        return "rep" if value == 1 else "reps"
    if value != int(value):
        return "раза"
    n = int(value) % 100
    if 11 <= n <= 14:
        return "раз"
    return "раза" if n % 10 in (2, 3, 4) else "раз"


def _pp(v: float) -> str:
    return f"{v:+.1f}".replace("+-", "−").replace("-", "−")


def _base(pred: dict, model: RiskModel, t: dict, tm: dict) -> dict:
    lvl = pred["level"]["code"]
    ri = pred["risk_interval"]
    return {
        "model": model.name,
        "outcome": model.spec["outcome"]["ru" if t is T["ru"] else "en"],
        "headline": f"{tm['outcome_short']}: {_pct(pred['risk'])}% "
                    f"({t['interval']} {_pct(ri['low'])}–{_pct(ri['high'])}%) — {tm['levels'][lvl]}",
        "level": {"code": lvl, "label": tm["levels"][lvl], "color": pred["level"]["color"],
                  "explanation": tm["level_explain"][lvl]},
        "context": tm["context"],
        "disclaimer": t["disclaimer"],
    }


# Single-marker scenarios that change the estimate by less than this are not shown.
MIN_WHAT_IF_PP = 5.0


def _references(model: RiskModel, keys: list[str]) -> list[dict]:
    refs = model.spec.get("references", {})
    return [{"key": k, **refs[k]} for k in keys if k in refs]


def interpret_earth(pred: dict, model: EarthModel, lang: str) -> dict:
    t = T[lang]
    tm = t["earth"]
    out = _base(pred, model, t, tm)
    sex = pred["inputs"]["sex"]
    comps = pred["details"]["components"]
    factors = {f["factor"]: f for f in pred["factors"]}
    drivers, what_if = [], []
    for name in ("vo2max", "pushups", "pullups"):
        c, f = comps[name], factors[name]
        unit = unit_label(c["unit"], lang)
        drivers.append({
            "factor": name, "status": c["status"], "effect_pp": f["effect_pp"],
            "text": tm["driver"][c["status"]].format(name=tm["names"][name], value=_num(c["value"]),
                                                     unit=_reps(c["value"], unit, lang), thr=_num(c["threshold"]),
                                                     thr_unit=_reps(c["threshold"], unit, lang),
                                                     eff=f"{abs(f['effect_pp']):.1f}"),
        })
        if f["potential_pp"] <= -0.5:
            what_if.append({
                "factor": name, "target_value": f["target_value"], "risk_after": f["risk_at_target"],
                "delta_pp": f["potential_pp"],
                "text": tm["what_if"].format(name=tm["names_acc"][name], target=_num(f["target_value"]),
                                             unit=_reps(f["target_value"], unit, lang),
                                             risk=_pct(f['risk_at_target']), pot=f"{abs(f['potential_pp']):.1f}"),
            })
    sexf = factors["sex"]
    drivers.append({"factor": "sex", "status": "info", "effect_pp": sexf["effect_pp"],
                    "text": tm["sex_driver"].format(sex=t["sex"][sex], eff=f"{abs(sexf['effect_pp']):.1f}")})
    drivers.sort(key=lambda d: -abs(d["effect_pp"]) if d["factor"] != "sex" else 1e9)
    what_if.sort(key=lambda w: w["delta_pp"])

    recs = []
    def add(key, **fmt):
        title, text = tm["recs"][key]
        recs.append({"id": key, "priority": REC_PRIORITY[key], "title": title, "text": text.format(**fmt)})
    if comps["vo2max"]["status"] != "above":
        add("aerobic", target=_num(comps["vo2max"]["target"]))
    if comps["pushups"]["status"] != "above" or comps["pullups"]["status"] != "above":
        add("upper_body", push=_num(comps["pushups"]["target"]), pull=_num(comps["pullups"]["target"]))
    if pred["level"]["code"] in ("elevated", "high"):
        add("consult")
    add("maintain")
    add("basics")
    recs.sort(key=lambda r: r["priority"])

    ri = pred["risk_interval"]
    out.update({
        "drivers": drivers,
        "what_if": what_if,
        "recommendations": recs,
        "notes": [n.format(low=_pct(ri['low']), high=_pct(ri['high'])) for n in tm["notes"]],
        "references": _references(model, ["agha2020", "crucian2018", "chastin2021"]),
    })
    return out


def _marker_text(name: str, info: dict, tm: dict, lang: str) -> tuple[str, str | None]:
    label, unit_key = tm["measure"][name]
    unit = unit_label(unit_key, lang)
    crits = info["criteria"]
    rel = next((c for c in crits if c["kind"] == "relative" and c["computable"]), None)
    main = next((c for c in crits if c["kind"] in ("absolute", "log10")), None)
    value = main.get("value") if main else None
    if rel:
        measured = f"{label}: " + " ".join(tm["was"].format(before=_num(rel["before"]), after=_num(rel["after"]),
                                                             unit=unit, change=rel["change"] * 100).split())
    else:
        measured = f"{label}: {_num(value)} {unit}".strip()
    reason = None
    if info["status"] != "below":
        best = max((c for c in crits if c["computable"]), key=lambda c: c["membership"])
        if best["kind"] == "relative":
            reason = tm["why"]["relative"].format(thr=_pct(best["threshold"] * 100))
        else:
            reason = tm["why"][best["kind"]].format(unit=unit, thr=_num(best["threshold"]))
    return measured, reason


def interpret_flight(pred: dict, model: FlightModel, lang: str) -> dict:
    t = T[lang]
    tm = t["flight"]
    out = _base(pred, model, t, tm)
    markers = pred["details"]["markers"]
    factors = {f["factor"]: f for f in pred["factors"]}
    marker_list, what_if = [], []
    for name in ("viral", "neuroendocrine", "cytokine", "immune_shift"):
        info, f = markers[name], factors[name]
        measured, reason = _marker_text(name, info, tm, lang)
        text = f"{measured} — {tm['status'][info['status']]}" + (f" ({reason})." if reason else ".")
        marker_list.append({"marker": name, "title": tm["names"][name], "status": info["status"],
                            "membership": info["membership"], "effect_pp": f["effect_pp"],
                            "text": text, "reference": tm["anchor"][name]})
        if info["status"] != "below" and f["effect_pp"] >= MIN_WHAT_IF_PP:
            what_if.append({"factor": name, "risk_after": f["risk_if_normal"], "delta_pp": -f["effect_pp"],
                            "text": tm["what_if"].format(name=tm["names_lower"][name], risk=_pct(f['risk_if_normal']),
                                                         pot=f"{f['effect_pp']:.1f}")})
    marker_list.sort(key=lambda m: -m["effect_pp"])
    shifted = [m for m in marker_list if m["status"] != "below"]
    all_normal = pred["details"].get("risk_if_shifted_normal")
    if len(shifted) >= 2 and all_normal is not None:
        gain = round(pred["risk"] - all_normal, 1)
        best_single = max((-w["delta_pp"] for w in what_if), default=0.0)
        if gain >= MIN_WHAT_IF_PP and gain - best_single >= MIN_WHAT_IF_PP:
            what_if.append({"factor": "all_markers", "risk_after": all_normal, "delta_pp": -gain,
                            "text": tm["what_if_all"].format(risk=_pct(all_normal), pot=f"{gain:.1f}")})
    what_if.sort(key=lambda w: w["delta_pp"])

    involved = [m for m in marker_list if m["status"] == "above"]
    names = ", ".join(m["title"] for m in involved)
    pattern = [tm["pattern"][0] if not involved else
               tm["pattern"][1].format(names=names) if len(involved) == 1 else tm["pattern"]["n"].format(names=names)]
    state = {m["marker"]: m["status"] for m in marker_list}
    if state["viral"] != "below" and state["neuroendocrine"] != "below":
        pattern.append(tm["pattern"]["stress_viral"])
    if state["cytokine"] != "below" and state["immune_shift"] != "below":
        pattern.append(tm["pattern"]["inflammation"])

    days_f = factors["days"]
    if days_f["value"] == days_f["reference_days"]:
        duration = tm["duration_ref"].format(days=days_f["value"])
    elif abs(days_f["effect_pp"]) < 0.5:
        duration = tm["duration_flat"].format(days=days_f["value"])
    else:
        duration = tm["duration"].format(days=days_f["value"], eff=_pp(days_f["effect_pp"]))
    stable = all(m["status"] == "below" for m in marker_list)
    if stable and days_f["value"] > days_f["reference_days"]:
        duration += " " + tm["duration_stable"]

    recs = []
    def add(key):
        title, text = tm["recs"][key]
        recs.append({"id": key, "priority": REC_PRIORITY[key], "title": title, "text": text})
    if pred["level"]["code"] == "high":
        add("priority")
    for m in marker_list:
        if m["status"] != "below":
            add(m["marker"])
    if days_f["value"] >= 90 and pred["level"]["code"] != "low":
        add("monitoring")
    if not any(m["status"] != "below" for m in marker_list):
        add("prevention")
    recs.sort(key=lambda r: r["priority"])

    ri = pred["risk_interval"]
    days = pred["details"]["days"]
    notes = [n.format(low=_pct(ri['low']), high=_pct(ri['high'])) for n in tm["notes"]]
    for w in pred["warnings"]:
        if w["code"] not in tm["warn"]:
            continue
        if "marker" in w:
            label = model.inputs.get(w["field"], {}).get("label", {}).get(lang, w["field"])
            notes.append(tm["warn"][w["code"]].format(field=label, name=tm["names"][w["marker"]]))
        else:
            notes.append(tm["warn"][w["code"]].format(days=days))
    dose = pred["details"].get("radiation_dose")
    if dose and days >= 365:
        notes.append(tm["radiation"].format(days=days, leo_lo=dose["leo_msv"][0], leo_hi=dose["leo_msv"][1],
                                            deep=dose["deep_space_msv"], limit=dose["career_limit_msv"]))
    has_baseline = any(c["kind"] == "relative" and c["computable"]
                       for m in pred["details"]["markers"].values() for c in m["criteria"])
    if has_baseline:
        notes.append(tm["baseline_timing"])
    refs = ["crucian2018", "rooney2019", "crucian2015", "mehta2017", "pierson2005", "stowe2001", "paul2020",
            "forget2017", "elecsys_il6", "fraser2001"]
    if stable and days > days_f["reference_days"]:
        refs.append("feuerecker2019")
    if any(w["code"] == "duration_beyond_evidence" for w in pred["warnings"]):
        refs.append("manzey1998")
    if dose and days >= 365:
        refs += ["zeitlin2013", "nasa_std3001"]
    if has_baseline:
        refs.append("kim2024")
    out.update({
        "markers": marker_list,
        "pattern": pattern,
        "duration": duration,
        "what_if": what_if,
        "recommendations": recs,
        "notes": notes,
        "references": _references(model, refs),
    })
    return out


def interpret(pred: dict, model: RiskModel, lang: str = "en") -> dict:
    lang = "ru" if lang == "ru" else "en"
    out = interpret_earth(pred, model, lang) if model.kind == "earth" else interpret_flight(pred, model, lang)
    out["language"] = lang
    return out
