"""Modelo de puntaje ponderado (escala Elo).

Fuerza efectiva = rating base (Elo de resultados reales)
                  - lesiones - cansancio + forma + moral + local.
La probabilidad de victoria sale de la diferencia de fuerzas (curva logística).
"""

from __future__ import annotations

import math

from .config import settings
from .models import Team, TeamStrength


def injury_penalty(team: Team) -> float:
    """Penalización por lesionados y jugadores con fitness bajo.

    Suma la 'importancia' de cada lesionado + el déficit de fitness de los
    que juegan tocados. Satura para que ninguna baja sola hunda al equipo.
    """
    lost = 0.0
    for p in team.players:
        if p.injured:
            lost += p.importance
        else:
            lost += p.importance * (1.0 - p.fitness) * 0.5
    saturation = 1.0 - math.exp(-lost)   # 0..1, crece y satura
    return settings.injury_weight * saturation


def fatigue_penalty(team: Team) -> float:
    """Cansancio: pocos días de descanso + muchos partidos recientes."""
    rest_factor = max(0.0, (5 - team.rest_days)) / 3.0          # 0..1
    load_factor = max(0.0, (team.matches_last_30 - 4)) / 4.0    # 0..1+
    combined = min(1.0, 0.6 * rest_factor + 0.4 * min(load_factor, 1.0))
    return settings.fatigue_weight * combined


def form_adjustment(team: Team) -> float:
    """Forma reciente: W=+1, D=0, L=-1, promedio ponderado y normalizado."""
    if not team.recent_form:
        return 0.0
    scores = {"W": 1.0, "D": 0.0, "L": -1.0}
    avg = sum(scores[r] for r in team.recent_form) / len(team.recent_form)
    return settings.form_weight * avg


def morale_adjustment(team: Team) -> float:
    return settings.morale_weight * team.morale


def compute_strength(team: Team) -> TeamStrength:
    inj = injury_penalty(team)
    fat = fatigue_penalty(team)
    frm = form_adjustment(team)
    mor = morale_adjustment(team)
    host = settings.host_bonus if team.is_host else 0.0

    effective = team.base_rating + team.correction - inj - fat + frm + mor + host

    return TeamStrength(
        team_id=team.id,
        name=team.name,
        code=team.code,
        flag=team.flag,
        base_rating=round(team.base_rating, 1),
        effective_rating=round(effective, 1),
        injury_penalty=round(inj, 1),
        fatigue_penalty=round(fat, 1),
        form_adjustment=round(frm, 1),
        morale_adjustment=round(mor, 1),
        host_bonus=round(host, 1),
        calibration_adj=round(team.correction, 1),
        injured_players=[p.name for p in team.players if p.injured],
    )


def win_probability(strength_a: float, strength_b: float) -> float:
    """Prob. de que A le gane a B según la diferencia de fuerza (logística Elo)."""
    diff = strength_a - strength_b
    return 1.0 / (1.0 + math.pow(10.0, -diff / settings.elo_scale))
