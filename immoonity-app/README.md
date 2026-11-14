# immoonity-app

API оценки иммунного риска: земная (предполётная) и полётная модели.

## Запуск

```bash
pip install -r requirements.txt
python app.py
```

Отдельно от сайта (например, на Render): `gunicorn app:app`. Вместе с сайтом — `gunicorn wsgi:app` из корня репозитория.

## API

| Метод | Путь | |
|---|---|---|
| GET | `/`, `/api/health` | проверка доступности |
| GET | `/api/models` | модели: входы, пороги, веса, проверка, источники |
| POST | `/predict` | прогноз и интерпретация, язык `?lang=ru` или `en` |
| POST | `/api/consultant/prompt` | запрос для LLM-консультанта |

Поля запроса:

- земная модель — `sex` (M/F), `vo2max`, `pullups`, `pushups`;
- полётная — `il6_a`, `nlr_a`, `ebv`, `corta`, `days`; необязательные `il6_b`, `nlr_b`, `cortb`.

Ответ: `risk` (%), `risk_interval` (90%), `level`, `factors`, `warnings`, `interpretation`.
Ошибки ввода — статус 400 с `details` по каждому полю.

## Модели и обучение

- `models/*.json` — коэффициенты, ковариация, пороги, обоснования, источники.
- `training/config.py` — пороги, веса, априорные распределения; параметры полётной модели и их вывод.
- `training/checks.py` — проверки полётной модели на данных без утечки.
- `python training/train_models.py` — сборка моделей (нужны numpy и matplotlib), результаты в `models/` и `reports/`.
- `python -m pytest` — тесты.

Земная модель обучена на данных Agha et al. 2020; параметры полётной заданы по литературе — см. `MODEL.md` в корне.

## Данные

- `pierson_data.csv` — Agha et al., 2020: 22 члена экипажа МКС (земная модель).
- `agha_data.csv` — Pierson et al., 2005: калибровка порога ВЭБ.
- `aggregated_dataset.csv` — 41 группа из исследований с пометками качества (`qc_flags`); только для проверок.
- `inspiration4_cbc.csv` — общий анализ крови экипажа Inspiration4, NASA OSDR OSD-569 (Kim et al., 2024).
- `inspiration4_il6.csv` — IL-6 в сыворотке экипажа Inspiration4, NASA OSDR OSD-575 (панель Eve HD71).

Имена первых двух файлов не совпадают с источниками, оставлены как в исходных данных.
