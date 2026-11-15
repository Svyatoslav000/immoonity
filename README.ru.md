# IMMOONITY

[English](README.md) | Русский

**Сайт:** https://immoonity.onrender.com · **Презентация (7 слайдов, англ.):** [docs/IMMOONITY_demo.pdf](docs/IMMOONITY_demo.pdf)

Оценка иммунного риска в космическом полёте: сайт с демо и API двух моделей — предполётной
(физическая подготовка) и полётной (биомаркеры).

| Папка / файл | Что это |
|---|---|
| `immoonity-site/` | сайт (одна страница, блок Demo обращается к API) |
| `immoonity-app/` | API, модели, обучение, данные, тесты |
| `wsgi.py`, `gunicorn.conf.py` | сайт и API одним сервисом |
| `render.yaml`, `amvera.yml`, `Dockerfile`, `Procfile`, `.python-version` | деплой |
| `MODEL.md` | обоснование моделей и источники (на английском) |
| `CHANGES.md` | список изменений (на английском) |

## Запуск в PyCharm

1. **File → Open** → папка `immoonity`.
2. Интерпретатор: **Add Interpreter → Virtualenv**, Python 3.13 (подойдёт 3.10+). На предложение установить
   зависимости из `requirements-dev.txt` — согласиться (или в терминале `pip install -r requirements-dev.txt`).
3. Конфигурация **1. Site + API** → **Run**. Откроется http://localhost:8000/#demo

| Конфигурация | Что делает |
|---|---|
| 1. Site + API | сайт с демо и API на порту 8000 |
| 2. Site + API (Russian consultant) | то же, интерпретация на русском |
| 3. API only (app.py) | API на порту 5000 |
| 4. Tests (pytest) | тесты API и моделей |
| 5. Retrain models | пересчёт `models/*.json` после правок в `training/config.py` |

Без PyCharm: `pip install -r requirements-dev.txt`, затем `python run_local.py`.

## Репозиторий

```bash
git clone https://github.com/Svyatoslav000/immoonity.git
```

GitHub Actions на каждый push запускает тесты и проверяет запуск сервера (`.github/workflows/tests.yml`).

## Деплой

### Render (бесплатно)

1. render.com → **New → Blueprint** → выбрать репозиторий → **Apply**.
2. Всё берётся из `render.yaml`: Python из `.python-version`, сборка `pip install -r requirements.txt`,
   запуск `gunicorn wsgi:app`, проверка `/api/health`, регион Frankfurt.
3. Через несколько минут сайт открывается по адресу `https://immoonity.onrender.com`
   (если имя занято — с суффиксом). Каждый push в `main` обновляет сайт.

Бесплатный сервис засыпает после 15 минут без запросов; первое открытие после паузы — до минуты.
Чтобы не засыпал — тариф Starter.

### Россия: Amvera (без VPN)

Render работает через Cloudflare, который в России замедляют. Amvera — российская площадка того же типа:
собирает `Dockerfile` из репозитория, настройки в `amvera.yml` (порт 8000).

1. amvera.ru → регистрация (при регистрации даётся стартовый баланс) → **Создать приложение**.
2. Источник — этот репозиторий GitHub, ветка `main`; тариф — любой, хватит самого маленького.
3. После сборки во вкладке **Домены** включить бесплатный домен — по нему открываются сайт и демо.
4. Push в `main` обновляет приложение (если автообновление не включилось — кнопка **Пересобрать**).

Сайт не обращается к внешним CDN: шрифты и GSAP лежат в `immoonity-site/vendor/`.

### Без интернета (конференции)

`python run_local.py` (или конфигурация **1. Site + API**) — сайт и демо на http://localhost:8000.
Чтобы открыть с телефонов в той же сети Wi‑Fi: `python run_local.py --host 0.0.0.0`, адрес — `http://<IP ноутбука>:8000`.

### Другие площадки

- Docker (Railway, Fly.io, Koyeb, Google Cloud Run, Yandex Cloud и др.):
  `docker build -t immoonity .`, затем `docker run -p 8000:8000 immoonity`. Порт берётся из переменной `PORT`.
- Procfile (Heroku и совместимые): `web: gunicorn wsgi:app`.
- Только сайт на статическом хостинге (GitHub Pages и т.п.): содержимое `immoonity-site`. Если API на
  том же адресе нет, демо обращается к `https://immoonity-api.onrender.com` (константа `RENDER_API` в
  `index.html`) или к адресу из параметра `?api=https://...`.

## API

| Метод | Путь | |
|---|---|---|
| GET | `/api/health` | проверка доступности и версии |
| GET | `/api/models` | модели: входы, пороги, веса, проверка, источники |
| POST | `/predict` | риск, 90% интервал, уровень, факторы, интерпретация (`?lang=ru` или `en`) |
| POST | `/api/consultant/prompt` | запрос для LLM-консультанта |

Поля запроса — в `immoonity-app/README.md`.

Демонстрационная исследовательская модель, не медицинское изделие.
