(() => {
    'use strict';
    const TRANSLATIONS = {
        ru: {
            copyright: 'Все права защищены.', cortisol: 'Кортизол', astronaut: 'Космонавт', menu: 'Меню',
            nav: ['Проблема', 'Что происходит', 'Решение', 'Демо', 'Команда'],
            heroSub: 'Астроиммунология и ИИ',
            slogan: 'Иммунные показатели до старта и во время полёта',
            exploreBtn: 'ИССЛЕДОВАТЬ МИССИЮ',
            painTag: 'Угроза',
            painTitle: 'Иммунная дисрегуляция в дальнем космосе',
            painCards: [
                'Стоимость часа работы экипажа МКС в примере коммерческих расчётов NASA за 2025 год.',
                'Доля участников исследования МКС, у которых в слюне обнаружили ДНК вируса варицелла-зостер (ВЗВ).',
                'Зарегистрированных медицинских события на один человеко-год полёта по данным обзора медкарт экипажей МКС.'
            ],
            nasaTag: 'Пробел риска NASA',
            nasaText: 'Задача NASA <strong>IM-501</strong> предусматривает проверку комплекса мер для поддержки иммунной системы в условиях космического полёта.',
            whTitle: 'Что происходит с иммунитетом в космосе?',
            whSub: 'Микрогравитация, радиация и стресс нарушают работу иммунной системы — часто еще до появления симптомов',
            whCards: [
                { title: 'Вирусы', text: 'В исследованиях экипажей МКС в полётных пробах обнаруживали ДНК герпесвирусов, в том числе ВЭБ и ВЗВ.' },
                { title: 'Воспаление', text: 'Нарастает хроническое вялотекущее воспаление — иммунная система постоянно работает в режиме тревоги, истощая ресурсы.' },
                { title: 'Нейроэндокринный стресс', text: 'Повышенный уровень кортизола и катехоламинов подавляет активность Т-клеток и нарушает циркадный иммунитет в полете.' }
            ],
            whTips: [
                { title: 'ДНК ВЭБ (EBV)', desc: 'Вирусная нагрузка Эпштейна — Барр — растет при ослаблении Т-клеточного контроля.' },
                { title: 'ИЛ-6 (IL-6)', desc: 'Ключевой провоспалительный цитокин — повышается в полете, маркер иммунного стресса.' },
                { title: 'Кортизол', desc: 'Гормон стресса — длительное повышение подавляет клеточный иммунитет.' }
            ],
            whConclusion: '<span>Последовательные замеры</span> позволяют увидеть, как меняются показатели у одного человека в ходе полёта.',
            solTitle: 'Оценка иммунных рисков до и во время полёта',
            solSub: 'Предполётная оценка использует данные физической подготовки. В полёте модель учитывает четыре системы и плановую продолжительность миссии.',
            solCards: [
                { title: 'Оценка', text: 'По данным предполётного тестирования модель оценивает риск реактивации латентных герпесвирусов в ходе миссии.' },
                { title: 'Наблюдение', text: 'В полёте можно записать три замера. Графики показывают изменения показателей и оценки модели между ними.' },
                { title: 'Интерпретация', text: 'Сводка показывает вклад показателей и доступные интервалы человеческих исследований для сравнения.' }
            ],
            metrics: [
                { val: 'Земная модель: 22 члена экипажа', desc: 'Астронавты МКС (Agha et al., 2020) | Диапазон риска: 55%–89%' },
                { val: 'Полётная модель: 4 системы', desc: 'Цитокины, лейкоциты, вирусная нагрузка и кортизол | Пороги полётной модели описаны в документации проекта.' }
            ],
            aiBoxText: 'Консультант поясняет, какие введённые показатели повлияли на результат и каковы ограничения модели.',
            tryDemoBtn: 'Открыть демо',
            demoTitle: 'Вы астронавт или мечтаете о космосе?',
            demoSub: 'Протестируйте нашу демо-модель и узнайте, как ваша иммунная система отреагирует на космический полет',
            earthLabels: ['Пол', 'VO₂max (мл/кг/мин)', 'Подтягивания (за 2 мин)', 'Отжимания (за 2 мин)'],
            genders: ['Мужской', 'Женский'],
            earthDescTitle: 'Земной предиктор',
            placeholders: {
                vo2max: 'напр. 48', pullups: 'напр. 15', pushups: 'напр. 60',
                il6_b: 'До (необязательно)', il6_a: 'После',
                nlr_b: 'До (необязательно)', nlr_a: 'После',
                ebv: 'напр. 600', cortb: 'До (необязательно)', corta: 'После', days: 'напр. 180'
            },
            consultantHint: 'ИИ-консультант: подробный разбор ниже ↓',
            pdfBtn: 'Скачать отчёт о проекте (PDF)',
            pricing: [
                {
                    title: 'Коммерческая лицензия', price: 'Индивидуально',
                    features: ['Полный доступ к био-предиктивным моделям', 'Индивидуальные профили риска экипажа', 'Персональные протоколы профилактики', 'Интеграция с дашбордами ЦУП'],
                    btn: 'Запросить B2B-расчет'
                },
                {
                    title: 'Полный доступ', price: 'Предзаказ <span>/ Стадия MVP</span>',
                    features: ['Хотите внедрить модель для вашей миссии?', 'Заинтересованы в стратегическом партнерстве?', 'Оставьте контакты для связи с командой IMMOONITY.'],
                    btn: 'Оставить контакты'
                }
            ],
            teamTitle: 'Команда IMMOONITY',
            teamSub: 'Мы объединяем медицину, иммунологию, анализ данных и бизнес-стратегию',
            teamMembers: [
                {
                    name: 'Алексей',
                    role: 'Иммунолог и<br>молекулярный биолог',
                    details: '<strong>Алексей Королёв</strong><br>Развитие партнёрств, работа с экспертами и соцсети. Связывает науку с миром.'
                },
                {
                    name: 'Лиза',
                    role: 'Экономист и аналитик данных<br>ТИМЛИД',
                    details: '<strong>Елизавета Приходько</strong><br>Построение предиктивных моделей, разработка сайта и превращение сложных данных в понятные решения.'
                },
                {
                    name: 'Игорь',
                    role: 'Медицинский специалист',
                    details: '<strong>Игорь Мизин</strong><br>Сбор и структурирование клинических данных, связь между медициной и машинным обучением.'
                },
                {
                    name: 'Святослав',
                    role: 'Ведущий разработчик',
                    details: '<strong>Святослав</strong><br>Разработка ИИ-моделей, серверной архитектуры и пайплайнов машинного обучения для оценки иммунных рисков.'
                }
            ],
            footerNote: 'Научная достоверность и будущее, основанное на данных.'
        },
        en: {
            copyright: 'All rights reserved.', cortisol: 'Cortisol', astronaut: 'Astronaut', menu: 'Menu',
            nav: ['The Pain', 'What happens', 'Solution', 'Demo', 'Team'],
            heroSub: 'Astroimmunology & AI',
            slogan: 'Track immune markers before and during spaceflight',
            exploreBtn: 'EXPLORE THE MISSION',
            painTag: 'The Threat',
            painTitle: 'Immune Dysregulation in Deep Space',
            painCards: [
                'Cost of an hour of ISS crew time in a 2025 NASA commercial cost example.',
                'Share of participants in an ISS study whose saliva contained varicella-zoster virus (VZV) DNA.',
                'Medical events recorded per crew member per flight year in a review of ISS medical records.'
            ],
            nasaTag: 'NASA Risk Gap',
            nasaText: 'NASA gap <strong>IM-501</strong> calls for flight testing of an integrated set of immune countermeasures.',
            whTitle: 'What happens to immunity in space?',
            whSub: 'Microgravity, radiation, and stress disrupt the immune system — often before symptoms appear',
            whCards: [
                { title: 'Viruses', text: 'Studies of ISS crews found herpesvirus DNA, including EBV and VZV, in samples collected during flight.' },
                { title: 'Inflammation', text: 'Chronic low‑grade inflammation rises — the immune system stays in "alert mode," draining resources.' },
                { title: 'Neuroendocrine Strain', text: 'Elevated cortisol and catecholamine levels severely suppress T-cell activity and disrupt natural circadian immunity during flight.' }
            ],
            whTips: [
                { title: 'EBV DNA', desc: 'Epstein‑Barr virus load — increases when T‑cell control weakens.' },
                { title: 'IL-6', desc: 'Key pro‑inflammatory cytokine — rises during spaceflight, linked to immune stress.' },
                { title: 'Cortisol', desc: 'Stress hormone — elevated cortisol suppresses immune function.' }
            ],
            whConclusion: '<span>Repeated measurements</span> show how an individual crew member’s markers change during flight.',
            solTitle: 'Immune risk assessment before and during flight',
            solSub: 'The pre-flight assessment uses physical fitness. The in-flight model uses four biomarker systems and the planned mission length.',
            solCards: [
                { title: 'Assessment', text: 'Pre-flight fitness measurements estimate the risk of latent herpesvirus reactivation during the mission.' },
                { title: 'Monitoring', text: 'Record up to three in-flight visits and compare measured values and model estimates over time.' },
                { title: 'Interpretation', text: 'The summary shows marker contributions and the human reference intervals available for comparison.' }
            ],
            metrics: [
                { val: 'Earth Model: 22 crew', desc: 'ISS astronauts (Agha et al., 2020) | Risk range: 55%–89%' },
                { val: 'In‑Flight Model: 4 systems', desc: 'Cytokines, leukocytes, viral load and cortisol | The project documentation describes the in-flight model thresholds.' }
            ],
            aiBoxText: 'The consultant explains which inputs contributed to the estimate and where the model’s interpretation is limited.',
            tryDemoBtn: 'Try Demo',
            demoTitle: 'Are you an astronaut or dreaming of space?',
            demoSub: 'Try our demo model and find out how your immune system will behave during spaceflight',
            earthLabels: ['Sex', 'VO₂max (ml/kg/min)', 'Pull-ups (2 min)', 'Push-ups (2 min)'],
            genders: ['Male', 'Female'],
            earthDescTitle: 'Earth Predictor',
            placeholders: {
                vo2max: 'e.g. 48', pullups: 'e.g. 15', pushups: 'e.g. 60',
                il6_b: 'Before (optional)', il6_a: 'After',
                nlr_b: 'Before (optional)', nlr_a: 'After',
                ebv: 'e.g. 600', cortb: 'Before (optional)', corta: 'After', days: 'e.g. 180'
            },
            consultantHint: 'AI consultant: see the analysis below ↓',
            pdfBtn: 'Download the project report (PDF)',
            pricing: [
                {
                    title: 'Commercial Licensing', price: 'Custom Pricing',
                    features: ['Full bio-predictive model access', 'Individual astronaut risk profiles', 'Personalized countermeasure protocols', 'Mission control dashboards & integration'],
                    btn: 'Request B2B Quote'
                },
                {
                    title: 'Get Full Access', price: 'Pre-order <span>/ MVP Phase</span>',
                    features: ['Want to deploy our model for your mission?', 'Interested in strategic collaboration?', 'Leave your contact details to connect with the IMMOONITY Operations Team.'],
                    btn: 'Leave Contact Info'
                }
            ],
            teamTitle: 'The Team Behind IMMOONITY',
            teamSub: 'We combine medicine, immunology, data science, and business strategy',
            teamMembers: [
                {
                    name: 'Alex',
                    role: 'Immunologist &<br>Molecular Biologist',
                    details: '<strong>Aleksei Korolev</strong><br>Leading expert outreach, partnerships, and social media — connecting science with the world.'
                },
                {
                    name: 'Liza',
                    role: 'Economist & Data Analyst<br>TEAM LEAD',
                    details: '<strong>Elizaveta Prikhodko</strong><br>Building predictive models, developing the website, and turning complex data into actionable insights.'
                },
                {
                    name: 'Henry',
                    role: 'Medical Specialist',
                    details: '<strong>Igor Mizin</strong><br>Collecting and structuring clinical data, bridging the gap between medicine and machine learning.'
                },
                {
                    name: 'Svyatoslav',
                    role: 'Lead Developer',
                    details: '<strong>Svyatoslav</strong><br>Developing AI models, backend architecture, and machine learning pipelines for immune risk prediction.'
                }
            ],
            footerNote: 'Scientific integrity, data-driven future.'
        },
        zh: {
            copyright: '保留所有权利。', cortisol: '皮质醇', astronaut: '航天员', menu: '菜单',
            nav: ['痛点', '太空变化', '解决方案', '模型演示', '团队'],
            heroSub: '航天免疫学与人工智能',
            slogan: '追踪飞行前与飞行期间的免疫指标',
            exploreBtn: '探索任务',
            painTag: '核心威胁',
            painTitle: '深空环境下的免疫失调',
            painCards: [
                'NASA 2025 年商业成本示例中，国际空间站乘组一小时工作时间的价格。',
                '国际空间站一项研究中，唾液检出水痘-带状疱疹病毒（VZV）DNA 的参与者比例。',
                '国际空间站乘组医疗记录回顾中，每人每飞行年的医疗事件数。'
            ],
            nasaTag: 'NASA 风险缺口',
            nasaText: 'NASA 的 <strong>IM-501</strong> 研究任务要求在太空飞行中测试综合免疫应对措施。',
            whTitle: '太空环境如何影响免疫系统？',
            whSub: '微重力、辐射和应激会在症状出现之前破坏免疫平衡',
            whCards: [
                { title: '病毒再激活', text: '国际空间站乘组的研究在飞行样本中检出了包括 EBV 和 VZV 在内的疱疹病毒 DNA。' },
                { title: '慢性炎症', text: '低度慢性炎症持续升高——免疫系统长期处于“警戒状态”，不断消耗机体储备。' },
                { title: '神经内分泌应激', text: '皮质醇与儿茶酚胺水平升高严重抑制T细胞活性，并扰乱飞行期间的昼夜节律免疫。' }
            ],
            whTips: [
                { title: 'EBV DNA', desc: 'EB病毒载量——当T细胞控制力减弱时显著上升。' },
                { title: 'IL-6', desc: '关键促炎细胞因子——太空飞行期间升高，反映免疫应激。' },
                { title: '皮质醇', desc: '应激激素——持续升高会抑制细胞免疫功能。' }
            ],
            whConclusion: '<span>连续测量</span>可以显示同一名航天员的免疫指标在飞行期间如何变化。',
            solTitle: '飞行前与飞行期间的免疫风险评估',
            solSub: '飞行前评估使用体能测试结果。飞行期间的模型使用四类生物指标和计划任务时长。',
            solCards: [
                { title: '评估', text: '根据飞行前体能测试估计任务期间潜伏疱疹病毒再激活的风险。' },
                { title: '监测', text: '最多可记录三次飞行测量，通过图表查看实测值和模型估计随时间的变化。' },
                { title: '解读', text: '综合结果显示各指标的贡献以及可供比较的人体研究参考区间。' }
            ],
            metrics: [
                { val: '地面模型：22名乘组', desc: '国际空间站宇航员数据 (Agha et al., 2020) | 风险区间：55%–89%' },
                { val: '在轨模型：4大系统', desc: '细胞因子、白细胞、病毒载量及皮质醇 | 飞行模型的阈值见项目文档。' }
            ],
            aiBoxText: '顾问解释哪些输入指标影响了本次估计，以及模型解读的局限。',
            tryDemoBtn: '体验演示',
            demoTitle: '您是宇航员，还是怀揣航天梦想？',
            demoSub: '体验我们的演示模型，了解您的免疫系统在太空飞行中的表现',
            earthLabels: ['性别', '最大摄氧量 VO₂max (ml/kg/min)', '引体向上 (2分钟)', '俯卧撑 (2分钟)'],
            genders: ['男性', '女性'],
            earthDescTitle: '地面预测器',
            placeholders: {
                vo2max: '例如 48', pullups: '例如 15', pushups: '例如 60',
                il6_b: '飞行前 (可选)', il6_a: '飞行中',
                nlr_b: '飞行前 (可选)', nlr_a: '飞行中',
                ebv: '例如 600', cortb: '飞行前 (可选)', corta: '飞行中', days: '例如 180'
            },
            consultantHint: 'AI 顾问：详细分析请见下方 ↓',
            pdfBtn: '下载项目报告（PDF）',
            pricing: [
                {
                    title: '商业授权', price: '定制报价',
                    features: ['完整生物预测模型访问权限', '宇航员个体化风险档案', '个性化防护干预方案', '任务控制中心仪表盘与系统集成'],
                    btn: '申请 B2B 报价'
                },
                {
                    title: '获取完整权限', price: '预订 <span>/ MVP 阶段</span>',
                    features: ['希望在您的任务中部署模型？', '有意开展战略合作？', '留下联系方式，与 IMMOONITY 团队取得联系。'],
                    btn: '留下联系方式'
                }
            ],
            teamTitle: 'IMMOONITY 核心团队',
            teamSub: '我们融合医学、免疫学、数据科学与商业战略',
            teamMembers: [
                {
                    name: '阿列克谢 (Alex)',
                    role: '免疫学家与<br>分子生物学家',
                    details: '<strong>阿列克谢·科罗廖夫 (Aleksei Korolev)</strong><br>负责专家对接、合作拓展与社交媒体传播，连接科学与世界。'
                },
                {
                    name: '丽莎 (Liza)',
                    role: '经济学家与数据分析师<br>团队负责人',
                    details: '<strong>伊丽莎白·普里霍季科 (Elizaveta Prikhodko)</strong><br>构建预测模型、开发网站，并将复杂数据转化为可落地的洞察。'
                },
                {
                    name: '伊戈尔 (Igor)',
                    role: '医学专家',
                    details: '<strong>伊戈尔·米津 (Igor Mizin)</strong><br>收集并整理临床数据，架起医学与机器学习之间的桥梁。'
                },
                {
                    name: '斯维亚托斯拉夫 (Svyatoslav)',
                    role: '首席开发工程师',
                    details: '<strong>斯维亚托斯拉夫 (Svyatoslav)</strong><br>开发用于免疫风险预测的 AI 模型、后端架构与机器学习流程。'
                }
            ],
            footerNote: '科学严谨，数据驱动未来。'
        }
    };


    function supported(value) {
        const primary = String(value || '').toLowerCase().split(/[-_]/)[0];
        return Object.hasOwn(TRANSLATIONS, primary) ? primary : null;
    }

    let stored;
    try { stored = localStorage.getItem('immoonity_lang'); } catch { /* Storage is optional. */ }
    let current = supported(new URLSearchParams(location.search).get('lang')) ||
        supported(stored) || supported(navigator.language) || 'ru';
    document.documentElement.lang = current;

    function applyLanguage(lang) {
        const t = TRANSLATIONS[lang];
        document.documentElement.lang = lang;
        document.querySelectorAll('.count-num').forEach(el => {
            if (el.dataset.counted) el.textContent = Number(el.dataset.target).toLocaleString(lang);
        });
        document.title = 'IMMOONITY · ' + t.heroSub;
        document.querySelectorAll('.lang-btn').forEach(button => {
            const active = button.dataset.lang === lang;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
        const copy = (selector, value, attribute) => {
            const element = document.querySelector(selector);
            if (element && attribute) element.setAttribute(attribute, value);
            else if (element) element.textContent = value;
        };
        copy('.bm-2', t.cortisol);
        copy('.team-photo', t.teamTitle, 'alt');
        copy('.astronaut-img', t.astronaut, 'alt');
        copy('.menu-toggle', t.menu, 'aria-label');

        document.querySelectorAll('.nav-links a').forEach((a, i) => { if (t.nav[i]) a.textContent = t.nav[i]; });

        const sub = document.querySelector('.hero-subtitle');
        if (sub) sub.textContent = t.heroSub;
        const exp = document.getElementById('explore-btn');
        if (exp) exp.textContent = t.exploreBtn;

        const pTag = document.querySelector('#pain .section-tag');
        if (pTag) pTag.textContent = t.painTag;
        const pTitle = document.querySelector('#pain .section-title');
        if (pTitle) pTitle.textContent = t.painTitle;
        document.querySelectorAll('#pain .counter-desc').forEach((el, i) => { if (t.painCards[i]) el.textContent = t.painCards[i]; });
        const nTag = document.querySelector('.nasa-tag');
        if (nTag) nTag.textContent = t.nasaTag;
        const nText = document.querySelector('.nasa-text');
        if (nText) nText.innerHTML = t.nasaText;

        const whTitle = document.querySelector('.wh-title');
        if (whTitle) whTitle.textContent = t.whTitle;
        const whSub = document.querySelector('.wh-subtitle');
        if (whSub) whSub.textContent = t.whSub;
        document.querySelectorAll('.wh-card').forEach((card, i) => {
            if (t.whCards[i]) {
                card.querySelector('.wh-card-title').textContent = t.whCards[i].title;
                card.querySelector('.wh-card-text').textContent = t.whCards[i].text;
            }
        });
        document.querySelectorAll('.wh-tooltip').forEach((tip, i) => {
            if (t.whTips[i]) {
                tip.querySelector('.wh-tooltip-title').textContent = t.whTips[i].title;
                tip.querySelector('.wh-tooltip-desc').textContent = t.whTips[i].desc;
            }
        });
        const whConcl = document.querySelector('.wh-conclusion-text');
        if (whConcl) whConcl.innerHTML = t.whConclusion;

        const solTitle = document.querySelector('.sol-title');
        if (solTitle) solTitle.textContent = t.solTitle;
        const solSub = document.querySelector('.sol-subtitle');
        if (solSub) solSub.textContent = t.solSub;
        document.querySelectorAll('.sol-card').forEach((card, i) => {
            if (t.solCards[i]) {
                card.querySelector('h3').textContent = t.solCards[i].title;
                card.querySelector('p').textContent = t.solCards[i].text;
            }
        });
        document.querySelectorAll('.metric-item').forEach((m, i) => {
            if (t.metrics[i]) {
                m.querySelector('.metric-val').textContent = t.metrics[i].val;
                m.querySelector('p').textContent = t.metrics[i].desc;
            }
        });
        const aiP = document.querySelector('.ai-box p');
        if (aiP) aiP.textContent = t.aiBoxText;
        const btnDemo = document.querySelector('.btn-demo');
        if (btnDemo) btnDemo.textContent = t.tryDemoBtn;

        const dTitle = document.querySelector('.demo-main-title');
        if (dTitle) dTitle.textContent = t.demoTitle;
        const dSub = document.querySelector('.demo-subtitle');
        if (dSub) dSub.textContent = t.demoSub;

        document.querySelectorAll('.pricing-card').forEach((card, i) => {
            if (t.pricing[i]) {
                card.querySelector('.pr-title').textContent = t.pricing[i].title;
                card.querySelector('.pr-price').innerHTML = t.pricing[i].price;
                card.querySelectorAll('.pr-features li').forEach((li, j) => {
                    if (t.pricing[i].features[j]) li.textContent = t.pricing[i].features[j];
                });
                card.querySelector('.pr-btn').textContent = t.pricing[i].btn;
            }
        });

        const teamTitle = document.querySelector('.team-title');
        if (teamTitle) teamTitle.textContent = t.teamTitle;
        const teamSub = document.querySelector('.team-desc');
        if (teamSub) teamSub.textContent = t.teamSub;
        document.querySelectorAll('#team .member-box').forEach((box, i) => {
            const m = t.teamMembers && t.teamMembers[i];
            if (!m) return;
            const nameEl = box.querySelector('.member-name');
            const roleEl = box.querySelector('.member-role');
            const detailsEl = box.querySelector('.details');
            if (nameEl) nameEl.textContent = m.name;
            if (roleEl) roleEl.innerHTML = m.role;
            if (detailsEl) detailsEl.innerHTML = m.details;
        });

        const fPs = document.querySelectorAll('footer p');
        if (fPs[0]) fPs[0].textContent = '© 2026 IMMOONITY. ' + t.copyright;
        if (fPs[1]) fPs[1].textContent = t.footerNote;
    }


    function change(lang) {
        if (!supported(lang) || current === lang) return;
        current = lang;
        try { localStorage.setItem('immoonity_lang', lang); } catch { /* Browsing without storage. */ }
        const url = new URL(location.href);
        url.searchParams.set('lang', lang);
        history.replaceState(history.state, '', url);
        applyLanguage(lang);
        document.dispatchEvent(new CustomEvent('site-language', {detail: lang}));
    }
    window.siteCopy = () => TRANSLATIONS[current];
    document.addEventListener('DOMContentLoaded', () => {
        applyLanguage(current);
        document.querySelector('.lang-switcher').addEventListener('click', e => {
            const button = e.target.closest('[data-lang]');
            if (button) change(button.dataset.lang);
        });
    });
})();
