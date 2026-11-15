# Changelog

## 3.1.3

- Hosting reachable from Russia: `amvera.yml` (Amvera Cloud builds the `Dockerfile`); the Docker image runs one
  worker. Fonts and GSAP are served from `immoonity-site/vendor/`, so the site needs no external CDNs and
  works offline.
- README: deploying on Amvera and running offline at conferences.

## 3.1.2

- Consultant: Sources come before Limitations, and Limitations open on click like Sources.
- What-if scenarios: softer wording; single-marker scenarios that change the estimate by less than 5 pp are hidden;
  with two or more shifted markers the consultant shows the effect of normalising all of them.
- Earth model notes: age adjustment is in development.
- Consultant footer: "Health decisions must be made together with a physician."
- Demo deck for NASA Space Apps 2026: `docs/IMMOONITY_demo.pdf`.

## 3.1.1

- Site live at https://immoonity.onrender.com (Render Blueprint).
- Team section: Svyatoslav, lead developer.
- Documentation, code comments, model-card texts and PyCharm run configurations in English; the Russian interface
  of the demo (`?lang=ru`) stays.
- Model parameters and API responses unchanged.

## 3.1.0 — MVP

### Models

- The in-flight model is no longer fitted to `aggregated_dataset.csv`: there the outcome equals the sum of the
  inputs in 37 of 41 rows (target leakage). Its 3.0.0 metrics (AUC 0.98, Brier 0.05) are not valid.
- In-flight parameters are set from the literature: mission length +0.21 per doubling (Rooney 2019), state from the
  assumption q = 0.15 (0.07–0.30). Risk with stable markers at 180 days: 11% (was 2%).
- Mission length: the risk grows ever more slowly; beyond 437 days (the longest spaceflight) a warning and a wider
  interval; for missions of a year or longer, a radiation dose estimate.
- Outcome named precisely: "multi-system immune dysregulation (≥2 subsystems)" instead of "clinically relevant" —
  such shifts are usually asymptomatic.
- Checks without leakage (`training/checks.py`): mission-length effect in the team's data +0.21 per doubling;
  NLR variability in the Inspiration4 crew 20.8% vs 19.8% assumed; after the 3-day flight the NLR threshold was not
  exceeded.
- Data: added `inspiration4_cbc.csv` (NASA OSDR, OSD-569) and `inspiration4_il6.csv` (OSD-575);
  `aggregated_dataset.csv` has 41 rows with quality flags. IL-6 variability in the Inspiration4 crew 27% vs 30%
  assumed; one day after landing the IL-6 rise threshold was exceeded in 2 of 4.
- Earth model unchanged.
- Rationale and sources: `MODEL.md`.

### Site

- Solution section: unsupported ROC-AUC 0.825 / 0.980 and "2,000+ data points" removed.
- Demo: "Before" values are taken 1–2 months before launch.
- All images have Latin file names (`main.png`, `block3.png`, etc.): Cyrillic names broke archive extraction on
  Windows.

### Project

- One repository: `wsgi.py` serves the site and the API from one address.
- Deployment: `render.yaml` (Render Blueprint), `Dockerfile`, `Procfile`, `.python-version`, `gunicorn.conf.py`.
- GitHub Actions: tests and a server smoke test on every push.
- `requirements.txt` for the server, `requirements-dev.txt` for tests and training.

## 3.0.0

### Models

- Outcomes defined explicitly: earth model — reactivation of latent viruses (EBV, VZV, CMV) in flight;
  in-flight model — dysregulation of two or more subsystems.
- Bayesian logistic regression: stable weights and a 90% prediction interval.
- Earth model: fitness index weighted 0.4 / 0.3 / 0.3 (VO₂max / push-ups / pull-ups, after Agha et al., 2020).
  Pull-ups no longer increase the risk.
- In-flight model: subsystem score weighted EBV 1.25, cortisol 1.0, IL-6 1.0, NLR 0.75.
  Mission length increases the risk (it used to decrease it).
- Thresholds: EBV 500 → 129 copies/mL; IL-6 rise +20% → +71%, cortisol +25% → +39%, NLR +50% → +46%
  (reference change values from biological variation).
- Soft thresholds: the risk changes smoothly, without jumps at the boundaries.
- Earth model leave-one-out Brier: 0.180.

### API

- Models stored as JSON instead of pickle; the server needs neither scikit-learn nor numpy.
- Input validation: per-field 400 errors (EN/RU) instead of 500; a zero "before" value no longer breaks the result.
- "Before flight" values are optional.
- Response: 90% interval, level, factor contributions, what-if scenarios, interpretation.
- New endpoints: `/api/health`, `/api/models`, `/api/consultant/prompt`.
- The `risk` field and the `gunicorn app:app` command are kept.

### Site (index.html, Demo section)

- Interval, risk level and consultant panel shown.
- Required fields checked; errors shown in the form instead of `alert`.
- Notice while the free Render instance wakes up.
- API address chosen automatically: local or Render.
- Male selected by default; "Before" fields optional.
- Demo script isolated: the global name `section` from the "What happens" block broke the form.
- First-screen content visible even if GSAP fails to load.
- Images renamed to `astronaut.png` and `logo.png`; unused PDF (`…0006.pdf`) removed.

## Open questions

- To confirm: EBV sample type (saliva), the 550 nmol/L cortisol threshold, age-adjusted fitness targets.
- The q = 0.15 assumption of the in-flight model needs validation on individual data (NASA LSDA, OSDR OSD-570/575).
