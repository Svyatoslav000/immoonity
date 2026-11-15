"""Risk calculation with the models from models/*.json."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

# z for two-sided intervals
_Z = {0.8: 1.2815515655446004, 0.9: 1.6448536269514722, 0.95: 1.959963984540054}

BORDERLINE_LOW = 0.25
BORDERLINE_HIGH = 0.75


def sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def soft_step(value: float, threshold: float, softness: float) -> float:
    """Soft threshold: 0.5 at the threshold, 0 and 1 far from it."""
    return sigmoid((value - threshold) / softness)


def soft_step_inverse(membership: float, threshold: float, softness: float) -> float:
    return threshold + softness * math.log(membership / (1.0 - membership))


def status_of(membership: float) -> str:
    if membership >= BORDERLINE_HIGH:
        return "above"
    if membership <= BORDERLINE_LOW:
        return "below"
    return "borderline"


class RiskModel:
    """Logistic model: risk = sigmoid(beta·x), interval from the coefficient covariance."""

    kind = "base"

    def __init__(self, spec: dict[str, Any]):
        self.spec = spec
        self.name: str = spec["model"]
        self.version: str = spec["version"]
        self.terms: list[str] = spec["terms"]
        self.beta: list[float] = [float(b) for b in spec["coefficients"]]
        self.cov: list[list[float]] = [[float(v) for v in row] for row in spec["covariance"]]
        self.interval_level: float = float(spec.get("interval_level", 0.9))
        self.inputs: dict[str, Any] = spec["inputs"]
        self.levels: list[dict[str, Any]] = spec["risk_levels"]
        if len(self.beta) != len(self.terms) or len(self.cov) != len(self.terms):
            raise ValueError(f"model {self.name}: inconsistent coefficient/covariance sizes")

    def coef(self, term: str) -> float:
        return self.beta[self.terms.index(term)]

    def _eta(self, x: list[float]) -> float:
        return sum(b * v for b, v in zip(self.beta, x))

    def _eta_sd(self, x: list[float]) -> float:
        n = len(x)
        var = sum(x[i] * self.cov[i][j] * x[j] for i in range(n) for j in range(n))
        return math.sqrt(max(var, 0.0))

    def risk_of(self, x: list[float]) -> float:
        return sigmoid(self._eta(x))

    def interval_of(self, x: list[float]) -> tuple[float, float]:
        z = _Z.get(round(self.interval_level, 2), 1.6448536269514722)
        eta, sd = self._eta(x), self._eta_sd(x)
        return sigmoid(eta - z * sd), sigmoid(eta + z * sd)

    def level_of(self, risk: float) -> dict[str, Any]:
        pct = risk * 100.0
        for lvl in self.levels:
            if pct < lvl["below"]:
                return lvl
        return self.levels[-1]

    def featurize(self, values: dict[str, Any]) -> tuple[list[float], dict[str, Any], list[dict]]:
        raise NotImplementedError

    def factors(self, values: dict[str, Any], x: list[float], details: dict[str, Any]) -> list[dict]:
        raise NotImplementedError

    def predict(self, values: dict[str, Any]) -> dict[str, Any]:
        """values are already validated (validation.validate)."""
        x, details, warnings = self.featurize(values)
        risk = self.risk_of(x)
        low, high = self.interval_of(x)
        level = self.level_of(risk)
        return {
            "model": self.name,
            "model_version": self.version,
            "risk": round(risk * 100.0, 1),
            "risk_interval": {
                "low": round(low * 100.0, 1),
                "high": round(high * 100.0, 1),
                "level": self.interval_level,
            },
            "level": {"code": level["code"], "color": level["color"]},
            "linear_predictor": round(self._eta(x), 4),
            "features": {t: round(v, 4) for t, v in zip(self.terms, x)},
            "details": details,
            "factors": self.factors(values, x, details),
            "warnings": warnings,
            "inputs": values,
        }


class EarthModel(RiskModel):
    """Pre-flight model: physical fitness -> risk of latent virus reactivation."""

    kind = "earth"

    def __init__(self, spec: dict[str, Any]):
        super().__init__(spec)
        self.components: dict[str, Any] = spec["components"]

    def _memberships(self, values: dict[str, Any]) -> dict[str, float]:
        sex = values["sex"]
        return {name: soft_step(float(values[name]), comp["threshold"][sex], comp["softness"][sex])
                for name, comp in self.components.items()}

    def _vector(self, memberships: dict[str, float], male: int) -> list[float]:
        fitness = sum(self.components[k]["weight"] * m for k, m in memberships.items())
        vec = {"intercept": 1.0, "fitness_index": fitness, "sex_male": float(male)}
        return [vec[t] for t in self.terms]

    def featurize(self, values):
        sex = values["sex"]
        male = 1 if sex == "M" else 0
        memberships = self._memberships(values)
        x = self._vector(memberships, male)
        details = {"sex": sex, "components": {}}
        for name, comp in self.components.items():
            thr, soft = comp["threshold"][sex], comp["softness"][sex]
            details["components"][name] = {
                "value": values[name],
                "unit": self.inputs[name].get("unit"),
                "threshold": thr,
                "softness": soft,
                "weight": comp["weight"],
                "membership": round(memberships[name], 4),
                "status": status_of(memberships[name]),
                # target for recommendations: threshold + 2 transition widths
                "target": round(soft_step_inverse(0.88, thr, soft), 1),
            }
        details["fitness_index"] = round(x[self.terms.index("fitness_index")], 4)
        return x, details, []

    def factors(self, values, x, details):
        sex = values["sex"]
        male = 1 if sex == "M" else 0
        memberships = self._memberships(values)
        risk = self.risk_of(x)
        b_fit = self.coef("fitness_index")
        out = []
        for name, comp in self.components.items():
            m = memberships[name]
            without = dict(memberships, **{name: 0.0})
            info = details["components"][name]
            target_m = max(m, soft_step(info["target"], info["threshold"], info["softness"]))
            risk_target = self.risk_of(self._vector(dict(memberships, **{name: target_m}), male))
            out.append({
                "factor": name,
                "kind": "fitness_component",
                "membership": round(m, 4),
                "status": status_of(m),
                "logit_contribution": round(b_fit * comp["weight"] * m, 4),
                "effect_pp": round((risk - self.risk_of(self._vector(without, male))) * 100, 1),
                "target_value": info["target"],
                "risk_at_target": round(risk_target * 100, 1),
                "potential_pp": round((risk_target - risk) * 100, 1),
            })
        other = self.risk_of(self._vector(memberships, 1 - male))
        out.append({
            "factor": "sex",
            "kind": "demographic",
            "value": sex,
            "logit_contribution": round(self.coef("sex_male") * male, 4),
            "effect_pp": round((risk - other) * 100, 1),
        })
        return out


class FlightModel(RiskModel):
    """In-flight model: shifts of four subsystems and mission length -> risk of dysregulation."""

    kind = "flight"

    def __init__(self, spec: dict[str, Any]):
        super().__init__(spec)
        self.markers: dict[str, Any] = spec["markers"]
        self.duration: dict[str, Any] = spec["duration"]
        self.evidence: dict[str, Any] = spec.get("evidence", {})
        self.radiation: dict[str, Any] | None = spec.get("radiation")

    def _eta_sd(self, x: list[float]) -> float:
        """The interval widens beyond the longest spaceflight."""
        base = super()._eta_sd(x)
        longest = self.evidence.get("longest_flight_days")
        sd = self.evidence.get("extrapolation_sd_per_doubling", 0.0)
        if not longest or not sd:
            return base
        beyond = x[self.terms.index("duration_log2")] - self._duration_term(longest)
        return math.hypot(base, sd * beyond) if beyond > 0 else base

    def _duration_notes(self, days: float) -> tuple[list[dict], dict[str, Any] | None]:
        warnings = []
        longest = self.evidence.get("longest_flight_days")
        if longest and days > longest:
            warnings.append({"code": "duration_beyond_evidence", "field": "days", "limit": longest})
        elif days > self.evidence.get("well_studied_days", float("inf")):
            warnings.append({"code": "duration_limited_evidence", "field": "days",
                             "limit": self.evidence["well_studied_days"]})
        dose = None
        if self.radiation:
            lo, hi = self.radiation["leo_msv_per_day"]
            dose = {"leo_msv": [round(lo * days), round(hi * days)],
                    "deep_space_msv": round(self.radiation["deep_space_msv_per_day"] * days),
                    "career_limit_msv": self.radiation["career_limit_msv"]}
        return warnings, dose

    @staticmethod
    def _criterion(crit: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
        kind = crit["kind"]
        res: dict[str, Any] = {"kind": kind, "threshold": crit["threshold"], "softness": crit["softness"]}
        if kind == "absolute":
            v = values.get(crit["field"])
            if v is None:
                return dict(res, computable=False, reason="missing")
            res.update(value=v, membership=soft_step(v, crit["threshold"], crit["softness"]))
        elif kind == "log10":
            v = values.get(crit["field"])
            if v is None:
                return dict(res, computable=False, reason="missing")
            res.update(value=v, membership=soft_step(
                math.log10(max(v, 0.0) + 1.0), math.log10(crit["threshold"] + 1.0), crit["softness"]))
        elif kind == "relative":
            res["before_field"] = crit["before"]
            before, after = values.get(crit["before"]), values.get(crit["after"])
            if before is None or after is None:
                return dict(res, computable=False, reason="baseline_missing")
            if before <= 0:
                return dict(res, computable=False, reason="baseline_not_positive", before=before)
            change = (after - before) / before
            res.update(before=before, after=after, change=change,
                       membership=soft_step(change, crit["threshold"], crit["softness"]))
        else:
            raise ValueError(f"unknown criterion kind {kind}")
        res["computable"] = True
        res["membership"] = round(res["membership"], 4)
        return res

    def _marker_states(self, values):
        states = {}
        for name, mk in self.markers.items():
            crits = [self._criterion(c, values) for c in mk["criteria"]]
            usable = [c for c in crits if c["computable"]]
            # a subsystem is involved if any of its criteria is met
            m = max(c["membership"] for c in usable) if usable else 0.0
            states[name] = {"membership": m, "criteria": crits}
        return states

    def _duration_term(self, days: float) -> float:
        ref = self.duration["reference_days"]
        return math.log2((days + 1.0) / (ref + 1.0))

    def _vector(self, memberships: dict[str, float], days: float) -> list[float]:
        score = sum(self.markers[k]["weight"] * m for k, m in memberships.items())
        vec = {"intercept": 1.0, "dysregulation_score": score, "duration_log2": self._duration_term(days)}
        return [vec[t] for t in self.terms]

    def featurize(self, values):
        states = self._marker_states(values)
        memberships = {k: s["membership"] for k, s in states.items()}
        x = self._vector(memberships, values["days"])
        warnings = []
        details: dict[str, Any] = {"markers": {}, "days": values["days"]}
        for name, st in states.items():
            for c in st["criteria"]:
                if not c["computable"] and c["kind"] == "relative":
                    warnings.append({"code": c["reason"], "marker": name, "field": c["before_field"]})
            details["markers"][name] = {
                "weight": self.markers[name]["weight"],
                "membership": round(st["membership"], 4),
                "status": status_of(st["membership"]),
                "criteria": st["criteria"],
            }
        details["dysregulation_score"] = round(x[self.terms.index("dysregulation_score")], 4)
        details["duration_term"] = round(x[self.terms.index("duration_log2")], 4)
        shifted = {k: 0.0 for k, m in memberships.items() if status_of(m) != "below"}
        details["risk_if_shifted_normal"] = round(
            self.risk_of(self._vector(dict(memberships, **shifted), values["days"])) * 100.0, 1)
        duration_warnings, dose = self._duration_notes(values["days"])
        warnings.extend(duration_warnings)
        if dose:
            details["radiation_dose"] = dose
        return x, details, warnings

    def factors(self, values, x, details):
        states = self._marker_states(values)
        memberships = {k: s["membership"] for k, s in states.items()}
        risk = self.risk_of(x)
        b_score = self.coef("dysregulation_score")
        out = []
        for name, mk in self.markers.items():
            m = memberships[name]
            normalised = self.risk_of(self._vector(dict(memberships, **{name: 0.0}), values["days"]))
            out.append({
                "factor": name,
                "kind": "biomarker_system",
                "membership": round(m, 4),
                "status": status_of(m),
                "logit_contribution": round(b_score * mk["weight"] * m, 4),
                "effect_pp": round((risk - normalised) * 100, 1),
                "risk_if_normal": round(normalised * 100, 1),
            })
        ref = self.duration["reference_days"]
        at_ref = self.risk_of(self._vector(memberships, ref))
        out.append({
            "factor": "days",
            "kind": "exposure",
            "value": values["days"],
            "logit_contribution": round(self.coef("duration_log2") * self._duration_term(values["days"]), 4),
            "effect_pp": round((risk - at_ref) * 100, 1),
            "reference_days": ref,
        })
        return out


_MODEL_CLASSES = {"earth": EarthModel, "flight": FlightModel}


def load_model(path: str | Path) -> RiskModel:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    return _MODEL_CLASSES[spec["model"]](spec)


def load_models(directory: str | Path = MODELS_DIR) -> dict[str, RiskModel]:
    return {name: load_model(Path(directory) / f"{name}_model.json") for name in ("earth", "flight")}
