"""Cálculo de rating Elo replayando los partidos ya jugados.

Todos arrancan en `elo_start`. Por cada partido terminado se actualiza el Elo
de ambos equipos según el resultado y el margen de goles. Así la fuerza base
sale 100% de resultados reales del torneo.
"""

from __future__ import annotations

import math

from .config import settings


def _expected(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + math.pow(10.0, (elo_b - elo_a) / 400.0))


def _margin_multiplier(goal_diff: int) -> float:
    """Ganar por más goles mueve más el Elo (idea del modelo Elo de fútbol)."""
    gd = abs(goal_diff)
    if gd <= 1:
        return 1.0
    return 1.0 + math.log(gd) * 0.6


def compute_elos(
    team_ids: list[int],
    finished_matches: list[tuple[int, int, int, int]],
) -> dict[int, float]:
    """
    finished_matches: lista de (home_id, away_id, home_score, away_score)
    en orden cronológico. Devuelve {team_id: elo}.
    """
    elo = {tid: settings.elo_start for tid in team_ids}

    for home, away, hs, as_ in finished_matches:
        if home not in elo or away not in elo:
            continue
        exp_home = _expected(elo[home], elo[away])
        if hs > as_:
            score_home = 1.0
        elif hs < as_:
            score_home = 0.0
        else:
            score_home = 0.5
        k = settings.elo_k * _margin_multiplier(hs - as_)
        delta = k * (score_home - exp_home)
        elo[home] += delta
        elo[away] -= delta

    return {tid: round(v, 1) for tid, v in elo.items()}
