/* One Earth assessment and up to three visits in the same mission. All predictions use /predict. */
window.initMissionSeries = function (options) {
    'use strict';
    const {lang, labels, resolveApiBase, renderRisk, renderConsultant, showMessage, request = window.fetch.bind(window)} = options;
    const tr = (en, ru, zh) => lang === 'zh' ? zh : lang === 'ru' ? ru : en;
    const root = document.querySelector('#demo .demo-card');
    const nav = root.querySelector('#mission-nav'), summary = root.querySelector('#mission-summary');
    const message = root.querySelector('#series-message'), footer = root.querySelector('.series-footer');
    const dialog = root.querySelector('#mission-loading');
    const first = root.querySelector('#flight-form'), earth = root.querySelector('#earth-form');
    const originalFlight = first.cloneNode(true);
    const downloads = new Map();
    const forms = [earth, first];
    const beforeAfter = {il6_b:'il6_a', nlr_b:'nlr_a', cortb:'corta'};
    const visitName = i => i ? tr('In-Flight ', 'В полёте ', "飞行测量 ") + i : tr('Earth Model', 'До полёта', "地面模型");
    const api = new URLSearchParams(location.search).get('api') || 'default';
    const key = 'immoonity.series.v2/' + location.pathname + '/' + api;
    const legacyKey = code => 'immoonity.series.v1/' + location.pathname + '/' + code + '/' + api;
    const empty = () => ({schema:1, opened:1, slots:[null,null,null,null], scenario:'space', unread:false});
    let state = empty(), selected = 0, busy = null, closeChart = null, storageOK = true;
    const node = (tag, cls, text) => {
        const e = document.createElement(tag);
        if (cls) e.className = cls;
        if (text != null) e.textContent = text;
        return e;
    };
    const field = (form, name) => form.querySelector('[data-field="' + name + '"]');
    const ready = i => Boolean(state.slots[i]?.result);
    function complete() {
        let i = 0;
        while (i < 4 && ready(i)) i++;
        return i;
    }
    function validResult(value, model) {
        if (value?.model !== model || !Number.isFinite(value.risk) || value.risk < 0 || value.risk > 100
                || !Number.isFinite(value.risk_interval?.low) || !Number.isFinite(value.risk_interval?.high)
                || !value.level || !value.interpretation?.level || !value.inputs || !Array.isArray(value.factors)) return false;
        const required = model === 'earth' ? ['vo2max','pullups','pushups'] : ['il6_a','nlr_a','ebv','corta','days'];
        return required.every(k => Number.isFinite(value.inputs[k]));
    }
    function read() {
        if (options.previous) { state = options.previous.state; return; }
        let raw;
        try {
            raw = sessionStorage.getItem(key);
            for (const language of [lang, 'en', 'ru']) {
                if (!raw) raw = sessionStorage.getItem(legacyKey(language));
            }
        }
        catch (_) { storageOK = false; return; }
        if (!raw) return;
        try {
            const data = JSON.parse(raw);
            if (data?.schema !== 1 || !Number.isInteger(data.opened) || data.opened < 1 || data.opened > 3
                    || !Array.isArray(data.slots) || data.slots.length !== 4
                    || !['space','checkup','extreme'].includes(data.scenario)) throw Error();
            data.slots.forEach((s, i) => {
                if (!s) return;
                if (i > data.opened || !s.values || (s.day != null && (!Number.isInteger(s.day) || s.day < 1))
                        || (s.result && !validResult(s.result, i === 0 ? 'earth' : 'flight'))) throw Error();
                if (i > 1 && s.result && !data.slots[i - 1]?.result) throw Error();
            });
            state = data;
        } catch (_) {
            message.textContent = tr('The saved series could not be read. Start a new measurement.',
                'Сохранённая серия не читается. Можно начать новый замер.', "无法读取已保存的记录。请开始新的测量。");
        }
    }
    function save() {
        try { sessionStorage.setItem(key, JSON.stringify(state)); }
        catch (_) { storageOK = false; }
        footer.querySelector('#series-storage-note').textContent = storageOK ?
            tr('This series is saved in this browser tab.', 'Серия сохраняется в этой вкладке браузера.', "此系列已保存在当前浏览器标签页中。") :
            tr('Browser storage is unavailable. This series lasts until the page reloads.', 'Хранилище недоступно. Серия доступна до перезагрузки страницы.', "浏览器存储不可用。刷新页面后将清除本系列。");
    }

    function moons(container, pending = -1) {
        container.replaceChildren();
        const count = complete();
        for (let i = 0; i < 4; i++) {
            const cell = node('span','moon-cell');
            cell.classList.toggle('moon-done', i < count);
            cell.classList.toggle('moon-linked', i + 1 < count);
            cell.classList.toggle('moon-pending', i === pending);
            cell.append(node('span','moon-disc'));
            container.append(cell);
        }
    }

    function updateNavigation() {
        nav.replaceChildren();
        nav.setAttribute('aria-label', tr('Measurement series','Серия замеров', "测量系列"));
        const track = node('div','mission-track');
        track.setAttribute('role','img');
        track.setAttribute('aria-label', tr('Completed steps: ', 'Завершено шагов: ', "已完成步骤：") + complete() + '/4');
        moons(track); nav.append(track);
        function control(id, text, handler, column, extraClass) {
            const btn = node('button','tab-btn ' + (extraClass || ''),text);
            btn.type = 'button'; btn.id = id; btn.style.setProperty('--nav-column',column);
            btn.addEventListener('click',handler); nav.append(btn);
            return btn;
        }
        if (complete() >= 2) {
            const btn = control('summary-tab', tr('Integrated result','Сводный результат', "综合结果"), () => show('summary'), 1,'summary-tab');
            btn.classList.toggle('unread', state.unread && selected !== 'summary');
            btn.classList.toggle('active',selected === 'summary');
            btn.setAttribute('aria-controls',summary.id); btn.setAttribute('aria-pressed',String(selected === 'summary'));
        }
        forms.forEach((f, i) => {
            const btn = control('visit-tab-' + i, visitName(i), () => show(i), i + 2);
            btn.setAttribute('aria-pressed',String(selected === i));
            btn.classList.toggle('active', selected === i); btn.setAttribute('aria-controls', f.id);
        });
        if (state.opened < 3) {
            const add = control('series-add', tr('+ Add measurement','+ Добавить замер', "+ 添加测量"), () => {
                if (complete() !== state.opened + 1 || state.opened >= 3) return;
                state.opened++; makeFlight(state.opened); save(); show(state.opened);
            }, state.opened + 3,'add-tab');
            add.disabled = complete() !== state.opened + 1;
            if (add.disabled) add.title = tr('Complete the preceding steps first.', 'Сначала рассчитайте предыдущие шаги.', "请先完成前面的步骤。");
        }
        footer.hidden = !state.slots.some(Boolean) && state.opened === 1;
    }

    function show(step, moveFocus = true) {
        if (busy) return;
        if (step === 'summary' && complete() < 2) return;
        selected = step;
        forms.forEach((form, i) => { form.classList.toggle('active', step === i); });
        if (closeChart) { closeChart(); closeChart = null; }
        summary.hidden = step !== 'summary';
        if (!summary.hidden) {
            state.unread = false;
            const records = state.slots.slice(0, complete()).map(slot => ({...slot, result: localized(slot.result)}));
            closeChart = window.renderMissionSummary(summary, records, lang, state.scenario, v => {
                state.scenario = v; save();
            });
            save();
        }
        updateNavigation();
        if (moveFocus) nav.querySelector(step === 'summary' ? '#summary-tab' : '#visit-tab-' + step)?.focus({preventScroll:true});
    }

    function clearCard(form) {
        form.querySelector('.result-display').style.display = 'none';
        form.querySelector('.consultant-panel').hidden = true;
        form.querySelector('.form-message').hidden = true;
    }
    function localized(result) {
        if (result.interpretation.language === lang) return result;
        if (result.translations?.[lang]) return {...result, ...result.translations[lang]};
        const outcome = result.model === 'earth'
            ? tr('Herpesvirus reactivation during the mission', 'Реактивация герпесвирусов в ходе миссии', '任务期间疱疹病毒再激活')
            : tr('Multi-system immune dysregulation by the end of the mission', 'Многосистемная иммунная дисрегуляция к концу миссии', '任务结束前的多系统免疫失调');
        return {...result, interpretation: {outcome, level: {label: ''}}, input_warnings: []};
    }
    function drawCard(form, stored) {
        const result = localized(stored);
        clearCard(form);
        renderRisk(form,result);
        if (result.interpretation.headline) {
            renderConsultant(form.querySelector('.consultant-panel'), result.model, result.interpretation);
        } else {
            showMessage(form, tr('Recalculate to read the analysis in this language.', 'Пересчитайте замер, чтобы прочитать разбор на этом языке.', '请重新计算以查看此语言的分析。'), [], 'warn');
        }
        const box = form.querySelector('.result-display');
        box.querySelector('.series-endpoint')?.remove();
        box.querySelector('.series-baseline-note')?.remove();
        let note = result.interpretation.baseline_note;
        if (result.model === 'flight' && note === undefined &&
            Object.keys(beforeAfter).some(field => !(result.inputs[field] > 0))) {
            note = tr('Markers without a positive pre-flight sample were assessed using current levels and absolute thresholds.',
                'Если положительной предполётной пробы нет, маркер оценён по текущему значению и абсолютному порогу.',
                '缺少正值飞行前基线的指标，按本次测量值和绝对阈值评估。');
        }
        if (note) {
            box.querySelector('.consultant-hint').before(node('p', 'series-baseline-note', note));
        }
        const record = state.slots[Number(form.dataset.step)];
        box.append(window.renderVisitEvidence(result, record?.day, lang));
        if (result.input_warnings?.length) showMessage(form,labels.check,result.input_warnings,'warn');
    }
    function newInput(box, id, labelText, placeholder) {
        const label = node('label',null,labelText); label.htmlFor = id;
        const input = node('input'); input.id = id; input.type='number'; input.step='any'; input.min='0';
        if (placeholder) input.placeholder = placeholder;
        box.append(label, input);
        return input;
    }

    // Count entry is an optional alternate representation of a measured human NLR.
    function addCounts(form, i) {
        const current = field(form,'nlr_a'), box = current.closest('.input-box');
        const toggle = node('input'); toggle.type='checkbox'; toggle.className='counts-toggle';
        const label = node('label','series-counts-toggle'); label.append(toggle, document.createTextNode(
            tr('Use absolute cell counts', 'Ввести абсолютные нейтрофилы и лимфоциты', "使用绝对细胞计数")));
        const section = node('div','series-counts'); section.hidden = true;
        const a = newInput(section,'anc-visit-'+i, tr('Neutrophils (10⁹/L)','Нейтрофилы (10⁹/л)', "中性粒细胞（10⁹/L）"));
        const b = newInput(section,'alc-visit-'+i, tr('Lymphocytes, same sample (10⁹/L)','Лимфоциты из той же пробы (10⁹/л)', "同一样本的淋巴细胞（10⁹/L）"));
        a.dataset.count='anc'; b.dataset.count='alc'; box.append(label,section);
        function convert() {
            const n=a.valueAsNumber, d=b.valueAsNumber;
            current.value = Number.isFinite(n) && n >= 0 && Number.isFinite(d) && d > 0 ? String(n/d) : '';
        }
        toggle.addEventListener('change',() => {
            if (toggle.checked) toggle.dataset.manual = current.value;
            section.hidden = !toggle.checked; current.readOnly = toggle.checked;
            if (toggle.checked) convert(); else current.value=toggle.dataset.manual || '';
            current.dispatchEvent(new Event('input', {bubbles: true}));
        });
        section.addEventListener('input',convert);
        return (counts) => {
            if (!counts) return;
            toggle.checked=true; section.hidden=false; current.readOnly=true;
            toggle.dataset.manual=current.value; a.value=counts.anc; b.value=counts.alc; convert();
        };
    }

    function setup(form, i) {
        const saved = state.slots[i];
        form.dataset.step = i;
        form.querySelectorAll('input[id]').forEach(input => {
            const name = input.id;
            const label = form.querySelector('label[for="' + name + '"]');
            input.dataset.field = name;
            if (options.copy.placeholders[name]) input.placeholder = options.copy.placeholders[name];
            if (i > 1) { input.id = name+'-visit-'+i; if (label) label.htmlFor=input.id; }
            if (saved?.values[name] != null) input.value = saved.values[name];
            if (input.type === 'number') input.min = '0';
        });
        const btn = form.querySelector('.calc-btn');
        btn.textContent = labels.calc[i === 0 ? 'earth-form' : 'flight-form'];
        const h = form.querySelector('.desc h3');
        form.querySelector('.consultant-hint').textContent = tr('Consultant analysis below ↓','Разбор консультанта ниже ↓', "查看下方的顾问分析 ↓");
        const caption = form.querySelector('.desc > p');
        const download = form.querySelector('.pdf-download-btn');
        download.lastChild.textContent = ' ' + options.copy.pdfBtn;
        download.addEventListener('click', () => downloadReport(form, i, download));
        if (i === 0) {
            h.textContent = options.copy.earthDescTitle;
            caption.textContent = tr('Estimated risk of herpesvirus reactivation during the mission, based on pre-flight fitness.', 'Оценка риска реактивации герпесвирусов в ходе миссии по физической подготовке перед полётом.', '根据飞行前体能估计任务期间疱疹病毒再激活的风险。');
            form.querySelector('.gender-selector').previousElementSibling.textContent = options.copy.earthLabels[0];
            ['vo2max', 'pullups', 'pushups'].forEach((id, j) => {
                form.querySelector('label[for="' + id + '"]').textContent = options.copy.earthLabels[j + 1];
            });
            const sex = field(form,'sex').value;
            form.querySelectorAll('.gender-btn').forEach((b,j) => {
                b.textContent = options.copy.genders[j];
                b.classList.toggle('active', sex === (j?'F':'M'));
                b.addEventListener('click',() => { field(form,'sex').dispatchEvent(new Event('input',{bubbles:true})); });
            });
        } else {
            h.textContent=visitName(i);
            if (i > 1) form.querySelector('.result-display').id='result-flight-'+i;
            caption.textContent = i === 1 ?
                tr('Enter the pre-flight sample if available and the current in-flight measurements. The model uses the planned mission length.', 'Укажите предполётную пробу, если она есть, и текущий замер в полёте. Для расчёта используется плановая длительность миссии.', "请输入本次飞行测量值。如有飞行前的样本，也可一并输入。模型使用计划任务时长。") :
                tr('Compare current values with the previous visit. Risk uses the original pre-flight baseline and the same planned mission length.', 'Сравните текущую пробу с предыдущим замером. Для оценки риска сохраняются исходная предполётная проба и тот же плановый срок миссии.', "本次测量与上次对照。风险计算使用首次输入的飞行前基线和计划任务时长。");
            for (const [before, after] of Object.entries(beforeAfter)) {
                const a=field(form,before), b=field(form,after);
                const name = before==='il6_b' ? 'IL-6 ('+tr('pg/mL','пг/мл', "pg/mL")+')' : before==='cortb' ? tr('Cortisol (nmol/L)','Кортизол (нмоль/л)', "皮质醇（nmol/L）") : 'NLR';
                const pre=i===1 ? tr('Pre-flight (optional)','До полёта (необязательно)', "飞行前（可选）") : tr('Previous visit','Предыдущая проба', "上次测量");
                const current=tr('Current sample','Текущая проба', "本次样本");
                a.closest('.input-box').querySelector('label').textContent=name+' · '+pre+' / '+current;
                a.placeholder=pre; b.placeholder=current; a.readOnly=i>1;
                a.setAttribute('aria-label',name+' · '+pre); b.setAttribute('aria-label',name+' · '+current);
            }
            field(form,'ebv').closest('.input-box').querySelector('label').textContent=tr('EBV DNA in saliva (copies/mL)','ДНК ВЭБ в слюне (копий/мл)', "唾液中的 EBV DNA（拷贝/mL）");
            const horizon=field(form,'days');
            horizon.closest('.input-box').querySelector('label').textContent=tr('Planned mission length (days)','Плановая длительность миссии (сутки)', "计划任务时长（天）");
            horizon.readOnly=i>1;
            const dateBox=node('div','input-box'), date=newInput(dateBox,'visit-day-'+i,tr('Flight day of this sample','День полёта при взятии этой пробы', "本次采样的飞行日"));
            date.step='1'; date.min='1'; date.required=true; date.dataset.visitDay=''; date.value=saved?.day ?? '';
            form.querySelector('.inputs').append(dateBox);
            const restoreCounts=addCounts(form,i); restoreCounts(saved?.counts);
        }
        form.addEventListener('input', e => {
            downloads.get(i)?.abort();
            form.dataset.dirty = 'true';
            e.target.classList.remove('input-error');
            if (state.slots[i]?.result) {
                clearCard(form);
                showMessage(form,tr('Changes are pending. The summary uses your last calculation.',
                    'Есть изменения. В сводке пока показан последний сохранённый расчёт.', "修改尚未计算。综合结果仍显示上次计算的数值。"),[],'warn');
            }
        });
        form.addEventListener('submit', e => { e.preventDefault(); calculate(i); });
        if (saved?.result) drawCard(form,saved.result);
        else if (saved) showMessage(form,tr('Recalculate after updating the preceding visit.', 'Пересчитайте после изменения предыдущей пробы.', "请在更新上次测量后重新计算。"),[],'warn');
    }

    function makeFlight(i) {
        const form = originalFlight.cloneNode(true);
        form.id='flight-'+i+'-form'; summary.before(form); forms[i]=form; setup(form,i); sync(i);
    }
    function sync(i) {
        if (i<2) return;
        const form=forms[i], prev=state.slots[i-1]?.result?.inputs, firstInputs=state.slots[1]?.result?.inputs;
        for (const [before,after] of Object.entries(beforeAfter)) field(form,before).value=prev?.[after] ?? '';
        field(form,'days').value=firstInputs?.days ?? '';
        form.querySelector('.calc-btn').disabled = !prev;
    }

    function commit(i, body, day, counts) {
        delete forms[i].dataset.dirty;
        const old=state.slots[i];
        const values = {...body.inputs};
        for (const marker of body.series_assessment?.markers || []) {
            if (typeof marker.value === 'string') values[marker.field] = marker.value;
        }
        const equal=old?.result && old.day===day && old.result.model_version===body.model_version &&
            old.result.series_assessment?.registry_version===body.series_assessment?.registry_version &&
            Object.keys({...old.values,...values}).every(key=>old.values[key]===values[key]);
        state.slots[i]={result:body,values,day,counts};
        if (i>0 && !equal) {
            for (let later=i+1; later<=state.opened; later++) {
                if (!state.slots[later]) continue;
                state.slots[later].result=null;
                clearCard(forms[later]);
                showMessage(forms[later],tr('The previous measurement changed. Review and recalculate.',
                    'Предыдущий замер изменился. Проверьте значения и пересчитайте.', "上次测量已更改。请核对并重新计算。"),[],'warn');
            }
        }
        for (let k=2;k<=state.opened;k++) sync(k);
        if (!equal && complete()>=2) state.unread=true;
        drawCard(forms[i],body); save(); updateNavigation();
    }

    function startLoading(i, controller) {
        busy=controller;
        const title=dialog.querySelector('h3'); title.textContent=labels.processing;
        dialog.querySelector('.loading-step').textContent=visitName(i);
        dialog.querySelector('.series-cancel').textContent=tr('Cancel','Отменить', "取消");
        moons(dialog.querySelector('.loading-moons'),i);
        if (typeof dialog.showModal==='function') dialog.showModal(); else dialog.setAttribute('open','');
    }
    function finishAnimation(start, signal) {
        const remaining = 2700 - (performance.now() - start);
        if (remaining <= 0 || signal.aborted) return Promise.resolve();
        return new Promise(resolve => {
            const finish = () => {
                clearTimeout(timer);
                signal.removeEventListener('abort', finish);
                resolve();
            };
            const timer = setTimeout(finish, remaining);
            signal.addEventListener('abort', finish, {once: true});
        });
    }
    function cancel() { if (busy) busy.abort(); }
    dialog.addEventListener('cancel',e=>{e.preventDefault();cancel();});
    dialog.querySelector('.series-cancel').addEventListener('click',cancel);

    async function calculate(i) {
        if (busy) return;
        const form=forms[i], btn=form.querySelector('.calc-btn');
        if (i>1 && !ready(i-1)) return;
        form.querySelector('.form-message').hidden=true;
        form.querySelectorAll('.input-error').forEach(el=>el.classList.remove('input-error'));
        const data={model:i?'flight':'earth',lang}, missing=[];
        form.querySelectorAll('[data-field]').forEach(input=>{
            if (input.value !== '') data[input.dataset.field]=input.value;
            else if (input.hasAttribute('data-required')) missing.push(input);
        });
        let counts=null;
        if (form.querySelector('.counts-toggle')?.checked) {
            const a=form.querySelector('[data-count="anc"]'), b=form.querySelector('[data-count="alc"]');
            const bad=[a,b].filter(input => !Number.isFinite(input.valueAsNumber) || (input===b?input.valueAsNumber<=0:input.valueAsNumber<0));
            if (bad.length) {
                bad.forEach(v=>v.classList.add('input-error')); bad[0].focus();
                showMessage(form,tr('Enter counts from one sample. Lymphocytes must be greater than zero.', 'Введите концентрации из одной пробы. Количество лимфоцитов должно быть больше нуля.', "请输入同一样本的细胞计数。淋巴细胞数必须大于零。")); return;
            }
            counts={anc:a.valueAsNumber,alc:b.valueAsNumber};
        }
        if (missing.length) {
            missing.forEach(v=>v.classList.add('input-error')); showMessage(form,labels.required); missing[0].focus(); return;
        }
        const date=form.querySelector('[data-visit-day]');
        const day=date?.value ? date.valueAsNumber : null;
        if (date && (date.validity.badInput || !Number.isSafeInteger(day) || day<1
                || state.slots.slice(1,i).some(s=>s?.day!=null && day<=s.day))) {
            date.classList.add('input-error'); date.focus();
            showMessage(form,tr('Enter a positive whole flight day after the preceding sample.', 'Укажите целый положительный день полёта после предыдущей пробы.', "请输入晚于上次采样日的正整数飞行日。")); return;
        }
        data.series_visit = i ? {day} : {};
        data.include_translations = true;
        // The form shows the previous visit for adjacent changes. The established model defines
        // its three optional _before fields as PRE-FLIGHT, so every risk request uses visit 1's baseline.
        if (i>1) {
            const original=state.slots[1].values;
            for (const before of Object.keys(beforeAfter)) {
                delete data[before];
                if (original[before]!=null) data[before]=original[before];
            }
            data.days=original.days;
        }
        const controller=new AbortController(); let timedOut=false, focusAfter=null;
        startLoading(i,controller); btn.disabled=true; btn.textContent=labels.processing;
        const shownAt = performance.now();
        const slow=setTimeout(()=>{dialog.querySelector('h3').textContent=labels.waking;},4000);
        const timeout=setTimeout(()=>{timedOut=true;controller.abort();},90000);
        try {
            const base=await resolveApiBase();
            const response=await request(base+'/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),signal:controller.signal});
            const body=await response.json();
            await finishAnimation(shownAt, controller.signal);
            controller.signal.throwIfAborted();
            if (!response.ok || !validResult(body,data.model)) {
                const details=Array.isArray(body?.details)?body.details:[];
                for (const d of details) {
                    const input=Array.from(form.querySelectorAll('[data-field]')).find(el=>el.dataset.field===d.field);
                    if (input) {input.classList.add('input-error'); focusAfter ??=input;}
                }
                showMessage(form,body?.message||labels.network,details); return;
            }
            if (i>1 && state.slots[1].result.model_version!==body.model_version) {
                showMessage(form,tr('The model version changed. Recalculate the first flight visit.', 'Версия модели изменилась. Пересчитайте первый полётный замер.', "模型版本已更新。请重新计算首次飞行测量。")); return;
            }
            commit(i,body,day,counts);
        } catch (_) {
            await finishAnimation(shownAt, controller.signal);
            if (timedOut || !controller.signal.aborted) showMessage(form,labels.network);
            else showMessage(form,tr('Calculation cancelled.','Расчёт отменён.', "已取消计算。"),[],'warn');
        } finally {
            clearTimeout(slow);clearTimeout(timeout);busy=null;
            if (dialog.open) {if (typeof dialog.close==='function') dialog.close(); else dialog.removeAttribute('open');}
            btn.disabled=false;btn.textContent=labels.calc[i===0?'earth-form':'flight-form'];
            if (focusAfter) focusAfter.focus();
        }
    }

    async function downloadReport(form, i, button) {
        const slot = state.slots[i];
        if (!slot?.result || form.dataset.dirty || downloads.has(i)) return;
        const controller = new AbortController();
        downloads.set(i, controller);
        button.disabled = true;
        button.setAttribute('aria-busy', 'true');
        const payload = {...slot.values, model: i ? 'flight' : 'earth', lang,
            expected_model_version: slot.result.model_version};
        if (i === 0 || Number.isInteger(slot.day)) payload.series_visit = i ? {day: slot.day} : {};
        if (slot.counts) payload.cell_counts = slot.counts;
        let timedOut = false;
        const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, 90000);
        try {
            const base = await resolveApiBase();
            const response = await request(base + '/api/report.pdf', {method: 'POST',
                headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload), signal: controller.signal});
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw Error(error.message || labels.network);
            }
            if (!response.headers.get('Content-Type')?.startsWith('application/pdf')) throw Error(labels.network);
            const blob = await response.blob();
            if (controller.signal.aborted || !form.isConnected || form.dataset.dirty || !slot.result || state.slots[i] !== slot) return;
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'IMMOONITY-' + (i ? 'F' + i + (slot.day ? '-day-' + slot.day : '') : 'Earth') + '-' + lang + '.pdf';
            document.body.append(link); link.click(); link.remove();
            setTimeout(() => URL.revokeObjectURL(url), 15000);
        } catch (error) {
            if (!controller.signal.aborted || timedOut) showMessage(form, timedOut ? labels.network : error.message || labels.network);
        } finally {
            clearTimeout(timeout);
            downloads.delete(i);
            button.disabled = false;
            button.removeAttribute('aria-busy');
        }
    }

    read(); setup(earth,0); setup(first,1);
    for (let i=2;i<=state.opened;i++) makeFlight(i);
    footer.querySelector('#series-reset').textContent=tr('Start a new series','Начать новую серию', "开始新的测量系列");
    footer.querySelector('#series-reset').addEventListener('click',()=>{
        if (busy || !window.confirm(tr('Clear the measurements in this tab and start a new series?', 'Очистить замеры этой вкладки и начать новую серию?', "清除本标签页中的测量并开始新系列？"))) return;
        try { sessionStorage.setItem(key, JSON.stringify(empty())); } catch (_) {}
        location.reload();
    });
    function takeSnapshot() {
        downloads.forEach(controller => controller.abort());
        if (busy) busy.abort();
        if (closeChart) closeChart();
        const drafts = forms.map(form => {
            const values = Object.fromEntries([...form.querySelectorAll('[data-field]')].map(input => [input.dataset.field, input.value]));
            const counts = form.querySelector('.counts-toggle');
            return {values, day: form.querySelector('[data-visit-day]')?.value, dirty: Boolean(form.dataset.dirty),
                counts: counts && {enabled: counts.checked, manual: counts.dataset.manual,
                    anc: form.querySelector('[data-count="anc"]').value, alc: form.querySelector('[data-count="alc"]').value}};
        });
        return {state, selected, drafts, marker: summary.querySelector('#series-marker')?.value};
    }
    if (options.previous) {
        options.previous.drafts.forEach((draft, i) => {
            const form = forms[i];
            for (const [name, value] of Object.entries(draft.values)) field(form, name).value = value;
            if (i === 0) {
                form.querySelectorAll('.gender-btn').forEach((button, j) => button.classList.toggle('active', draft.values.sex === (j ? 'F' : 'M')));
            } else {
                form.querySelector('[data-visit-day]').value = draft.day;
                const toggle = form.querySelector('.counts-toggle');
                toggle.checked = draft.counts.enabled;
                toggle.dataset.manual = draft.counts.manual ?? '';
                form.querySelector('.series-counts').hidden = !toggle.checked;
                field(form, 'nlr_a').readOnly = toggle.checked;
                for (const name of ['anc', 'alc']) form.querySelector('[data-count="' + name + '"]').value = draft.counts[name];
            }
            if (draft.dirty) field(form, i ? 'il6_a' : 'vo2max').dispatchEvent(new Event('input', {bubbles: true}));
        });
    }
    save();
    show(options.previous?.selected ?? 0, false);
    const marker = summary.querySelector('#series-marker');
    if (marker && options.previous?.marker) { marker.value = options.previous.marker; marker.onchange(); }
    return {takeSnapshot};
};
