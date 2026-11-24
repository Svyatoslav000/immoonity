# IMMOONITY

[![tests](https://github.com/Svyatoslav000/immoonity/actions/workflows/tests.yml/badge.svg)](https://github.com/Svyatoslav000/immoonity/actions/workflows/tests.yml)

English | [Русский](README.ru.md)

Immune risk assessment for spaceflight: a website with an interactive demo and an API for two models —
pre-flight (physical fitness) and in-flight (biomarkers).

**Live:** https://immoonity.onrender.com · **Demo deck (7 slides):** [docs/IMMOONITY_demo.pdf](docs/IMMOONITY_demo.pdf)

| Folder / file | Contents |
|---|---|
| `immoonity-site/` | website (single page; the Demo section calls the API) |
| `immoonity-app/` | API, models, training, data, tests |
| `wsgi.py`, `gunicorn.conf.py` | site and API as one service |
| `render.yaml`, `amvera.yml`, `Dockerfile`, `Procfile`, `.python-version` | deployment |
| `MODEL.md` | model rationale and sources |
| `CHANGES.md` | changelog |

## Models

| | Earth (pre-flight) | In-flight |
|---|---|---|
| Outcome | reactivation of a latent herpesvirus (EBV, VZV, CMV) during a ~6-month mission | multi-system immune dysregulation (≥2 of 4 subsystems) by the end of the mission |
| Inputs | sex, VO₂max, push-ups, pull-ups | IL-6, NLR, cortisol (before and in flight), EBV DNA in saliva, mission length |
| Parameters | Bayesian logistic regression on 22 ISS crew members (Agha et al., 2020) | derived from published studies |
| Checks | leave-one-out AUC 0.65, Brier 0.18 | NASA OSDR data of the Inspiration4 crew (OSD-569, OSD-575) |

Research demonstrator, not a medical device.

The demo supports English, Russian and Simplified Chinese. A series has one pre-flight assessment and up to three in-flight visits. Enter the actual flight day at each visit. The summary keeps the original risk estimates and compares measured values across visits. Changing language preserves the current series.

The evidence check compares each supplied marker with compatible human p05–p95 limits, including both endpoints. Its registry is currently empty. The composite probability by flight day requires independently confirmed outcomes and calibration. [Research data and coverage](immoonity-app/research/README.md).

## Run locally

Python 3.10+ (3.13 recommended):

```bash
pip install -r requirements-dev.txt
```

```bash
python run_local.py
```

The demo opens at http://localhost:8000/#demo. Use `--lang ru` or `--lang zh` to choose the initial language and `--port` to change the port.
Tests: `python -m pytest` in `immoonity-app`.

### PyCharm

1. **File → Open** → the `immoonity` folder.
2. **Add Interpreter → Virtualenv**, then install `requirements-dev.txt` when PyCharm offers it.
3. Run configuration **1. Site + API**.

| Run configuration | What it does |
|---|---|
| 1. Site + API | site with the demo and API on port 8000 |
| 2. Site + API (Russian consultant) | the same, interpretation in Russian |
| 3. API only (app.py) | API only, port 5000 |
| 4. Tests (pytest) | API and model tests |
| 5. Retrain models | rebuild `models/*.json` after editing `training/config.py` |

## Deploy

### Render (free)

1. render.com → **New → Blueprint** → select this repository → **Apply**.
2. Everything comes from `render.yaml`: Python from `.python-version`, build `pip install -r requirements.txt`,
   start `gunicorn wsgi:app`, health check `/api/health`, region Frankfurt.
3. Every push to `main` redeploys the site.

A free instance sleeps after 15 minutes without traffic; the first request after that takes up to a minute.

### Russia: Amvera (no VPN needed)

Render is served through Cloudflare, which is throttled in Russia. Amvera is a Russian platform of the same kind:
it builds the `Dockerfile` from the repository; settings are in `amvera.yml` (port 8000).

1. amvera.ru → sign up → **Create application**.
2. Source: this GitHub repository, branch `main`; the smallest plan is enough.
3. After the build, enable the free domain under **Domains**: it serves the site and the demo.
4. A push to `main` updates the app (otherwise use **Rebuild**).

The site uses no external CDNs: fonts and GSAP are in `immoonity-site/vendor/`.

### Offline (conferences)

`python run_local.py` (or the **1. Site + API** run configuration) serves the site and the demo at
http://localhost:8000. For phones on the same Wi-Fi: `python run_local.py --host 0.0.0.0`, then
`http://<laptop IP>:8000`.

### Other hosts

- Docker (Railway, Fly.io, Koyeb, Google Cloud Run, Yandex Cloud, etc.): `docker build -t immoonity .`, then
  `docker run -p 8000:8000 immoonity`. The port is taken from `PORT`.
- Procfile (Heroku and compatible): `web: gunicorn wsgi:app`.
- Static site only (GitHub Pages, etc.): the `immoonity-site` folder. Without an API at the same address the demo
  calls `https://immoonity-api.onrender.com` (`RENDER_API` in `index.html`) or the address from `?api=https://...`.

## API

| Method | Path | |
|---|---|---|
| GET | `/api/health` | availability and version |
| GET | `/api/models` | model cards: inputs, thresholds, weights, checks, sources |
| POST | `/predict` | risk, 90% interval, level, factors and interpretation in `en`, `ru` or `zh` |
| POST | `/api/consultant/prompt` | request for an LLM consultant |

Request fields:

- earth model — `sex` (M/F), `vo2max`, `pullups`, `pushups`;
- in-flight model — `il6_a`, `nlr_a`, `ebv`, `corta`, `days`; optional baselines `il6_b`, `nlr_b`, `cortb`.

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"sex": "M", "vo2max": 48, "pullups": 15, "pushups": 60}'
```
