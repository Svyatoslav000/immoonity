"""Descriptive p05/p95 for exact visits; type 7 interpolation, one sample per person per visit."""
import csv
from decimal import Decimal
from pathlib import Path


def quantile(values, probability):
    values = sorted(values)
    pos = (len(values) - 1) * Decimal(probability)
    i = int(pos)
    return values[i] + (pos - i) * (values[min(i + 1, len(values) - 1)] - values[i])


def build(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        inputs = list(csv.DictReader(f))
    for visit in ("L-44", "R+1"):
        rows = [r for r in inputs if r["timepoint"] == visit]
        subjects = {r["subject_id"] for r in rows}
        if not rows or len(subjects) != len(rows):
            raise ValueError(f"Missing or duplicate participant at {visit}")
        for field, unit, source in [("nlr", "ratio", "OSD-569"), ("il6_pg_mL", "pg/mL", "OSD-575")]:
            values = [Decimal(r[field]) for r in rows]
            yield dict(study="Inspiration4", visit=visit, phase=rows[0]["phase"], marker=field, unit=unit,
                       n_people=len(subjects), p05=str(quantile(values, "0.05")), p95=str(quantile(values, "0.95")),
                       quantile_method="linear_type_7", status="exploratory_only", source=source)


if __name__ == "__main__":
    folder = Path(__file__).resolve().parent
    rows = list(build(folder / "human_reference.csv"))
    with (folder / "descriptive_percentiles.csv").open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=rows[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
