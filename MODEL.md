# Model rationale

## What the models estimate

| | Earth (pre-flight) | In-flight |
|---|---|---|
| Outcome | reactivation of at least one latent herpesvirus (EBV, VZV, CMV) during a ~6-month mission | involvement of ≥2 of 4 immune subsystems by the end of the mission |
| Inputs | sex, VO₂max, push-ups, pull-ups | IL-6, NLR, cortisol (before and in flight), EBV DNA in saliva, mission length |
| Parameters | fitted to 22 ISS crew members (Agha 2020) | set from published studies |
| Validation | leave-one-out: AUC 0.65, Brier 0.18 | checks on data without target leakage (below) |

Parameters, thresholds and sources: `immoonity-app/training/config.py`; results: `immoonity-app/reports/metrics.json`.

## Earth model

- Fitness index F = 0.4·VO₂max + 0.3·push-ups + 0.3·pull-ups; each component is a soft threshold.
  The weights are proportional to |ln RR| from Agha 2020: high aerobic fitness lowers the reactivation risk by 29%,
  high upper-body endurance by 39%; 0.41 : 0.59.
- Coefficients (Bayesian logistic regression, weakly informative priors): intercept +1.87,
  index −1.65 (fully fit vs unfit: odds ×0.19), male +0.26 (not significant).
- 17 of 22 crew members (77%) reactivated, so even fit people have a 55–65% risk.
- Leave-one-out: AUC 0.65 (95% CI 0.41–0.88), Brier 0.18. The sample is small, so the intervals are wide.
- Targets (VO₂max 43 / 36, push-ups 45 / 20, pull-ups 10 / 3 for men / women) are the team's benchmarks,
  not adjusted for age.

## In-flight model

### Subsystems and thresholds

| Subsystem | Involved if | Basis | Weight |
|---|---|---|---|
| Inflammation | IL-6 > 7 pg/mL or a rise > +71% | 95th percentile of 817 healthy adults (Elecsys IL-6); RCV for CVi 30% | 1.0 |
| Leukocyte shift | NLR > 3.5 or a rise > +46% | normal range 0.78–3.53 (Forget 2017); RCV for CVi 19% | 0.75 |
| EBV reactivation | EBV DNA in saliva > 129 copies/mL | midpoint between 40 before flight and 417 in flight (Pierson 2005) | 1.25 |
| Stress axis | cortisol > 550 nmol/L or a rise > +39% | RCV for CVi 16% (15–21% across databases → +37…+50%) | 1.0 |

RCV is the reference change value: √2 · 1.645 · √(CVa² + CVi²), CVa = 5% (Fraser 2001). The thresholds are soft:
near a threshold the contribution changes smoothly. The weights are an expert estimate of clinical significance:
EBV is closest to clinical events, NLR is non-specific (acute stress, sampling time).

### Why the parameters are not fitted

In the team's group-level dataset (`aggregated_dataset.csv`) the outcome `outcome_severity_score` equals the sum of
the flags of the same subsystems that serve as model inputs in 37 of 41 rows. A model fitted to such data reproduces
the outcome definition: the metrics of version 3.0.0 (AUC 0.98, Brier 0.05) and the ROC-AUC of 0.980 on the site
came from this leakage, not from accuracy. There are no open individual-level "markers → outcome" data.

So the parameters are set explicitly:

- Mission length: +0.21 log-odds per doubling (90%: 0.09–0.45). Rooney 2019: the share of astronauts shedding
  viruses on 10–16-day flights and on the ISS (≥180 days) — any herpesvirus 53 → 61%, VZV 41 → 65%,
  EBV 82 → 96%, CMV 47 → 61%; that is 0.09, 0.27, 0.45 and 0.15 per doubling, median 0.21.
- State: assumption q = 0.15 (0.07–0.30), the probability that a subsystem stable early in flight becomes
  involved by month 6. This gives a risk by day 180 of ~11% with no involved subsystems, ~39% with one and 90% with
  two (the outcome is already met; 10% allows for a one-off outlier). The intercept −2.27 and slope 2.15 are the line
  through these points.
- The interval reflects the uncertainty of q, of the 90% and of the mission-length effect.

### Checks on data without leakage (`training/checks.py`)

| Check | Data | Result |
|---|---|---|
| Leakage | `aggregated_dataset.csv` | outcome = sum of the inputs in 37 of 41 rows |
| Mission-length effect | 22 real spaceflight groups: outcome and mission length only | +0.21 ± 0.23 per doubling, +0.32 ± 0.26 for viral reactivation — matches the model |
| NLR variability | Inspiration4: 4 people × 3 pre-flight draws (NASA OSDR, OSD-569) | 20.8% vs 19.8% assumed |
| NLR shift after the 3-day flight | Inspiration4, R+1 | +23%, +45%, −29%, −11%: the +46% threshold not exceeded (one borderline) |
| IL-6 variability | Inspiration4: 4 people × 3 pre-flight draws (NASA OSDR, OSD-575) | 27% vs 30% assumed |
| IL-6 shift after the 3-day flight | Inspiration4, R+1 | +81%, +31%, +190%, +59%: the +71% threshold exceeded in two — the post-landing IL-6 rise is also reported by Kim 2024 |
| Baseline taken 3 days before launch | Inspiration4 | the decision changes for one person for both NLR and IL-6 — take "before" values 1–2 months before launch |

## Mission length: "if the markers did not change, they will not change over 2000 days either"

### What the evidence supports

- Most immune shifts appear in the first weeks of flight and then stay at the same level rather than growing:
  6-month ISS missions (Crucian 2014, 2015, 2018); in the 340-day NASA Twins Study inflammatory markers were raised
  throughout the flight and returned to normal after landing (Garrett-Bakelman 2019).
- Individual resilience is real: better fitness means less reactivation (Agha 2020: −29% and −39%); NK-cell function
  fell less in experienced astronauts than in first-time flyers (Bigley 2019); some crew members' VO₂peak barely
  changes in flight (Moore 2014).

### What it does not support

- Viral reactivation grows with mission length: 53% of crew on 10–16-day flights vs 61% on the ISS, VZV 41 → 65%;
  after long missions shedding lasts up to 30 days vs 3–5 (Rooney 2019; Mehta 2017).
- Late changes happen: during a year of isolation at Concordia station immune responses rose sharply after
  3–4 months (Feuerecker 2019); in the 520-day Mars-500 study cortisol was higher and immune responses stronger
  (Yi 2014).
- Events accumulate even in a stable state: on the ISS rashes occur 1.12 times and upper respiratory symptoms
  0.97 times per flight-year; 46% of crew members had a "notable" event per mission (Crucian 2016).
- Radiation accumulates linearly: 0.2–0.5 mSv/day on the ISS, ≈1.8 mSv/day in interplanetary flight
  (Zeitlin 2013). Over 2000 days that is 400–1000 mSv in orbit or ~3600 mSv in deep space, against NASA's career
  limit of 600 mSv. Early markers do not reflect this.
- No data exist: the longest spaceflight is 437 days (V. Polyakov, 1994–1995; Manzey 1998); 2000 days is 4.6 times
  longer.

### Conclusion

Stable markers early in flight are a good sign, not a guarantee: the risk keeps growing, though ever more slowly.
The model reflects this: with stable markers the risk grows with mission length more slowly than once shifts have
started; beyond 437 days it shows a warning, a wider interval and a radiation dose estimate.

| Profile | 30 days | 180 days | 437 days | 1000 days | 2000 days |
|---|---|---|---|---|---|
| stable markers | 7% (2–26) | 11% (3–36) | 14% (3–43) | 17% (4–52) | 21% (4–61) |
| cortisol ↑ | 32% (14–57) | 44% (24–67) | 51% (29–73) | 57% (31–80) | 62% (30–86) |
| cortisol ↑ + EBV 417 | 85% (67–94) | 91% (79–96) | 93% (83–97) | 94% (84–98) | 95% (84–99) |

90% intervals in brackets. For stable markers at 2000 days: 5% at q = 0.07 and 54% at q = 0.30;
15% and 37% with a smaller and larger mission-length effect (`reports/metrics.json → scenarios`).

## NASA data

Search of NASA sites (November 2026):

| Source | What was found | Use |
|---|---|---|
| data.nasa.gov, query "immune" | 80 datasets: mice, fruit flies, cells in vitro; no human data with the model's markers | — |
| NASA OSDR (osdr.nasa.gov, API) | Inspiration4: OSD-569 (complete blood count), OSD-575 (serum cytokines and chemistry), OSD-571 (plasma metabolomics), OSD-656 (urine); Axiom: OSD-903, OSD-943 (gene expression) | OSD-569 → `inspiration4_cbc.csv`, OSD-575 → `inspiration4_il6.csv` |
| api.nasa.gov | 16 APIs; only the OSDR API relates to immunity | used to get the OSDR data |
| Earthdata | Earth science data; for "immune" only study descriptions without data (fish, Antarctic personnel) | — |
| science.nasa.gov | articles and programs, not data | — |

In the Inspiration4 plasma metabolomics (OSD-571) cortisol is higher after landing than before flight (p = 0.025,
0.11 after correction for multiple comparisons), but the data are normalized, so the cortisol rise threshold cannot
be checked against them.

The team's data package:

| Package files | Use |
|---|---|
| 06, 08 — Inspiration4 complete blood count (OSD-569) | `data/inspiration4_cbc.csv` |
| 09 — dataset 1 (41 rows with quality flags) | `data/aggregated_dataset.csv`: leakage and mission-length checks |
| 10, 11 — datasets 2 and 3 | not used: the values were extracted from papers automatically and not verified against the sources |
| 01–04 — gene expression (human and mouse) | not used: the model works with laboratory markers; mouse tissues do not transfer to human blood |

## Limitations

- The earth model is based on 22 people from a single study; the in-flight model uses parameters from the
  literature and assumptions and has not been validated on individual outcomes.
- No adjustment for age, time of day (cortisol) or sample type.
- Validation on individual outcomes needs NASA LSDA data (Integrated Immune, on request); the only open data are
  from the 3-day Inspiration4 flight (4 people).

## References

- Agha NH, et al. FASEB J. 2020;34:2869–2881. https://doi.org/10.1096/fj.201902327R
- Bigley AB, et al. J Appl Physiol. 2019;126:842–853. https://doi.org/10.1152/japplphysiol.00761.2018
- Crucian BE, et al. J Interferon Cytokine Res. 2014;34:778–786. https://doi.org/10.1089/jir.2013.0129
- Crucian B, et al. NPJ Microgravity. 2015;1:15013. https://doi.org/10.1038/npjmgrav.2015.13
- Crucian B, et al. Int J Gen Med. 2016;9:383–391. https://doi.org/10.2147/IJGM.S114188
- Crucian BE, et al. Front Immunol. 2018;9:1437. https://doi.org/10.3389/fimmu.2018.01437
- Feuerecker M, et al. Allergy. 2019;74:64–77. https://doi.org/10.1111/all.13545
- Forget P, et al. BMC Res Notes. 2017;10:12. https://doi.org/10.1186/s13104-016-2335-5
- Fraser CG. Biological Variation: From Principles to Practice. AACC Press; 2001.
- Garrett-Bakelman FE, et al. Science. 2019;364:eaau8650. https://doi.org/10.1126/science.aau8650
- Kim J, et al. Nat Commun. 2024;15:4954. https://doi.org/10.1038/s41467-024-49211-2
- Manzey D, Lorenz B, Poljakov V. Ergonomics. 1998;41:537–559. https://doi.org/10.1080/001401398186991
- Mehta SK, et al. NPJ Microgravity. 2017;3:11. https://doi.org/10.1038/s41526-017-0015-y
- Moore AD Jr, et al. J Appl Physiol. 2014;117:231–238. https://doi.org/10.1152/japplphysiol.01251.2013
- NASA OCHMO. Radiation protection technical brief (NASA-STD-3001).
  https://www.nasa.gov/wp-content/uploads/2023/03/radiation-protection-technical-brief-ochmo.pdf
- NASA Open Science Data Repository: OSD-569, OSD-575 (SpaceX Inspiration4).
  https://osdr.nasa.gov/bio/repo/data/studies/OSD-569, https://osdr.nasa.gov/bio/repo/data/studies/OSD-575
- Pierson DL, et al. Brain Behav Immun. 2005;19:235–242. https://doi.org/10.1016/j.bbi.2004.08.001
- Rooney BV, et al. Front Microbiol. 2019;10:16. https://doi.org/10.3389/fmicb.2019.00016
- Stowe RP, et al. Psychosom Med. 2001;63:891–895.
- Yi B, et al. Brain Behav Immun. 2014;40:203–210. https://doi.org/10.1016/j.bbi.2014.03.018
- Zeitlin C, et al. Science. 2013;340:1080–1084. https://doi.org/10.1126/science.1235989
