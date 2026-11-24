"""Simplified Chinese terminology for the model and its interpretation."""

FIELD_LABELS = {
    "sex": "性别", "vo2max": "最大摄氧量", "pullups": "引体向上", "pushups": "俯卧撑",
    "il6_b": "飞行前 IL-6", "il6_a": "飞行中 IL-6", "nlr_b": "飞行前 NLR", "nlr_a": "飞行中 NLR",
    "ebv": "唾液 EBV DNA", "cortb": "飞行前皮质醇", "corta": "飞行中皮质醇", "days": "计划任务时长",
}

OUTCOMES = {
    "earth": "约六个月的任务中潜伏疱疹病毒（EBV、VZV 或 CMV）再激活的风险",
    "flight": "任务结束前出现多系统免疫失调（至少两个子系统受累）的风险",
}

CONSULTANT = {
    "interval": "90% 区间", "pp": "个百分点", "disclaimer": "健康相关决策应与医生共同作出。",
    "sex": {"M": "男性", "F": "女性"},
    "earth": {
        "outcome_short": "飞行期间潜伏病毒再激活的风险",
        "levels": {"low": "低于平均水平", "moderate": "平均水平", "elevated": "高于平均水平", "high": "高"},
        "level_explain": {
            "low": "该体能状况接近原研究中准备最充分的乘组成员。",
            "moderate": "部分体能指标已达标，仍有改善空间。",
            "elevated": "多数体能指标未达到目标或处于临界范围。",
            "high": "该体能状况接近原研究中飞行前体能较低的成员，该组几乎所有人都出现过病毒再激活。",
        },
        "context": "在建立模型所依据的国际空间站队列中，77% 的成员出现潜伏疱疹病毒（EBV、VZV 或 CMV）再激活。长航时任务中这一现象通常没有症状。模型估计飞行前体能与该风险的关系。",
        "names": {"vo2max": "最大摄氧量", "pushups": "俯卧撑", "pullups": "引体向上"},
        "names_acc": {"vo2max": "最大摄氧量", "pushups": "俯卧撑", "pullups": "引体向上"},
        "driver": {
            "above": "{name}为 {value} {unit}，高于目标 {thr} {thr_unit}，模型估计风险降低 {eff} 个百分点。",
            "borderline": "{name}为 {value} {unit}，接近目标 {thr} {thr_unit}，模型中的保护效应为 −{eff} 个百分点。",
            "below": "{name}为 {value} {unit}，低于目标 {thr} {thr_unit}，模型中的保护效应较小。",
        },
        "sex_driver": "性别为{sex}。研究中男性的估计风险略高于女性，相差 {eff} 个百分点，但这一差异存在统计不确定性。",
        "what_if": "若{name}达到 {target} {unit}，估计值可降至约 {risk}%（降低 {pot} 个百分点）。",
        "recs": {
            "aerobic": ("有氧耐力", "可与医生讨论有氧及间歇训练，目标最大摄氧量 ≥ {target} mL/kg/min。飞行前心肺适能较高与再激活风险约低 29% 相关（Agha 等，2020）。"),
            "upper_body": ("上肢耐力", "肌耐力目标为俯卧撑 ≥ {push} 次、引体向上 ≥ {pull} 次。上肢耐力较好与风险约低 39%、再激活较晚和病毒载量较低有关（Agha 等，2020）。"),
            "maintain": ("保持体能", "在轨期间定期锻炼。研究中，飞行前体能较低且返回后体能下降较多的乘员最常出现再激活（Agha 等，2020）。"),
            "basics": ("日常预防", "睡眠、营养和压力管理有助于维持免疫功能。可与医生讨论个人预防方案及疫苗接种状况（Crucian 等，2018）。"),
            "consult": ("医疗团队", "建议与乘组医生讨论飞行前的体能训练与监测方案。"),
        },
        "notes": ["年龄校正尚在开发中。"],
    },
    "flight": {
        "outcome_short": "多系统免疫失调的风险",
        "levels": {"low": "低", "moderate": "中等", "elevated": "偏高", "high": "高"},
        "level_explain": {
            "low": "各子系统均未触发模型阈值，或变化很小。",
            "moderate": "单个子系统出现变化，或指标位于临界范围，应结合连续测量。",
            "elevated": "一个子系统变化明显（尤其是 EBV 再激活），或两个子系统处于临界范围。",
            "high": "至少两个子系统受到影响，建议由乘组医生评估并随访。",
        },
        "context": "模型考察炎症（IL-6）、白细胞变化（NLR）、EBV 再激活和应激激素（皮质醇）。各指标按其临床意义赋权，参数来自公开研究。项目尚缺少将个人指标与独立临床结局配对的数据。",
        "names": {"cytokine": "炎症（IL-6）", "immune_shift": "白细胞变化（NLR）", "viral": "EBV 再激活", "neuroendocrine": "应激轴（皮质醇）"},
        "names_lower": {"cytokine": "IL-6", "immune_shift": "NLR", "viral": "EBV DNA", "neuroendocrine": "皮质醇"},
        "measure": {"cytokine": ("IL-6", "pg/mL"), "immune_shift": ("NLR", ""), "viral": ("EBV DNA", "copies/mL"), "neuroendocrine": ("皮质醇", "nmol/L")},
        "status": {"above": "高于模型阈值", "borderline": "处于临界范围", "below": "低于模型阈值"},
        "why": {"absolute": "参考值 {thr} {unit}", "relative": "参考变化值 +{thr}%", "log10": "再激活阈值约为 {thr} {unit}"},
        "anchor": {
            "cytokine": "参考值最高为 7 pg/mL（健康人群第 95 百分位）。",
            "immune_shift": "健康成人的 NLR 参考范围为 0.78–3.53。",
            "viral": "研究报告的唾液 EBV DNA 均值约为飞行前 40 拷贝/mL、飞行中 417 拷贝/mL。",
            "neuroendocrine": "模型阈值为较基线上升超过 39%，或浓度高于 550 nmol/L。",
        },
        "was": "{before} → {after} {unit}（{change:+.0f}%）",
        "pattern": {
            0: "各子系统均未超过阈值。",
            1: "一个子系统（{names}）出现变化。按研究的分级属于轻度，应结合后续趋势。",
            "n": "涉及的子系统包括{names}。多系统免疫变化通常无症状。在 NASA 对 112 名航天员的回顾中，6 人出现病毒再激活相关症状，均为轻症（Rooney 等，2019）。",
            "stress_viral": "应激反应和 EBV 再激活同时出现，符合既往研究描述的关联（Stowe 等，2001）。",
            "inflammation": "IL-6 和 NLR 同时升高提示系统性炎症变化（Paul 等，2020；Crucian 等，2018）。",
        },
        "duration_ref": "任务时长 {days:g} 天是模型的参考值。许多免疫变化在最初数周出现并持续。研究中，10–16 天任务和国际空间站任务的病毒再激活比例分别为 53% 和 61%（Crucian 等，2015；Rooney 等，2019）。",
        "duration_flat": "按当前指标，任务时长 {days:g} 天对估计值的影响很小。",
        "duration": "任务时长 {days:g} 天，与 180 天任务相比，估计值相差 {eff} 个百分点。模型中风险随时长增加，但增幅逐渐减小（Crucian 等，2015；Rooney 等，2019）。",
        "duration_stable": "指标稳定时，模型中风险随时长上升较慢。后期仍可能发生变化，隔离研究曾在 3–4 个月后观察到免疫反应增强（Feuerecker 等，2019）。",
        "what_if": "若{name}回到参考范围，估计值可降至约 {risk}%（降低 {pot} 个百分点）。",
        "what_if_all": "若所有发生变化的指标回到参考范围，估计值可降至约 {risk}%（降低 {pot} 个百分点）。",
        "recs": {
            "viral": ("病毒再激活", "告知乘组医生，关注皮疹、黏膜病变、发热和疲劳，并随访 EBV DNA。治疗决定由医生作出（Mehta 等，2017）。"),
            "neuroendocrine": ("应激与昼夜节律", "关注睡眠、照明、工作负荷和心理支持。皮质醇随昼夜变化，复测宜在相同时段进行（Stowe 等，2001；Crucian 等，2018）。"),
            "cytokine": ("炎症", "随访 IL-6 和其他炎症指标，评估有无感染表现，并保持适量运动、充足睡眠和营养（Crucian 等，2018）。"),
            "immune_shift": ("血细胞计数", "在统一时段复查血常规及白细胞分类。急性应激和取样时间均可影响 NLR（Paul 等，2020）。"),
            "monitoring": ("趋势监测", "长航时任务中，应按与医疗团队商定的计划复测；连续测量比单次结果更有参考价值。"),
            "priority": ("优先评估", "风险估计较高，建议优先与乘组医生讨论结果。"),
            "prevention": ("预防", "保持运动、睡眠、营养和压力管理等预防措施（Crucian 等，2018）。"),
        },
        "notes": ["参数来自已发表的研究。项目缺少独立的个人结局数据，分组表中的结局往往等于输入标志之和。{low}–{high}% 区间反映了模型假设的不确定性。"],
        "baseline_timing": "建议在起飞前 1–2 个月测量基线。Inspiration4 的四名成员在起飞前 3 天的淋巴细胞计数均比起飞前 1.5–3 个月高 30%–73%，其中一人的 IL-6 达到此前的 2.2 倍。",
        "radiation": "模型未纳入辐射。在 {days:g} 天内，国际空间站轨道估计剂量约为 {leo_lo}–{leo_hi} mSv，行星际飞行约为 {deep} mSv（Zeitlin 等，2013）。模型引用的 NASA 职业限值为 {limit} mSv。",
        "warn": {
            "baseline_missing": "未提供{field}，仅按绝对值评估“{name}”。",
            "baseline_not_positive": "{field}不大于零，未对“{name}”使用相对变化判据。",
            "duration_limited_evidence": "超过六个月的免疫研究数据有限（NASA 双胞胎研究中一人飞行 340 天），估计不确定性较大。",
            "duration_beyond_evidence": "{days:g} 天超过已记录的最长单次太空飞行 437 天。此处为外推，估计区间相应加宽。",
        },
    },
}
