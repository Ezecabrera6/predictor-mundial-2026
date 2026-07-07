"""Simulación Monte Carlo del cuadro de eliminación directa.

Respeta los partidos ya jugados (ganador fijo) y simula los pendientes miles de
veces según la probabilidad de victoria. Cuenta con qué frecuencia cada equipo
llega a cada ronda y gana la copa. Con `replay_from` se pueden "reabrir" rondas
ya jugadas (ej. simular todo el octavos desde cero).
"""

from __future__ import annotations

import random

from .models import Bracket, Match, MatchPrediction, SimulationResult, TeamStrength
from .scoring import compute_strength, win_probability

_ROUND_ORDER = {"r16": 0, "qf": 1, "sf": 2, "final": 3, "third": 3}


def _ordered(matches: list[Match]) -> list[Match]:
    # Excluye el partido por el 3er puesto de la cadena principal de avance,
    # pero lo deja al final para poder predecirlo si ambos equipos se conocen.
    return sorted(matches, key=lambda m: (_ROUND_ORDER[m.round], m.id))


def _resolve(slot, winners: dict[str, int], losers: dict[str, int]) -> int | None:
    if slot.team_id:
        return slot.team_id
    if slot.source is None:
        return None
    pool = winners if slot.take == "W" else losers
    return pool.get(slot.source)


def _simulate_once(
    matches: list[Match],
    strengths: dict[int, float],
    rng: random.Random,
    replay_from: str | None,
) -> tuple[dict[str, int], dict[str, int]]:
    winners: dict[str, int] = {}
    losers: dict[str, int] = {}
    # Sin replay_from: nada se reabre (orden imposible de alcanzar).
    replay_order = _ROUND_ORDER.get(replay_from, 999) if replay_from else 999

    for m in matches:
        home = _resolve(m.home, winners, losers)
        away = _resolve(m.away, winners, losers)
        if home is None or away is None:
            continue  # aún no resoluble (no debería pasar con orden correcto)

        force_open = _ROUND_ORDER[m.round] >= replay_order
        if m.finished and m.winner_id and not force_open:
            w = m.winner_id
        else:
            p = win_probability(strengths[home], strengths[away])
            w = home if rng.random() < p else away
        winners[m.id] = w
        losers[m.id] = away if w == home else home
    return winners, losers


def run_simulation(
    bracket: Bracket, n: int, seed: int | None = None, replay_from: str | None = None
) -> list[SimulationResult]:
    rng = random.Random(seed)
    matches = _ordered(bracket.matches)
    strengths = {t.id: compute_strength(t).effective_rating for t in bracket.teams}
    reach = {t.id: {"qf": 0, "sf": 0, "final": 0, "cup": 0} for t in bracket.teams}

    # Mapa ronda de un partido -> a qué "reach" contribuye ganarlo
    reach_key = {"r16": "qf", "qf": "sf", "sf": "final", "final": "cup"}

    for _ in range(n):
        winners, _losers = _simulate_once(matches, strengths, rng, replay_from)
        for m in matches:
            if m.round == "third":
                continue
            w = winners.get(m.id)
            if w is not None and w in reach:
                reach[w][reach_key[m.round]] += 1

    results = []
    for t in bracket.teams:
        c = reach[t.id]
        results.append(
            SimulationResult(
                team_id=t.id,
                name=t.name,
                code=t.code,
                flag=t.flag,
                reach_qf=round(c["qf"] / n, 4),
                reach_sf=round(c["sf"] / n, 4),
                reach_final=round(c["final"] / n, 4),
                win_cup=round(c["cup"] / n, 4),
                champion_pct=round(100 * c["cup"] / n, 2),
            )
        )
    results.sort(key=lambda r: r.win_cup, reverse=True)
    return results


def predict_known_matches(bracket: Bracket) -> list[MatchPrediction]:
    """Probabilidades de los partidos con ambos rivales ya definidos."""
    strengths = {t.id: compute_strength(t) for t in bracket.teams}
    by_id = {t.id: t for t in bracket.teams}
    preds: list[MatchPrediction] = []
    for m in _ordered(bracket.matches):
        h = m.home.team_id
        a = m.away.team_id
        if not h or not a or h not in by_id or a not in by_id:
            continue
        p = win_probability(strengths[h].effective_rating, strengths[a].effective_rating)
        home, away = by_id[h], by_id[a]
        played = (
            f"{m.home_score}-{m.away_score}"
            if m.finished and m.home_score is not None
            else None
        )
        preds.append(
            MatchPrediction(
                match_id=m.id,
                round=m.round,
                home=home.name,
                away=away.name,
                home_code=home.code,
                away_code=away.code,
                home_win_prob=round(p, 4),
                away_win_prob=round(1 - p, 4),
                favorite=home.name if p >= 0.5 else away.name,
                finished=m.finished,
                played_result=played,
            )
        )
    return preds


def team_strengths(bracket: Bracket) -> list[TeamStrength]:
    out = [compute_strength(t) for t in bracket.teams]
    out.sort(key=lambda s: s.effective_rating, reverse=True)
    return out
