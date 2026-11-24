/* Summary of completed visits. Disease endpoints and risk scales come from the prediction API. */
(() => {
    'use strict';

    const markers = [
        { key: 'il6_a', before: 'il6_b', name: 'IL-6', unit: ['pg/mL', 'пг/мл', 'pg/mL'] },
        { key: 'nlr_a', before: 'nlr_b', name: 'NLR', unit: ['', '', ''] },
        { key: 'ebv', name: 'EBV DNA', unit: ['copies/mL', 'копий/мл', '拷贝/mL'] },
        { key: 'corta', before: 'cortb', name: ['Cortisol', 'Кортизол', '皮质醇'], unit: ['nmol/L', 'нмоль/л', 'nmol/L'] }
    ];

    function node(tag, text, cls) {
        const item = document.createElement(tag);
        if (text != null) item.textContent = text;
        if (cls) item.className = cls;
        return item;
    }

    function fitLine(x, y) {
        if (x.length < 2) return null;
        const avg = values => values.reduce((a, b) => a + b, 0) / values.length;
        const xm = avg(x), ym = avg(y);
        const sum = x.reduce((s, v) => s + (v - xm) ** 2, 0);
        if (!sum) return null;
        const slope = x.reduce((s, v, i) => s + (v - xm) * (y[i] - ym), 0) / sum;
        return { slope, at: day => ym + slope * (day - xm) };
    }

    // The table next to the plot exposes all values to keyboard and screen-reader users.
    function plot(canvas, xs, ys, intervals, trend, axisLabels, percent) {
        const width = Math.max(210, canvas.clientWidth || 380), height = 172;
        const dpr = window.devicePixelRatio || 1;
        canvas.width = Math.round(width * dpr);
        canvas.height = Math.round(height * dpr);
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        ctx.scale(dpr, dpr);
        const left = 42, right = width - 24, top = 14, bottom = height - 30;
        const max = percent ? 100 : Math.max(1, ...ys) * 1.12;
        const x = n => xs.length === 1 ? (right + left) / 2 : left + (right - left) * (n - xs[0]) / (xs.at(-1) - xs[0]);
        const y = n => bottom - n * (bottom - top) / max;
        const segment = (x0, y0, x1, y1) => {
            ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
        };
        ctx.font = '12px Inter, sans-serif';
        ctx.fillStyle = '#ced5dc'; ctx.textAlign = 'right'; ctx.strokeStyle = '#344451';
        for (const tick of [0, max / 2, max]) {
            segment(left, y(tick), right, y(tick));
            ctx.fillText(Number(tick.toPrecision(3)).toString(), left - 6, y(tick) + 4);
        }
        if (trend) {
            ctx.save(); ctx.beginPath(); ctx.rect(left, top, right - left, bottom - top); ctx.clip();
            ctx.strokeStyle = '#8cd7dc'; ctx.lineWidth = 2; ctx.setLineDash([5, 4]);
            segment(x(xs[0]), y(trend.at(xs[0])), x(xs.at(-1)), y(trend.at(xs.at(-1))));
            ctx.restore();
        }
        if (!percent && xs.length > 1) {
            ctx.strokeStyle = '#95804f'; ctx.lineWidth = 1.4;
            for (let i = 1; i < xs.length; i++) segment(x(xs[i-1]), y(ys[i-1]), x(xs[i]), y(ys[i]));
        }
        ctx.textAlign = 'center';
        xs.forEach((v, i) => {
            const px = x(v);
            if (intervals) {
                const [low, high] = intervals[i];
                ctx.strokeStyle = '#a8b7c3'; ctx.lineWidth = 1.2;
                segment(px, y(low), px, y(high));
                segment(px - 4, y(low), px + 4, y(low)); segment(px - 4, y(high), px + 4, y(high));
            }
            ctx.fillStyle = '#f7c950'; ctx.beginPath(); ctx.arc(px, y(ys[i]), 4, 0, 2 * Math.PI); ctx.fill();
            // Closely spaced visit days remain available in the exact table.
            if (i === 0 || i === xs.length - 1 || (px - x(xs[i - 1]) > 28 && x(xs[i + 1]) - px > 28)) {
                ctx.fillStyle = '#ced5dc'; ctx.fillText(axisLabels[i], px, bottom + 19);
            }
        });
    }

    function table(headings, rows) {
        const shell = node('div', null, 'series-table-scroll');
        const table = node('table'), head = table.createTHead().insertRow();
        for (const label of headings) {
            const th = node('th', label); th.scope = 'col'; head.append(th);
        }
        const body = table.createTBody();
        for (const row of rows) {
            const tr = body.insertRow();
            row.forEach(value => { tr.insertCell().textContent = value; });
        }
        shell.append(table);
        return shell;
    }

    window.renderVisitEvidence = function (result, day, lang) {
        const tr = (en, ru, zh) => lang === 'zh' ? zh : lang === 'ru' ? ru : en;
        const info = result.series_assessment;
        const block = node('section', null, 'series-endpoint');
        const isFlight = result.model === 'flight';
        if (isFlight) {
            const dayLabel = Number.isInteger(day) ? tr('day ', 'дню ', "飞行第") + day : tr('the visit', 'дате замера', "本次测量");
            block.append(node('h4', lang === 'zh' ? (Number.isInteger(day) ? '截至飞行第' + day + '天的综合结局' : '截至本次测量的综合结局') : tr('Composite outcome by ', 'Общий исход к ', "综合结局") + dayLabel));
            block.append(node('p', tr('Mission failure or clinically confirmed immunodeficiency with a documented disease.',
                'Срыв миссии или клинически подтверждённый иммунодефицит с конкретным заболеванием.', "任务失败，或临床确诊免疫缺陷并伴有记录在案的具体疾病。")));
            block.append(node('p', Number.isInteger(day) ?
                tr('Probability unavailable. A calibrated model with dated, independently ascertained events is needed.',
                   'Вероятность пока не оценена. Нужна модель, проверенная на независимо зарегистрированных событиях с датами.', "目前无法估计概率。需要用独立确认且有日期的事件进行模型校准与验证。") :
                tr('This saved visit has no sampling day. Enter its day and recalculate.',
                   'В сохранённом замере нет дня взятия пробы. Укажите день и пересчитайте.', "此记录缺少采样日。请输入飞行日并重新计算。"), 'series-note'));
            if (Number.isInteger(day) && day > result.inputs.days) {
                block.append(node('p', tr('This sample is later than the planned mission length in the In-Flight card. Review the planned duration in the first flight visit.',
                    'Эта проба взята после планового срока, указанного в карточке In-Flight. Плановый срок можно уточнить в первом полётном замере.', "本次采样日晚于记录的计划任务时长。请核对首次飞行测量中的计划时长。"), 'series-note'));
            }
        }
        block.append(node('h4', tr('Human literature reference intervals','Сравнение с данными исследований на людях', "人体研究文献中的参考区间")));
        if (!info || !Array.isArray(info.markers)) {
            block.append(node('p', tr('Reference comparison is unavailable for this calculation.',
                'Для этого расчёта сравнение с референсами недоступно.', "本次计算没有可用的参考区间比较结果。"), 'series-note'));
            return block;
        }
        const routes = {
            human_only: tr('Model 1 · human data', 'Модель 1 · данные людей', "模型 1 · 人体数据"),
            human_plus_animal: tr('Model 2 · human and animal data', 'Модель 2 · данные людей и животных', "模型 2 · 人体与动物数据"),
            undetermined: tr('Evidence model undetermined', 'Модель по источнику данных пока не определена', "尚无法确定适用的证据模型")
        };
        const statuses = {
            inside:tr('Inside, inclusive','В пределах, включая границы', "区间内（含边界）"),
            above:tr('Above p95','Выше p95', "高于 p95"), below:tr('Below p05','Ниже p05', "低于 p05"),
            missing_value:tr('Value missing','Нет значения', "缺少测量值"), no_reference:tr('No applicable reference','Нет подходящего интервала', "无适用的参考区间"),
            context_required:tr('Check the test protocol','Уточните протокол измерения', "请核对检测方案"),
            ambiguous_reference:tr('Overlapping references','Несколько подходящих интервалов', "多个参考区间重叠")
        };
        block.append(node('p', routes[info.route]));
        const detail = node('details', null, 'series-evidence');
        detail.append(node('summary', tr('Compared with p05–p95', 'Сопоставлено с p05–p95', "已与 p05–p95 比较") + ' · ' + info.assessed + '/' + info.total));
        const names = {vo2max:'VO₂max',pullups:tr('Pull-ups','Подтягивания', "引体向上"),pushups:tr('Push-ups','Отжимания', "俯卧撑"),
            il6_a:'IL-6',il6_b:'IL-6',nlr_a:'NLR',nlr_b:'NLR',ebv:'EBV DNA',corta:tr('Cortisol','Кортизол', "皮质醇"),cortb:tr('Cortisol','Кортизол', "皮质醇")};
        const rows = info.markers.map(r => [
            names[r.field] + ' · ' + (r.phase === 'inflight' ? tr('in flight','в полёте', "飞行期间") : tr('pre-flight','до полёта', "飞行前")),
            r.value == null ? '—' : String(r.value) + ' ' + r.unit,
            r.p05 == null ? '—' : r.p05 + ' – ' + r.p95,
            statuses[r.status], r.reference_id || '—'
        ]);
        detail.append(table([tr('Marker','Показатель', "指标"),tr('Value','Значение', "测量值"),'p05 – p95',tr('Result','Результат', "结果"),tr('Reference','Референс', "参考来源")], rows));
        detail.append(node('p', tr('Both percentile boundaries are included. A verified out-of-range value selects Model 2.',
            'Обе границы входят в интервал. Достаточно одного подтверждённого выхода за границы для выбора Модели 2.', "两个百分位边界均计入区间。只要一个已核实的指标超出区间，即选择模型 2。"), 'series-note'));
        block.append(detail);
        return block;
    };

    window.renderMissionSummary = function (host, records, lang, scenario, onScenario) {
        const tr = (en, ru, zh) => lang === 'zh' ? zh : lang === 'ru' ? ru : en;
        const languageIndex = {en: 0, ru: 1, zh: 2}[lang];
        const fmt = (v, places = 1) => Number(v).toLocaleString(lang, { maximumFractionDigits: places });
        const val = v => Number.isFinite(v) ? fmt(v, 4) : '—';
        const earth = records[0].result, flights = records.slice(1), last = flights.at(-1).result;
        const timed = flights.every((r, i) => Number.isInteger(r.day) && (i === 0 || r.day > flights[i - 1].day));
        const xs = flights.map((r, i) => timed ? r.day : i + 1);
        const axis = timed ? tr('Flight day', 'День полёта', "飞行日") : tr('Flight visit number', 'Номер полётного замера', "飞行测量序号");
        const risk = flights.map(r => r.result.risk);
        const intervals = flights.map(r => [r.result.risk_interval.low, r.result.risk_interval.high]);
        const trend = fitLine(xs, risk);
        const choice = node('select'); choice.id = 'mission-scenario';
        const label = node('label', tr('Scenario', 'Сценарий', "场景")); label.htmlFor = choice.id;
        const scenarios = [['space',tr('Space mission','Космическая миссия', "太空任务")], ['checkup',tr('General health check','Чекап', "常规健康检查")], ['extreme',tr('Extreme conditions / Arctic shift','Экстремальные условия / арктическая вахта', "极端环境／北极轮班")]];
        for (const [id, text] of scenarios) choice.add(new Option(text, id));
        choice.value = scenario; choice.onchange = () => onScenario(choice.value);
        const selectBox = node('div', null, 'series-select'); selectBox.append(label, choice);
        host.replaceChildren(node('h3', tr('Integrated result','Сводный результат', "综合结果")), selectBox,
            node('p', tr('The scenario is a display setting. Both estimates retain their spaceflight endpoints.', 'Сценарий меняет подпись. Обе оценки относятся к указанным ниже исходам космической миссии.', "场景仅改变显示标签。两项估计仍对应各自的航天任务结局。"), 'series-note'));

        host.append(window.renderVisitEvidence(last, flights.at(-1).day, lang));
        const cards = node('div', null, 'series-summary-cards');
        for (const [name, body] of [[tr('Pre-flight · Earth','До полёта · Earth', "飞行前 · 地面模型"), earth],
                                     [tr('Latest in-flight visit','Последний полётный замер', "最近一次飞行测量"), last]]) {
            const card = node('article');
            card.append(node('h4', name), node('p', fmt(body.risk) + '%', 'series-value'),
                node('p', body.interpretation.outcome),
                node('small', tr('90% interval ', '90% интервал ', "90% 区间 ") + fmt(body.risk_interval.low) + '–' + fmt(body.risk_interval.high) + '%'));
            cards.append(card);
        }
        host.append(cards);
        const title = node('h4', tr('In-flight risk over time','Динамика оценки In-Flight', "飞行期间的风险估计变化"));
        const chart = node('canvas'); chart.setAttribute('aria-hidden', 'true');
        host.append(title, node('p', axis + ' · ' + tr('estimate (%) and 90% interval', 'оценка (%) и 90% интервал', "估计值（%）与 90% 区间"), 'series-note'), chart);
        if (trend) {
            const unit = timed ? tr('pp/day','п.п./сут', "个百分点/天") : tr('pp/visit','п.п./замер', "个百分点/次");
            const caption = flights.length === 2 ? tr('Change between two visits', 'Изменение между двумя замерами', "两次测量之间的变化") : tr('Linear trend across three visits', 'Линейный тренд по трём замерам', "三次测量的线性趋势");
            const slopeText = new Intl.NumberFormat(lang, {maximumSignificantDigits:3,signDisplay:'exceptZero'}).format(trend.slope);
            host.append(node('p', caption + ' · ' + slopeText + ' ' + unit, 'series-trend'));
        } else {
            host.append(node('p', tr('A second in-flight visit will show the direction of change.', 'Направление изменения появится после второго полётного замера.', "完成第二次飞行测量后可查看变化方向。"), 'series-note'));
        }
        host.append(table([tr('Visit','Замер', "测量"), tr('Flight day','День полёта', "飞行日"), tr('Estimate','Оценка', "估计值"), tr('90% interval','90% интервал', "90% 区间")],
            flights.map((r, i) => ['F' + (i + 1), val(r.day), fmt(r.result.risk) + '%', intervals[i].map(v => fmt(v)).join('–') + '%'])));

        const systems = {
            cytokine: 'IL-6', immune_shift: 'NLR', viral: 'EBV DNA', neuroendocrine: tr('cortisol','кортизол', "皮质醇")
        };
        const factors = last.factors.filter(f => f.kind === 'biomarker_system' && f.status !== 'below');
        if (factors.length) {
            const peak = Math.max(...factors.map(f => f.effect_pp));
            const top = factors.filter(f => f.effect_pp === peak).map(f => systems[f.factor]).filter(Boolean);
            host.append(node('p', tr('Largest modeled contribution at the latest visit — ', 'Наибольший вклад в последнюю оценку модели — ', "最近一次测量中对模型估计贡献最大的是 ") + top.join(', ') + ' (' + fmt(peak) + ' ' + tr('pp','п.п.', "个百分点") + ').'));
        } else {
            host.append(node('p', tr('All four markers are below the model’s activation ranges at the latest visit.', 'По правилам модели на последнем замере все четыре маркера ниже зоны срабатывания.', "最近一次测量的四项指标均低于模型的触发范围。")));
        }

        const markerChoice = node('select'); markerChoice.id = 'series-marker';
        const markerName = m => Array.isArray(m.name) ? m.name[languageIndex] : m.name;
        markers.forEach(m => markerChoice.add(new Option(markerName(m) + (m.unit[languageIndex] ? ' · ' + m.unit[languageIndex] : ''), m.key)));
        const markerLabel = node('label', tr('Marker','Маркер', "指标")); markerLabel.htmlFor = markerChoice.id;
        const fieldBox = node('div', null, 'series-select'); fieldBox.append(markerLabel, markerChoice);
        const markerChart = node('canvas'); markerChart.setAttribute('aria-hidden', 'true');
        const markerData = node('div'), markerAxis = node('p',null,'series-note');
        host.append(node('h4',tr('Measured values','Введённые показатели', "实测数值")), fieldBox, markerAxis, markerChart, markerData);
        let markerX, markerValues, markerTicks;
        function draw() {
            plot(chart, xs, risk, intervals, trend, xs.map(String), true);
            plot(markerChart, markerX, markerValues, null, null, markerTicks, false);
        }
        function showMarker() {
            const m = markers.find(v => v.key === markerChoice.value);
            const baseline = m.before ? flights[0].result.inputs[m.before] : null;
            const values = flights.map(r => r.result.inputs[m.key]);
            const hasBaseline = Number.isFinite(baseline);
            markerX = hasBaseline ? [0, ...flights.map((_, i) => i + 1)] : xs;
            markerTicks = hasBaseline ? [tr('Pre','До', "飞行前"), ...flights.map((_, i) => 'F' + (i + 1))] : xs.map(String);
            markerValues = hasBaseline ? [baseline, ...values] : values;
            markerAxis.textContent = hasBaseline ? tr('Sample order · pre-flight sample and flight visits', 'Порядок проб · до полёта и полётные замеры', "样本顺序 · 飞行前与飞行期间") : axis;
            const rows = [[tr('Pre-flight baseline','Предполётная проба', "飞行前基线"), '—', val(baseline), '—']];
            values.forEach((v, i) => {
                const before = i ? values[i - 1] : baseline;
                const d = Number.isFinite(before) ? v - before : null;
                rows.push(['F' + (i + 1), val(flights[i].day), val(v), d === null ? '—' : (d > 0 ? '+' : '') + fmt(d,4)]);
            });
            markerData.replaceChildren(table([tr('Sample','Проба', "样本"), tr('Flight day','День полёта', "飞行日"), markerName(m) + (m.unit[languageIndex] ? ' · ' + m.unit[languageIndex] : ''), tr('Change from previous sample','Δ к предыдущей пробе', "与上次采样的差值")], rows));
            draw();
        }
        markerChoice.onchange = showMarker; showMarker();
        const evidence = node('details', null, 'series-evidence');
        evidence.append(node('summary',tr('Population and animal evidence','Данные людей и животных', "人体与动物研究证据")),
            node('p',tr('Earth and In-Flight retain their stated endpoints. Selection of human or human–animal evidence uses the human reference intervals for the entered measurements.',
                      'Earth и In-Flight рассчитывают указанные в карточках исходы. Для выбора человеческих или смешанных источников используются интервалы человеческих исследований по введённым показателям.', "地面模型与飞行模型分别估计各自的结局。系统根据输入值与人体参考区间的比较选择证据模型。")),
            node('p',tr('Rat NLR on SLS-2 can inform the direction and timing of changes. The plotted observations are summarized separately by species.',
                      'Изменение NLR у крыс в SLS-2 даёт ориентир для сравнения направления и сроков. Полёт и синхронный контроль сопоставляются внутри вида.', "SLS-2 任务的大鼠 NLR 可用于比较变化方向与时间。飞行与同步对照数据均在同一物种内比较。")));
        const ref = node('a',tr('Paul et al. · Figure 1A','Paul et al. · рисунок 1A', "Paul 等 · 图 1A")); ref.href = 'https://doi.org/10.3389/fimmu.2020.564950'; ref.target='_blank'; ref.rel='noopener';
        evidence.append(ref);host.append(evidence);
        if (typeof ResizeObserver === 'function') {
            const observer = new ResizeObserver(draw);
            observer.observe(host);
            return () => observer.disconnect();
        }
        window.addEventListener('resize',draw);
        return () => window.removeEventListener('resize',draw);
    };
})();
