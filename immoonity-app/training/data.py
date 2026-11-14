"""Загрузка исходных данных и матрицы признаков для обучения."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

VIRUSES = ("ebv_reactivation", "vzv_reactivation", "cmv_reactivation")


def read_csv(path: str | Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def earth_table(rows: list[dict], cfg: dict, weights: dict | None = None):
    """Признаки [1, индекс подготовки, мужской пол]; исход — реактивация хотя бы одного вируса."""
    w = weights or {k: c["weight"] for k, c in cfg["components"].items()}
    cols = cfg["component_columns"]
    X, y = [], []
    for r in rows:
        fitness = sum(w[k] * int(r[cols[k]]) for k in w)
        X.append([1.0, fitness, float(r["sex"] == "M")])
        y.append(int(any(int(r[v]) for v in VIRUSES)))
    return np.array(X), np.array(y)
