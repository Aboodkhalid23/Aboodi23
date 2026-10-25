"""CMA-ES: covariance matrix adaptation evolution strategy, (μ/μ_w, λ) with rank-one and rank-μ updates and
cumulative step-size adaptation (Hansen, "The CMA Evolution Strategy: A Tutorial", 2016).

Why this optimizer: the objective here (how far a predicted camera or tension curve is from the reference) has no
gradient — peaks appear and disappear, fits switch models — and is cheap but noisy-ish. CMA-ES needs only rankings of
candidates, learns the correlations between parameters (start time and duration trade off against each other), and
works well for 5–60 dimensions.

Search happens in the unit box [0, 1]^n. Candidates outside it are evaluated at their projection onto the box plus a
quadratic penalty (the boundary handling of Hansen's reference code), so the distribution stays unbiased.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np


class CMAES:
    def __init__(self, x0: np.ndarray, sigma0: float = 0.2, popsize: int | None = None, seed: int = 0):
        self.n = n = len(x0)
        self.mean = np.asarray(x0, float).copy()
        self.sigma = float(sigma0)
        self.rng = np.random.default_rng(seed)
        self.lam = lam = popsize or 4 + int(3 * math.log(n))
        self.mu = mu = lam // 2
        w = math.log(mu + 0.5) - np.log(np.arange(1, mu + 1))
        self.w = w / w.sum()
        self.mueff = mueff = 1 / float(np.sum(self.w ** 2))
        self.cc = (4 + mueff / n) / (n + 4 + 2 * mueff / n)
        self.cs = (mueff + 2) / (n + mueff + 5)
        self.c1 = 2 / ((n + 1.3) ** 2 + mueff)
        self.cmu = min(1 - self.c1, 2 * (mueff - 2 + 1 / mueff) / ((n + 2) ** 2 + mueff))
        self.damps = 1 + 2 * max(0.0, math.sqrt((mueff - 1) / (n + 1)) - 1) + self.cs
        self.chiN = math.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n))
        self.pc, self.ps = np.zeros(n), np.zeros(n)
        self.B, self.D = np.eye(n), np.ones(n)
        self.C, self.invsqrtC = np.eye(n), np.eye(n)
        self.evals, self._eigen_at = 0, 0

    def ask(self) -> np.ndarray:
        z = self.rng.standard_normal((self.lam, self.n))
        return self.mean + self.sigma * (z * self.D) @ self.B.T

    def tell(self, X: np.ndarray, f: np.ndarray):
        n, lam, mu = self.n, self.lam, self.mu
        self.evals += lam
        order = np.argsort(f)
        Xs = X[order[:mu]]
        old = self.mean
        self.mean = self.w @ Xs
        yw = (self.mean - old) / self.sigma
        self.ps = (1 - self.cs) * self.ps + math.sqrt(self.cs * (2 - self.cs) * self.mueff) * (self.invsqrtC @ yw)
        hsig = np.linalg.norm(self.ps) / math.sqrt(1 - (1 - self.cs) ** (2 * self.evals / lam)) / self.chiN < 1.4 + 2 / (n + 1)
        self.pc = (1 - self.cc) * self.pc + hsig * math.sqrt(self.cc * (2 - self.cc) * self.mueff) * yw
        art = (Xs - old) / self.sigma
        self.C = ((1 - self.c1 - self.cmu) * self.C
                  + self.c1 * (np.outer(self.pc, self.pc) + (1 - hsig) * self.cc * (2 - self.cc) * self.C)
                  + self.cmu * (art.T * self.w) @ art)
        self.sigma *= math.exp((self.cs / self.damps) * (np.linalg.norm(self.ps) / self.chiN - 1))
        if self.evals - self._eigen_at > lam / (self.c1 + self.cmu) / n / 10:   # O(n²) per generation on average
            self._eigen_at = self.evals
            self.C = np.triu(self.C) + np.triu(self.C, 1).T
            d2, self.B = np.linalg.eigh(self.C)
            self.D = np.sqrt(np.maximum(d2, 1e-20))
            self.invsqrtC = (self.B / self.D) @ self.B.T


@dataclass
class Result:
    x: np.ndarray
    f: float
    evals: int
    history: list[float] = field(default_factory=list)   # best value after each generation


def minimize(f: Callable[[np.ndarray], float], x0: np.ndarray, sigma0: float = 0.2, budget: int = 400, seed: int = 0,
             popsize: int | None = None, tol: float = 1e-9) -> Result:
    """Minimise f over the unit box [0, 1]^n starting from x0 (in the box). Deterministic for a given seed."""
    x0 = np.clip(np.asarray(x0, float), 0, 1)
    if len(x0) == 0:
        return Result(x0, float(f(x0)), 1)
    es = CMAES(x0, sigma0, popsize, seed)
    best_x, best_f = x0, float(f(x0))
    hist, evals = [best_f], 1
    while evals + es.lam <= budget:
        X = es.ask()
        vals = np.empty(len(X))
        for i, x in enumerate(X):
            xc = np.clip(x, 0, 1)
            fx = float(f(xc))
            if fx < best_f:
                best_x, best_f = xc, fx
            vals[i] = fx + 1e3 * float(np.sum((x - xc) ** 2))   # outside the box: evaluated on it, penalised by the distance
        evals += len(X)
        es.tell(X, vals)
        hist.append(best_f)
        if es.sigma * float(es.D.max()) < tol:
            break
    return Result(best_x, best_f, evals, hist)
