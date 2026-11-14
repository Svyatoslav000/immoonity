"""Байесовская логистическая регрессия для малых выборок.

MAP-оценка с гауссовскими априорными распределениями (устойчива при полном разделении классов),
интервалы по аппроксимации Лапласа и её проверка выборкой по значимости.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


@dataclass
class Posterior:
    terms: list[str]
    mean: np.ndarray            # MAP-оценка
    cov: np.ndarray             # ковариация по Лапласу
    prior_mean: np.ndarray
    prior_sd: np.ndarray
    n_iter: int
    converged: bool
    loglik: float
    n: int
    events: int
    extra: dict = field(default_factory=dict)

    @property
    def sd(self) -> np.ndarray:
        return np.sqrt(np.diag(self.cov))

    def interval(self, level: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
        z = {0.9: 1.6448536269514722, 0.95: 1.959963984540054}[level]
        return self.mean - z * self.sd, self.mean + z * self.sd


def log_posterior(beta, X, y, prior_mean, prior_sd, weights=None):
    w = np.ones(len(y)) if weights is None else weights
    z = X @ beta
    ll = np.sum(w * (y * z - np.logaddexp(0.0, z)))
    lp = -0.5 * np.sum(((beta - prior_mean) / prior_sd) ** 2)
    return ll + lp


def fit_map(X, y, terms, prior_mean, prior_sd, weights=None, max_iter=200, tol=1e-10) -> Posterior:
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    mu = np.asarray(prior_mean, float)
    sd = np.asarray(prior_sd, float)
    w = np.ones(len(y)) if weights is None else np.asarray(weights, float)
    beta = mu.copy()
    converged = False
    it = 0
    for it in range(1, max_iter + 1):
        p = _sigmoid(X @ beta)
        grad = X.T @ (w * (y - p)) - (beta - mu) / sd ** 2
        hess = X.T @ (X * (w * p * (1 - p))[:, None]) + np.diag(1.0 / sd ** 2)
        step = np.linalg.solve(hess, grad)
        # метод Ньютона с дроблением шага
        t = 1.0
        lp_old = log_posterior(beta, X, y, mu, sd, w)
        while log_posterior(beta + t * step, X, y, mu, sd, w) < lp_old - 1e-12 and t > 1e-6:
            t /= 2.0
        beta = beta + t * step
        if np.max(np.abs(t * step)) < tol:
            converged = True
            break
    p = _sigmoid(X @ beta)
    hess = X.T @ (X * (w * p * (1 - p))[:, None]) + np.diag(1.0 / sd ** 2)
    cov = np.linalg.inv(hess)
    loglik = float(np.sum(w * (y * (X @ beta) - np.logaddexp(0.0, X @ beta))))
    return Posterior(list(terms), beta, cov, mu, sd, it, converged, loglik, len(y), int(y.sum()))


def importance_check(post: Posterior, X, y, profiles: dict[str, np.ndarray], n_draws=40000,
                     inflate=1.5, seed=0) -> dict:
    """Сравнение интервалов Лапласа с точным апостериорным (выборка по значимости)."""
    rng = np.random.default_rng(seed)
    k = len(post.mean)
    prop_cov = post.cov * inflate ** 2
    L = np.linalg.cholesky(prop_cov)
    draws = post.mean + rng.standard_normal((n_draws, k)) @ L.T
    inv = np.linalg.inv(prop_cov)
    diff = draws - post.mean
    log_q = -0.5 * np.einsum("ij,jk,ik->i", diff, inv, diff)
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    Z = draws @ X.T
    log_lik = np.sum(y * Z - np.logaddexp(0.0, Z), axis=1)
    log_prior = -0.5 * np.sum(((draws - post.prior_mean) / post.prior_sd) ** 2, axis=1)
    log_w = log_lik + log_prior - log_q
    log_w -= log_w.max()
    w = np.exp(log_w)
    w /= w.sum()
    ess = 1.0 / np.sum(w ** 2)

    def wquantile(values, q):
        order = np.argsort(values)
        cw = np.cumsum(w[order])
        return float(values[order][np.searchsorted(cw, q)])

    out = {"ess": float(ess), "n_draws": n_draws, "coef_mean_is": (w @ draws).tolist(),
           "coef_q025_q50_q975": [[wquantile(draws[:, j], q) for q in (0.025, 0.5, 0.975)] for j in range(k)],
           "profiles": {}}
    for name, x in profiles.items():
        risk_draws = _sigmoid(draws @ x)
        eta, s = float(post.mean @ x), float(np.sqrt(x @ post.cov @ x))
        out["profiles"][name] = {
            "laplace": [float(_sigmoid(eta - 1.6448536 * s)), float(_sigmoid(eta)), float(_sigmoid(eta + 1.6448536 * s))],
            # медиана сопоставима с sigmoid(MAP)
            "exact_is": [wquantile(risk_draws, 0.05), wquantile(risk_draws, 0.5), wquantile(risk_draws, 0.95)],
        }
    return out


def predict(post: Posterior, X) -> np.ndarray:
    return _sigmoid(np.asarray(X, float) @ post.mean)
