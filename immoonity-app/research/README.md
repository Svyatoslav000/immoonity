# Research data for the measurement series

`human_reference.csv` pairs IL-6 and blood counts by participant and sampling visit. It contains 28 visits from four Inspiration4 crew members. The time points are pre-flight or post-landing. The four percentile pairs in `descriptive_percentiles.csv` describe these participants at L−44 and R+1. Their sample sizes and phases limit their use in the in-flight model. [NASA OSD-569](https://osdr.nasa.gov/bio/repo/data/studies/OSD-569) · [NASA OSD-575](https://osdr.nasa.gov/bio/repo/data/studies/OSD-575).

`literature/` contains 116 human records and 14 animal records in seven data tables. Rows include participant observations, cohort summaries, repeat visits and figure estimates. The source register identifies the publication, table or figure, species, limitations and known cohort overlap. Participant counts and outcomes must be obtained at the level reported in each source. [Source register](literature/sources.csv).

`reference_coverage.csv` lists the available data and missing evidence by marker. The production registry in `../models/human_reference_intervals.json` accepts approved human intervals for a matching marker, unit, sampling phase, population, protocol and applicable time window. It ships empty. All required and supplied optional measurements inside the closed interval select human evidence. One verified value outside selects human and animal evidence. Incomplete coverage with no confirmed outlier leaves the route undetermined. Animal data provide context for changes within a species.

The composite endpoint is the first mission failure or clinically confirmed immunodeficiency with a documented disease by the entered flight day. The two CSV templates capture independent event ascertainment and follow-up. `outcome_labels.py` preserves unknown or censored status when the records cannot establish an outcome. A calibrated human model needs dated clinical events and follow-up. Detecting EBV DNA alone does not establish this composite event. [Mehta et al.](https://doi.org/10.1038/s41526-017-0015-y).

The site describes the commercial crew-hour figure as a 2025 NASA cost example, 65% as VZV shedding in an ISS study, and 3.4 as the observed medical event rate per crew member per flight year. NASA gap IM-501 concerns testing immune countermeasures in flight. [NASA cost example](https://ntrs.nasa.gov/citations/20250006299) · [VZV study overview](https://doi.org/10.3389/fmicb.2019.00016) · [NASA immune risk evidence report](https://humanresearchroadmap.nasa.gov/evidence/reports/IMMUNE%20EB%20Update%202021%20v02%20FINAL_6-15-22.pdf) · [IM-501](https://humanresearchroadmap.nasa.gov/Gaps/gap.aspx?i=674).

To rebuild the paired data and descriptive percentiles from the repository root:

```sh
python immoonity-app/research/prepare_reference.py . immoonity-app/research/human_reference.csv
python immoonity-app/research/reference_percentiles.py
```
