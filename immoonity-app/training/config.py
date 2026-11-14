"""Параметры моделей: пороги, веса, априорные распределения и их обоснование.

Всё отсюда попадает в models/*.json при обучении (training/train_models.py).
"""

import math

MODEL_VERSION = "3.1.0"
INTERVAL_LEVEL = 0.90
RANDOM_SEED = 20261109

# Источники
REFERENCES = {
    "agha2020": {
        "citation": "Agha NH, Mehta SK, Rooney BV, et al. Exercise as a countermeasure for latent viral "
                    "reactivation during long duration space flight. FASEB J. 2020;34(2):2869-2881.",
        "url": "https://doi.org/10.1096/fj.201902327R",
    },
    "pierson2005": {
        "citation": "Pierson DL, Stowe RP, Phillips TM, Lugg DJ, Mehta SK. Epstein-Barr virus shedding by "
                    "astronauts during space flight. Brain Behav Immun. 2005;19(3):235-242.",
        "url": "https://doi.org/10.1016/j.bbi.2004.08.001",
    },
    "mehta2017": {
        "citation": "Mehta SK, et al. Latent virus reactivation in astronauts on the International Space "
                    "Station. NPJ Microgravity. 2017;3:11.",
        "url": "https://doi.org/10.1038/s41526-017-0015-y",
    },
    "crucian2016": {
        "citation": "Crucian B, et al. Incidence of clinical symptoms during long-duration orbital "
                    "spaceflight. Int J Gen Med. 2016;9:383-391.",
        "url": "https://doi.org/10.2147/IJGM.S114188",
    },
    "crucian2018": {
        "citation": "Crucian BE, et al. Immune system dysregulation during spaceflight: potential "
                    "countermeasures for deep space exploration missions. Front Immunol. 2018;9:1437.",
        "url": "https://doi.org/10.3389/fimmu.2018.01437",
    },
    "paul2020": {
        "citation": "Paul AM, et al. Neutrophil-to-lymphocyte ratio: a biomarker to monitor the immune "
                    "status of astronauts. Front Immunol. 2020;11:564950.",
        "url": "https://doi.org/10.3389/fimmu.2020.564950",
    },
    "forget2017": {
        "citation": "Forget P, et al. What is the normal value of the neutrophil-to-lymphocyte ratio? "
                    "BMC Res Notes. 2017;10:12.",
        "url": "https://doi.org/10.1186/s13104-016-2335-5",
    },
    "elecsys_il6": {
        "citation": "Roche Diagnostics. Elecsys IL-6: upper reference limit 7 pg/mL (95th percentile, "
                    "817 apparently healthy individuals), method sheet.",
        "url": "https://www.labcorp.com/test-menu/29791/interleukin-6-serum",
    },
    "stowe2001": {
        "citation": "Stowe RP, Pierson DL, Barrett AD. Elevated stress hormone levels relate to "
                    "Epstein-Barr virus reactivation in astronauts. Psychosom Med. 2001;63(6):891-895.",
        "url": "https://researchexperts.utmb.edu/en/publications/elevated-stress-hormone-levels-relate-to-epstein-barr-virus-react/",
    },
    "stowe2000": {
        "citation": "Stowe RP, et al. Stress-induced reactivation of Epstein-Barr virus in astronauts. "
                    "Neuroimmunomodulation. 2000;8(2).",
        "url": "https://researchexperts.utmb.edu/en/publications/stress-induced-reactivation-of-epstein-barr-virus-in-astronauts/",
    },
    "chastin2021": {
        "citation": "Chastin SFM, et al. Effects of regular physical activity on the immune system, "
                    "vaccination and risk of community-acquired infectious disease in the general "
                    "population: systematic review and meta-analysis. Sports Med. 2021;51:1673-1686.",
        "url": "https://napier-repository.worktribe.com/output/2899155",
    },
    "klein2016": {
        "citation": "Klein SL, Flanagan KL. Sex differences in immune responses. Nat Rev Immunol. "
                    "2016;16(10):626-638.",
        "url": "https://doi.org/10.1038/nri.2016.90",
    },
    "gelman2008": {
        "citation": "Gelman A, Jakulin A, Pittau MG, Su YS. A weakly informative default prior "
                    "distribution for logistic and other regression models. Ann Appl Stat. 2008;2(4):1360-1383.",
        "url": "https://doi.org/10.1214/08-AOAS191",
    },
    "greenland2016": {
        "citation": "Greenland S, Mansournia MA, Altman DG. Sparse data bias: a problem hiding in plain "
                    "sight. BMJ. 2016;352:i1981.",
        "url": "https://doi.org/10.1136/bmj.i1981",
    },
    "riley2020": {
        "citation": "Riley RD, et al. Calculating the sample size required for developing a clinical "
                    "prediction model. BMJ. 2020;368:m441.",
        "url": "https://doi.org/10.1136/bmj.m441",
    },
    "fraser2001": {
        "citation": "Fraser CG. Biological Variation: From Principles to Practice. Washington, DC: AACC Press; "
                    "2001 (reference change value, RCV = √2·z·√(CVa² + CVi²)).",
        "url": "https://www.westgard.com/biodatabase1.htm",
    },
    "il6_bv": {
        "citation": "Cava F, et al. Biological variation of interleukin 6 (IL-6) and soluble interleukin 2 "
                    "receptor (sIL2R) in serum of healthy individuals (2000): CVi ≈ 48%; Dugué B, Leppänen E.: "
                    "CVi ≈ 30% — внутрииндивидуальная вариабельность IL-6 у здоровых 30–48%.",
        "url": "https://data.zhenzhi.com/details/1/908769401",
    },
    "cortisol_bv": {
        "citation": "EFLM Biological Variation Database, cortisol (serum, morning): median CVi ≈ 16%; "
                    "в версиях базы Ricós/Westgard — 15.2% и 20.9%.",
        "url": "https://biologicalvariation.eu/meta_by_analyte/492",
    },
    "leuko_bv": {
        "citation": "Delanghe JR, et al. (editorial on leukocyte-ratio biomarkers): CVi neutrophils 16.1%, "
                    "lymphocytes 10.4%; CV of a ratio ≈ √(CV₁² + CV₂²).",
        "url": "https://core.ac.uk/download/333623231.pdf",
    },
    "rooney2019": {
        "citation": "Rooney BV, Crucian BE, Pierson DL, Laudenslager ML, Mehta SK. Herpes virus reactivation in "
                    "astronauts during spaceflight and its application on Earth. Front Microbiol. 2019;10:16.",
        "url": "https://doi.org/10.3389/fmicb.2019.00016",
    },
    "crucian2014": {
        "citation": "Crucian BE, et al. Plasma cytokine concentrations indicate that in vivo hormonal regulation "
                    "of immunity is altered during long-duration spaceflight. J Interferon Cytokine Res. "
                    "2014;34(10):778-786.",
        "url": "https://doi.org/10.1089/jir.2013.0129",
    },
    "crucian2015": {
        "citation": "Crucian B, et al. Alterations in adaptive immunity persist during long-duration "
                    "spaceflight. NPJ Microgravity. 2015;1:15013.",
        "url": "https://doi.org/10.1038/npjmgrav.2015.13",
    },
    "garrett2019": {
        "citation": "Garrett-Bakelman FE, et al. The NASA Twins Study: a multidimensional analysis of a "
                    "year-long human spaceflight. Science. 2019;364(6436):eaau8650.",
        "url": "https://doi.org/10.1126/science.aau8650",
    },
    "bigley2019": {
        "citation": "Bigley AB, et al. NK cell function is impaired during long-duration spaceflight. "
                    "J Appl Physiol. 2019;126(4):842-853.",
        "url": "https://doi.org/10.1152/japplphysiol.00761.2018",
    },
    "moore2014": {
        "citation": "Moore AD Jr, et al. Peak exercise oxygen uptake during and following long-duration "
                    "spaceflight. J Appl Physiol. 2014;117(3):231-238.",
        "url": "https://doi.org/10.1152/japplphysiol.01251.2013",
    },
    "feuerecker2019": {
        "citation": "Feuerecker M, et al. Immune sensitization during 1 year in the Antarctic high-altitude "
                    "Concordia environment. Allergy. 2019;74(1):64-77.",
        "url": "https://doi.org/10.1111/all.13545",
    },
    "yi2014": {
        "citation": "Yi B, et al. 520-d isolation and confinement simulating a flight to Mars reveals heightened "
                    "immune responses and alterations of leukocyte phenotype. Brain Behav Immun. 2014;40:203-210.",
        "url": "https://doi.org/10.1016/j.bbi.2014.03.018",
    },
    "kim2024": {
        "citation": "Kim J, et al. Single-cell multi-ome and immune profiles of the Inspiration4 crew reveal "
                    "conserved, cell-type, and sex-specific responses to spaceflight. Nat Commun. 2024;15:4954. "
                    "Анализы экипажа — NASA OSDR: OSD-569 (общий анализ крови), OSD-575 (цитокины сыворотки).",
        "url": "https://doi.org/10.1038/s41467-024-49211-2",
    },
    "manzey1998": {
        "citation": "Manzey D, Lorenz B, Poljakov V. Mental performance in extreme environments: results from a "
                    "performance monitoring study during a 438-day spaceflight. Ergonomics. 1998;41(4):537-559.",
        "url": "https://doi.org/10.1080/001401398186991",
    },
    "zeitlin2013": {
        "citation": "Zeitlin C, et al. Measurements of energetic particle radiation in transit to Mars on the "
                    "Mars Science Laboratory. Science. 2013;340(6136):1080-1084.",
        "url": "https://doi.org/10.1126/science.1235989",
    },
    "nasa_std3001": {
        "citation": "NASA OCHMO. Radiation protection technical brief (NASA-STD-3001): career limit 600 mSv "
                    "effective dose. Дозы на МКС ~0.2–0.5 мЗв/сут — Simonsen L., NASA NTRS 20250006168.",
        "url": "https://www.nasa.gov/wp-content/uploads/2023/03/radiation-protection-technical-brief-ochmo.pdf",
    },
    "tripod2015": {
        "citation": "Collins GS, Reitsma JB, Altman DG, Moons KGM. Transparent reporting of a multivariable "
                    "prediction model for individual prognosis or diagnosis (TRIPOD). BMJ. 2015;350:g7594.",
        "url": "https://doi.org/10.1136/bmj.g7594",
    },
}

# Цвета уровней риска (как на шкале сайта)
GREEN, YELLOW, ORANGE, RED = "#00ff88", "#ffcc00", "#ff9500", "#ff3300"

# Земная (предполётная) модель
EARTH = {
    "data_file": "pierson_data.csv",
    "outcome": {
        "code": "latent_virus_reactivation",
        "ru": "Риск реактивации латентных герпесвирусов (ВЭБ, VZV, ЦМВ) в ходе ~6-месячного полёта",
        "en": "Risk of latent herpesvirus reactivation (EBV, VZV, CMV) during a ~6-month mission",
        "definition_ru": "Реактивация хотя бы одного из трёх вирусов (ebv/vzv/cmv_reactivation = 1).",
    },
    "inputs": {
        "sex": {"type": "sex", "required": True,
                "label": {"ru": "Пол", "en": "Sex"}},
        "vo2max": {"type": "number", "required": True, "unit": "ml/kg/min", "min": 5, "max": 100,
                   "plausible": [15, 85], "label": {"ru": "VO₂max", "en": "VO₂max"}},
        "pullups": {"type": "number", "required": True, "unit": "reps", "min": 0, "max": 150,
                    "plausible": [0, 60], "label": {"ru": "Подтягивания", "en": "Pull-ups"}},
        "pushups": {"type": "number", "required": True, "unit": "reps", "min": 0, "max": 500,
                    "plausible": [0, 150], "label": {"ru": "Отжимания", "en": "Push-ups"}},
    },
    # Индекс подготовки F = sum(w_k * m_k). Веса пропорциональны |ln RR| из Agha et al. 2020:
    # выносливость (VO2max) -29% -> 0.34, верхний плечевой пояс -39% -> 0.49; 0.34 : 0.49 = 0.4 : 0.6,
    # вторая доля поровну на отжимания и подтягивания.
    "components": {
        "vo2max": {"weight": 0.4,
                   "threshold": {"M": 43.0, "F": 36.0}, "softness": {"M": 2.0, "F": 2.0}},
        "pushups": {"weight": 0.3,
                    "threshold": {"M": 45.0, "F": 20.0}, "softness": {"M": 4.0, "F": 3.0}},
        "pullups": {"weight": 0.3,
                    "threshold": {"M": 10.0, "F": 3.0}, "softness": {"M": 1.5, "F": 1.0}},
    },
    "component_columns": {"vo2max": "vo2max_percentile", "pushups": "push_ups_group",
                          "pullups": "pull_ups_group"},
    "terms": ["intercept", "fitness_index", "sex_male"],
    "priors": {
        "intercept": {"mean": 0.0, "sd": 2.5,
                      "why": "Слабоинформативное априорное распределение (Gelman et al., 2008): "
                             "базовый риск не задаём заранее.", "refs": ["gelman2008"]},
        "fitness_index": {"mean": 0.0, "sd": 2.5,
                          "why": "Слабоинформативное (Gelman et al., 2008): знак и силу эффекта определяют "
                                 "данные астронавтов. Опубликованные эффекты Agha 2020 (−29%/−39%) задают веса "
                                 "внутри индекса и служат проверкой согласованности, но в априорное "
                                 "распределение не входят — это то же исследование, что и датасет (двойной "
                                 "учёт). Данные общей популяции (Chastin 2021: HR 0.69) подтверждают "
                                 "направление, но не переносимы по величине; оба варианта — в анализе "
                                 "чувствительности.",
                          "refs": ["gelman2008", "agha2020", "chastin2021"]},
        "sex_male": {"mean": 0.0, "sd": 0.5,
                     "why": "Скептическое: данные противоречивы — у Stowe et al. (2000) реактивация ВЭБ "
                            "чаще у женщин (60% vs 35%), в датасете команды — чаще у мужчин; "
                            "половые различия иммунного ответа существуют (Klein & Flanagan, 2016), "
                            "но их направление для реактивации в полёте не установлено.",
                     "refs": ["stowe2000", "klein2016"]},
    },
    # Границы уровней в пределах диапазона модели (~53-90%); в исходной когорте реактивация у 77%.
    "risk_levels": [
        {"code": "low", "below": 65.0, "color": GREEN},
        {"code": "moderate", "below": 80.0, "color": YELLOW},
        {"code": "elevated", "below": 86.0, "color": ORANGE},
        {"code": "high", "below": 101.0, "color": RED},
    ],
    "sensitivity": {
        "fitness_prior_chastin": {"fitness_index": {"mean": -0.5, "sd": 1.0}},
        "fitness_prior_agha": {"fitness_index": {"mean": -1.5, "sd": 1.0}},
        "fitness_prior_wide": {"fitness_index": {"mean": 0.0, "sd": 10.0}},
        "sex_prior_weak": {"sex_male": {"mean": 0.0, "sd": 2.5}},
        "all_priors_x0.5": "scale_sd:0.5",
        "all_priors_x2": "scale_sd:2.0",
        "weights_equal": {"weights": {"vo2max": 1 / 3, "pushups": 1 / 3, "pullups": 1 / 3}},
        "weights_vo2_dominant": {"weights": {"vo2max": 0.6, "pushups": 0.2, "pullups": 0.2}},
        "weights_vo2_only": {"weights": {"vo2max": 1.0, "pushups": 0.0, "pullups": 0.0}},
    },
}

# Полётная модель
# Порог ВЭБ: геометрическая середина между контролем (40 копий/мл) и средним в полёте (417),
# данные agha_data.csv (Pierson et al. 2005).
EBV_CONTROL, EBV_FLIGHT = 40.0, 417.0
EBV_THRESHOLD = round((EBV_CONTROL * EBV_FLIGHT) ** 0.5, 1)

# Относительный рост «до -> после» значим, если превышает критическую разницу (RCV):
# RCV = sqrt(2) * z * sqrt(CVa^2 + CVi^2), z = 1.645 (односторонний 95%).
RCV_Z = 1.645
ASSAY_CV = 0.05  # аналитическая вариабельность
BIOVAR = {
    "il6": {"cvi": 0.30, "note": "нижняя граница диапазона 30–48% (чувствительнее)", "ref": "il6_bv"},
    "cortisol": {"cvi": 0.16, "note": "EFLM, утренний кортизол сыворотки; в разных версиях базы 15–21%", "ref": "cortisol_bv"},
    "nlr": {"cvi": round(math.sqrt(0.161 ** 2 + 0.104 ** 2), 3),
            "note": "из CVi нейтрофилов 16.1% и лимфоцитов 10.4% (дельта-метод)", "ref": "leuko_bv"},
}


def rcv(cvi: float, cva: float = ASSAY_CV, z: float = RCV_Z) -> float:
    return math.sqrt(2.0) * z * math.sqrt(cva ** 2 + cvi ** 2)


RCV = {k: round(rcv(v["cvi"]), 3) for k, v in BIOVAR.items()}

# Полётная модель не обучается: в aggregated_dataset.csv исход совпадает с суммой входов
# (37 из 41 строки). Датасет используется только в training/checks.py.


def _logit(p: float) -> float:
    return math.log(p / (1.0 - p))


# Длительность: доля астронавтов с выделением вирусов, «Шаттл» 10–16 сут против МКС ≥180 сут (Rooney 2019).
SHEDDING_SHORT_LONG = {"any": (0.53, 0.61), "VZV": (0.41, 0.65), "EBV": (0.82, 0.96), "CMV": (0.47, 0.61)}
SHORT_DAYS, LONG_DAYS = 13, 180
_DOUBLINGS = math.log2((LONG_DAYS + 1) / (SHORT_DAYS + 1))
DURATION_EFFECTS = {k: round((_logit(b) - _logit(a)) / _DOUBLINGS, 3) for k, (a, b) in SHEDDING_SHORT_LONG.items()}
_EFF = sorted(DURATION_EFFECTS.values())
DURATION_MEAN = round((_EFF[1] + _EFF[2]) / 2, 3)          # медиана четырёх оценок
DURATION_SD = round((_EFF[-1] - _EFF[0]) / (2 * 1.645), 3)  # 90%-диапазон — от меньшей оценки до большей

# Q_LATE — вероятность, что стабильная в начале полёта подсистема вовлечётся к 180-м суткам (экспертная оценка).
Q_LATE = {"central": 0.15, "low": 0.07, "high": 0.30}
# При ≥2 вовлечённых подсистемах исход достигнут; меньше 1 — на случайный выброс измерения.
P_MET = {"central": 0.90, "low": 0.80, "high": 0.97}


def state_anchors(q: float, p_met: float) -> list[float]:
    """Логит вероятности исхода к 180 сут при 0, 1 и 2 вовлечённых подсистемах из 4."""
    p0 = 1 - (1 - q) ** 4 - 4 * q * (1 - q) ** 3   # нужны ещё две подсистемы
    p1 = 1 - (1 - q) ** 3                           # нужна ещё одна
    return [_logit(p0), _logit(p1), _logit(p_met)]


def state_line(q: float, p_met: float) -> tuple[float, float]:
    """Свободный член и наклон по баллу подсистем: прямая МНК через три опорные точки."""
    y = state_anchors(q, p_met)
    slope = (y[2] - y[0]) / 2
    return sum(y) / 3 - slope, slope


def flight_parameters(q: float | None = None, p_met: float | None = None,
                      duration: float | None = None) -> tuple[list[float], list[list[float]]]:
    """Коэффициенты [intercept, dysregulation_score, duration_log2] и их ковариация.

    Неопределённость q и p_met переносится на коэффициенты линеаризацией по логиту (90%-диапазоны -> SD).
    """
    q = Q_LATE["central"] if q is None else q
    p_met = P_MET["central"] if p_met is None else p_met
    b0, b1 = state_line(q, p_met)
    blocks = []
    for rng, line in ((Q_LATE, lambda v: state_line(v, p_met)), (P_MET, lambda v: state_line(q, v))):
        lo, hi = _logit(rng["low"]), _logit(rng["high"])
        a, b = line(rng["low"]), line(rng["high"])
        jac = [(b[i] - a[i]) / (hi - lo) for i in range(2)]
        blocks.append((jac, (hi - lo) / (2 * 1.645)))
    cov = [[sum(j[r] * j[c] * sd ** 2 for j, sd in blocks) for c in range(2)] + [0.0] for r in range(2)]
    cov.append([0.0, 0.0, DURATION_SD ** 2])
    return [b0, b1, DURATION_MEAN if duration is None else duration], cov


_MEAN, _COV = flight_parameters()

FLIGHT = {
    "data_file": "aggregated_dataset.csv",
    "check_files": {"nlr": "inspiration4_cbc.csv", "il6": "inspiration4_il6.csv"},
    "outcome": {
        "code": "multisystem_dysregulation",
        "ru": "Риск многосистемной иммунной дисрегуляции (≥2 подсистем) к концу миссии",
        "en": "Risk of multi-system immune dysregulation (≥2 subsystems) by the end of the mission",
        "definition_ru": "Вовлечены две и более из четырёх подсистем: воспаление, сдвиг лейкоцитов, реактивация "
                         "ВЭБ, стресс-ось. Градация исследований: 0 — нет изменений, 1 — одна подсистема, "
                         "2 — две подсистемы или клиническое проявление, 3 — системная дисрегуляция.",
    },
    "inputs": {
        "il6_b": {"type": "number", "required": False, "unit": "pg/mL", "min": 0, "max": 10000,
                  "plausible": [0, 100], "label": {"ru": "IL-6 до полёта", "en": "IL-6 before"}},
        "il6_a": {"type": "number", "required": True, "unit": "pg/mL", "min": 0, "max": 10000,
                  "plausible": [0, 100], "label": {"ru": "IL-6 в полёте", "en": "IL-6 in flight"}},
        "nlr_b": {"type": "number", "required": False, "unit": "", "min": 0, "max": 100,
                  "plausible": [0.3, 20], "label": {"ru": "NLR до полёта", "en": "NLR before"}},
        "nlr_a": {"type": "number", "required": True, "unit": "", "min": 0, "max": 100,
                  "plausible": [0.3, 20], "label": {"ru": "NLR в полёте", "en": "NLR in flight"}},
        "ebv": {"type": "number", "required": True, "unit": "copies/mL", "min": 0, "max": 1e9,
                "plausible": [0, 1e7], "label": {"ru": "ДНК ВЭБ (слюна)", "en": "EBV DNA (saliva)"}},
        "cortb": {"type": "number", "required": False, "unit": "nmol/L", "min": 0, "max": 5000,
                  "plausible": [30, 1500], "label": {"ru": "Кортизол до полёта", "en": "Cortisol before"}},
        "corta": {"type": "number", "required": True, "unit": "nmol/L", "min": 0, "max": 5000,
                  "plausible": [30, 1500], "label": {"ru": "Кортизол в полёте", "en": "Cortisol in flight"}},
        "days": {"type": "number", "required": True, "unit": "days", "min": 1, "max": 3000,
                 "plausible": [1, 3000], "label": {"ru": "Длительность миссии", "en": "Mission days"}},
    },
    # Подсистема считается вовлечённой, если сработал любой из её критериев.
    # Веса — клиническая значимость (экспертная оценка); в сумме 4, балл читается как число подсистем.
    "markers": {
        "cytokine": {
            "weight": 1.0, "column": "has_cytokine_response",
            "criteria": [
                {"kind": "relative", "before": "il6_b", "after": "il6_a",
                 "threshold": RCV["il6"], "softness": round(0.2 * RCV["il6"], 3)},
                {"kind": "absolute", "field": "il6_a", "threshold": 7.0, "softness": 0.75},
            ],
            "refs": ["elecsys_il6", "il6_bv", "fraser2001", "crucian2014", "kim2024"],
            "why": "Системное воспаление. После полёта IL-6 растёт вместе с IL-10, CRP и MCP-1 — так же, как у "
                   "астронавтов после длительных миссий (Kim 2024); сдвиги цитокинов сохраняются весь полёт "
                   "(Crucian 2014). Абсолютный порог 7 пг/мл — 95-й перцентиль у 817 здоровых (Elecsys IL-6). "
                   f"Относительный порог +{RCV['il6'] * 100:.0f}% = критическая разница (RCV) при "
                   "внутрииндивидуальной вариабельности IL-6 30–48%; у экипажа Inspiration4 по трём анализам до "
                   "полёта — 27% (NASA OSDR, OSD-575).",
        },
        "immune_shift": {
            "weight": 0.75, "column": "has_immune_cell_shift",
            "criteria": [
                {"kind": "relative", "before": "nlr_b", "after": "nlr_a",
                 "threshold": RCV["nlr"], "softness": round(0.2 * RCV["nlr"], 3)},
                {"kind": "absolute", "field": "nlr_a", "threshold": 3.5, "softness": 0.25},
            ],
            "refs": ["forget2017", "paul2020", "leuko_bv", "fraser2001", "kim2024"],
            "why": "NLR растёт в полёте (Paul 2020), но маркер неспецифичен (острый стресс, время забора); "
                   "верхняя граница нормы 3.53 (Forget 2017). Относительный порог "
                   f"+{RCV['nlr'] * 100:.0f}% (RCV): заложенная вариабельность NLR ≈20% совпала с измеренной "
                   "у экипажа Inspiration4 по трём предполётным анализам (training/checks.py). Пониженный вес: "
                   "во всех исследованиях с изолированным сдвигом лейкоцитов исход был лёгким.",
        },
        "viral": {
            "weight": 1.25, "column": "has_viral_reactivation",
            "criteria": [
                {"kind": "log10", "field": "ebv", "threshold": EBV_THRESHOLD, "softness": 0.15},
            ],
            "refs": ["pierson2005", "mehta2017", "rooney2019", "crucian2018"],
            "why": "Прямой признак потери Т-клеточного контроля над латентными вирусами — ближайшее к "
                   "клиническим событиям звено (Mehta 2017; Crucian 2018). Порог ≈129 копий/мл — "
                   "геометрическая середина между уровнем до полёта (40) и средним в полёте (417) по данным "
                   "Pierson 2005 (32 астронавта, 1398 образцов слюны).",
        },
        "neuroendocrine": {
            "weight": 1.0, "column": "has_neuroendocrine_change",
            "criteria": [
                {"kind": "relative", "before": "cortb", "after": "corta",
                 "threshold": RCV["cortisol"], "softness": round(0.2 * RCV["cortisol"], 3)},
                {"kind": "absolute", "field": "corta", "threshold": 550.0, "softness": 25.0},
            ],
            "refs": ["stowe2000", "stowe2001", "mehta2017", "cortisol_bv", "fraser2001"],
            "why": "Стресс-гормоны — пусковое звено реактивации ВЭБ: кортизол (Stowe 2000), катехоламины "
                   "(Stowe 2001); реактивация на МКС совпадала со сдвигом суточного ритма кортизола (Mehta "
                   f"2017). Относительный порог +{RCV['cortisol'] * 100:.0f}% = RCV при CVi кортизола 16% "
                   "(в разных версиях базы EFLM 15–21%, порог тогда +37…+50%). Абсолютный порог 550 нмоль/л — "
                   "ориентир команды (около верхней границы утреннего референсного интервала, зависит от "
                   "метода).",
        },
    },
    "duration": {"field": "days", "reference_days": 180,
                 "transform": "log2((days + 1) / (180 + 1))"},
    # 437 сут — самый длинный полёт (В. Поляков)
    "evidence": {"well_studied_days": 200, "longest_flight_days": 437,
                 "extrapolation_sd_per_doubling": DURATION_MEAN,
                 "refs": ["manzey1998", "garrett2019"]},
    "radiation": {"leo_msv_per_day": [0.2, 0.5], "deep_space_msv_per_day": 1.8, "career_limit_msv": 600,
                  "refs": ["nasa_std3001", "zeitlin2013"]},
    "terms": ["intercept", "dysregulation_score", "duration_log2"],
    "parameters": {"mean": _MEAN, "covariance": _COV},
    "priors": {
        "intercept": {"mean": round(_MEAN[0], 4), "sd": round(math.sqrt(_COV[0][0]), 4),
                      "why": f"Не обучен. Выведен из допущения q = {Q_LATE['central']} ({Q_LATE['low']}–"
                             f"{Q_LATE['high']}): доля подсистем, которые у стабильного в начале полёта человека "
                             "вовлекаются к 6-му месяцу. Для двух из четырёх подсистем это ~11% (90%: ~3–35%). "
                             "Сдвиги обычно возникают в первые недели и сохраняются (Crucian 2014, 2015), поэтому "
                             "стабильные маркеры — благоприятный признак; но поздние изменения возможны: в "
                             "изоляции на 1 год реакции усиливались после 3–4 месяцев (Feuerecker 2019).",
                      "refs": ["crucian2014", "crucian2015", "feuerecker2019", "rooney2019"]},
        "dysregulation_score": {"mean": round(_MEAN[1], 4), "sd": round(math.sqrt(_COV[1][1]), 4),
                                "why": "Не обучен. Следует из определения исхода: при 1 вовлечённой подсистеме "
                                       "нужна ещё одна (~39% при q = 0.15), при 2 исход уже достигнут "
                                       f"({P_MET['central']:.0%}, поправка на выброс единичного измерения). "
                                       "Наклон — прямая через эти три точки.",
                                "refs": []},
        "duration_log2": {"mean": DURATION_MEAN, "sd": DURATION_SD,
                          "why": "Не обучен. Rooney 2019: выделение вирусов в коротких полётах (10–16 сут) и на МКС "
                                 "(≥180 сут) — любые герпесвирусы 53→61%, VZV 41→65%, ВЭБ 82→96%, ЦМВ 47→61%. "
                                 "На удвоение длительности логарифм шансов растёт на "
                                 + ", ".join(f"{v:.2f}" for v in DURATION_EFFECTS.values())
                                 + f"; взята медиана {DURATION_MEAN:.2f}. Риск растёт с длительностью, но всё "
                                   "медленнее: основная часть сдвигов возникает в начале полёта.",
                          "refs": ["rooney2019", "mehta2017", "crucian2015"]},
    },
    "risk_levels": [
        {"code": "low", "below": 20.0, "color": GREEN},
        {"code": "moderate", "below": 50.0, "color": YELLOW},
        {"code": "elevated", "below": 80.0, "color": ORANGE},
        {"code": "high", "below": 101.0, "color": RED},
    ],
    # Другие допущения (reports/metrics.json -> scenarios)
    "scenarios": {
        "q_low": {"q": Q_LATE["low"]},
        "q_high": {"q": Q_LATE["high"]},
        "p_met_low": {"p_met": P_MET["low"]},
        "duration_low": {"duration": _EFF[0]},
        "duration_high": {"duration": _EFF[-1]},
        "weights_equal": {"weights": {"cytokine": 1.0, "immune_shift": 1.0, "viral": 1.0, "neuroendocrine": 1.0}},
    },
}
