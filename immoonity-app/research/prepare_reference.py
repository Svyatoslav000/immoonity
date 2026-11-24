"""Rebuild the paired human marker reference from IMMOONITY's two Inspiration4 extracts."""
import argparse
import csv
from decimal import Decimal
from pathlib import Path


def read_visits(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        visits = {}
        for row in csv.DictReader(stream):
            key = (row["subject_id"], row["timepoint"])
            if key in visits:
                raise ValueError(f"Duplicate visit {key} in {path.name}")
            visits[key] = row
        return visits


def assemble(repo):
    data = repo / "immoonity-app" / "data"
    cbc = read_visits(data / "inspiration4_cbc.csv")
    cytokines = read_visits(data / "inspiration4_il6.csv")
    if cbc.keys() != cytokines.keys():
        raise ValueError("The extracts have different participant/visit keys")
    for key, row in cbc.items():
        participant, timepoint = key
        day = int(row["day"])
        if day != int(cytokines[key]["day"]):
            raise ValueError(f"Timepoint mismatch at {key}")
        if timepoint == f"L{day}" and day < 0:
            phase, anchor = "preflight", "launch"
        elif timepoint == f"R+{day}" and day >= 0:
            phase, anchor = "postflight", "landing"
        else:
            raise ValueError(f"Unrecognized timepoint at {key}")
        anc, alc = (Decimal(row[k]) / 1000 for k in ("neutrophils_per_ul", "lymphocytes_per_ul"))
        nlr, il6 = Decimal(row["nlr"]), Decimal(cytokines[key]["il6_pg_ml"])
        if anc < 0 or alc <= 0 or il6 < 0 or abs(nlr - anc / alc) > Decimal("0.000051"):
            raise ValueError(f"Check concentrations or reported NLR at {key}")
        yield dict(study="Inspiration4", species="Homo sapiens", subject_id=participant,
                   timepoint=timepoint, phase=phase, day_anchor=anchor, day_relative=day,
                   anc_1e9_L=format(anc, "f"), alc_1e9_L=format(alc, "f"), nlr=str(nlr),
                   il6_pg_mL=str(il6), cbc_source="OSD-569", il6_source="OSD-575")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = list(assemble(args.repo))
    if not rows:
        raise ValueError("Both extracts are empty")
    with args.output.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=rows[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} visits, {len({r['subject_id'] for r in rows})} participants")
