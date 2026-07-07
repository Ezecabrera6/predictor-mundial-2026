"""Modelo de goles y goleadores.

- Goles esperados por partido con un Poisson derivado del rating Elo efectivo.
- Marcador entero mÃ¡s probable (para mostrar un resultado previsto por cruce).
- AtribuciÃ³n de goleadores con los datos que hay: jugadores que YA marcaron en el
  torneo (de los partidos jugados) + jugadores cargados en overrides.json, mÃ¡s un
  bucket "Otros" para el resto del plantel (el API no trae planteles completos).
- run_goldenboot: Monte Carlo del cuadro que acumula goles por jugador
  (goles ya hechos + goles futuros simulados) â†’ carrera por la Bota de Oro.
"""

from __future__ import annotations

import math
import random
import re

from .models import Bracket, ScorerRow, Team
from .scoring import compute_strength, win_probability
from .simulation import _ordered, _resolve

GOAL_TOTAL = 2.6        # goles promedio por partido (ambos equipos)
GOAL_SCALE = 320.0      # reparto de goles segÃºn diferencia de rating (suave)
_POS_W = {"FWD": 1.0, "MID": 0.5, "DEF": 0.16, "GK": 0.02}
_MIN_RE = re.compile(r"\s*\d+(\s*\+\s*\d+)?\s*['â€™]?\s*(\(.*?\))?\s*$")


def clean_scorer_name(s: str) -> str:
    """'J. QuiÃ±ones 9\'' -> 'J. QuiÃ±ones'."""
    if not s:
        return ""
    name = _MIN_RE.sub("", str(s)).strip()
    name = re.sub(r"\s*\((pen|p|og|e\.?c\.?)\)\s*$", "", name, flags=re.I).strip()
    return name


def expected_goals(r_home: float, r_away: float) -> tuple[float, float]:
    """Goles esperados (Poisson) de cada lado segÃºn los ratings."""
    share = 1.0 / (1.0 + 10 ** (-(r_home - r_away) / GOAL_SCALE))
    return GOAL_TOTAL * share, GOAL_TOTAL * (1.0 - share)


def _pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def likely_scoreline(lam_h: float, lam_a: float, cap: int = 6) -> tuple[int, int]:
    """Marcador entero mÃ¡s probable (argmax de Poisson x Poisson)."""
    best, bp = (0, 0), -1.0
    for gh in range(cap + 1):
        ph = _pmf(gh, lam_h)
        for ga in range(cap + 1):
            pr = ph * _pmf(ga, lam_a)
            if pr > bp:
                bp, best = pr, (gh, ga)
    return best


def _poisson(lam: float, rng: random.Random) -> int:
    L = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def real_goals_by_team(bracket: Bracket) -> dict[int, dict[str, int]]:
    """Goles ya marcados en el torneo, por equipo -> {jugador: goles}."""
    out: dict[int, dict[str, int]] = {}
    for m in bracket.matches:
        if not m.finished:
            continue
        for tid, scorers in (
            (m.home.team_id, m.home_scorers),
            (m.away.team_id, m.away_scorers),
        ):
            if not tid:
                continue
            for s in scorers:
                name = clean_scorer_name(s)
                if not name:
                    continue
                out.setdefault(tid, {})[name] = out.setdefault(tid, {}).get(name, 0) + 1
    return out


def team_scorer_weights(
    team: Team, real_by_team: dict[int, dict[str, int]]
) -> tuple[list[tuple[str, float]], float]:
    """Pesos de goleadores del equipo + peso del bucket 'Otros' (desconocidos)."""
    w: dict[str, float] = {}
    for name, g in real_by_team.get(team.id, {}).items():
        w[name] = w.get(name, 0.0) + 1.0 + 1.6 * g          # ya marcÃ³: candidato fuerte
    for p in team.players:
        if p.injured:
            continue
        pw = _POS_W.get(p.position, 0.4) * (0.35 + p.importance) * (0.4 + 0.6 * p.fitness)
        w[p.name] = w.get(p.name, 0.0) + pw
    known = sum(w.values())
    otros = max(1.0, 0.9 * known)                            # resto del plantel
    return list(w.items()), otros


def sample_scorer(
    items: list[tuple[str, float]], otros: float, rng: random.Random
) -> str | None:
    """Devuelve el nombre del goleador, o None si el gol va a 'Otros'."""
    total = sum(x for _, x in items) + otros
    r = rng.random() * total
    acc = 0.0
    for name, x in items:
        acc += x
        if r <= acc:
            return name
    return None


def likely_scorers(
    team: Team, real_by_team: dict[int, dict[str, int]], k: int = 2
) -> list[str]:
    """Los k goleadores mÃ¡s probables del equipo (para mostrar por partido)."""
    items, _ = team_scorer_weights(team, real_by_team)
    items.sort(key=lambda kv: kv[1], reverse=True)
    return [n for n, _w in items[:k]]


def run_goldenboot(
    bracket: Bracket, n: int, seed: int | None = None, cap: int = 8000
) -> list[ScorerRow]:
    """Goles esperados por jugador = goles ya hechos + goles futuros simulados."""
    rng = random.Random(seed)
    runs = max(1, min(n, cap))
    matches = _ordered(bracket.matches)
    strengths = {t.id: compute_strength(t).effective_rating for t in bracket.teams}
    team_by_id = {t.id: t for t in bracket.teams}
    real_by_team = real_goals_by_team(bracket)
    wcache = {t.id: team_scorer_weights(t, real_by_team) for t in bracket.teams}

    goals_now: dict[str, int] = {}
    name_team: dict[str, int] = {}
    for tid, d in real_by_team.items():
        for name, g in d.items():
            goals_now[name] = goals_now.get(name, 0) + g
            name_team.setdefault(name, tid)
    for t in bracket.teams:
        for p in t.players:
            name_team.setdefault(p.name, t.id)

    fut: dict[str, float] = {}
    for _ in range(runs):
        winners: dict[str, int] = {}
        losers: dict[str, int] = {}
        for m in matches:
            home = _resolve(m.home, winners, losers)
            away = _resolve(m.away, winners, losers)
            if home is None or away is None:
                continue
            if m.finished:
                w = m.winner_id
                if w is None:
                    hs, as_ = m.home_score or 0, m.away_score or 0
                    w = home if hs >= as_ else away
            else:
                ph = win_probability(strengths[home], strengths[away])
                w = home if rng.random() < ph else away
                lam_h, lam_a = expected_goals(strengths[home], strengths[away])
                for tid, lam in ((home, lam_h), (away, lam_a)):
                    items, otros = wcache[tid]
                    for _g in range(_poisson(lam, rng)):
                        nm = sample_scorer(items, otros, rng)
                        if nm:
                            fut[nm] = fut.get(nm, 0.0) + 1.0
                            name_team.setdefault(nm, tid)
            winners[m.id] = w
            losers[m.id] = away if w == home else home

    rows: list[ScorerRow] = []
    for nm in set(goals_now) | set(fut):
        t = team_by_id.get(name_team.get(nm))
        exp = goals_now.get(nm, 0) + fut.get(nm, 0.0) / runs
        rows.append(
            ScorerRow(
                name=nm,
                code=t.code if t else "",
                team=t.name if t else "",
                goals_now=goals_now.get(nm, 0),
                exp_goals=round(exp, 2),
            )
        )
    rows.sort(key=lambda r: (r.exp_goals, r.goals_now), reverse=True)
    return rows