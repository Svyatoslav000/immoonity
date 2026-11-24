# immoonity-app

Immune risk API: the earth (pre-flight) and in-flight models.

## Run

```bash
pip install -r requirements.txt
python app.py
```

API only (for example on Render): `gunicorn app:app`. Together with the site: `gunicorn wsgi:app` from the repository root.

## API

| Method | Path | |
|---|---|---|
| GET | `/`, `/api/health` | health check |
| GET | `/api/models` | model cards: inputs, thresholds, weights, checks, sources |
| POST | `/predict` | prediction and interpretation in `en`, `ru` or `zh` |
| POST | `/api/consultant/prompt` | request for an LLM consultant |

Request fields:

- earth model — `sex` (M/F), `vo2max`, `pullups`, `pushups`;
- in-flight model — `il6_a`, `nlr_a`, `ebv`, `corta`, `days`; optional `il6_b`, `nlr_b`, `cortb`.

Response: `risk` (%), `risk_interval` (90%), `level`, `factors`, `warnings`, `interpretation`.
Input errors return HTTP 400 with `details` for each field.

Series requests can include `"series_visit": {}` before launch and, for example, `"series_visit": {"day": 15}` in flight. The flight day is the actual day of sampling. The existing `days` field is the planned mission length. The response adds `series_assessment` with the evidence route, per-marker comparisons and the composite endpoint status. With `"include_translations": true`, the response also includes the other two interpretations for the same numeric result.

## Models and training

- `models/*.json` — coefficients, covariance, thresholds, rationale, sources.
- `training/config.py` — thresholds, weights, priors; in-flight parameters and their derivation.
- `training/checks.py` — checks of the in-flight model on data without target leakage.
- `python training/train_models.py` — builds the models (needs numpy and matplotlib); output in `models/` and `reports/`.
- `python -m pytest` — tests.

The earth model is fitted to Agha et al. 2020; the in-flight parameters come from the literature — see `MODEL.md` in
the repository root.

## Data

- `pierson_data.csv` — Agha et al., 2020: 22 ISS crew members (earth model).
- `agha_data.csv` — Pierson et al., 2005: EBV threshold calibration.
- `aggregated_dataset.csv` — 41 study groups with quality flags (`qc_flags`); checks only.
- `inspiration4_cbc.csv` — complete blood count of the Inspiration4 crew, NASA OSDR OSD-569 (Kim et al., 2024).
- `inspiration4_il6.csv` — serum IL-6 of the Inspiration4 crew, NASA OSDR OSD-575 (Eve HD71 panel).

The first two file names do not match their sources; they are kept as in the original data.
