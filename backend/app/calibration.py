"""Calibración contra los partidos YA jugados.

Dos piezas:
1) `evaluate`: mide cuántos resultados finalizados reproduce el modelo actual
   (el favorito por fuerza efectiva vs. quién avanzó de verdad).
2) `fit_corrections`: APRENDIZAJE por equipo. Cuando el modelo falla un partido
   ya jugado, sube el rating del que avanzó y baja el del que predijo mal, y
   repite hasta acertar todos los resultados (o hasta el tope de iteraciones).
   Así "se calibra hasta pegarle al 100%".

Nota honesta: forzar el 100% ajusta también upsets y definiciones por penales
(que son azarosas), así que es un ajuste fino a lo ya ocurrido, no una garantía
sobre el futuro.
"""

from __future__ import annotations

import math


def _win_prob(diff: float, scale: float) -> float:
    return 1.0 / (1.0 + math.pow(10.0, -diff / scale))


def evaluate(
    matches: list[dict],
    value: dict[int, float],
    scale: float,
) -> dict:
    """Califica los partidos de eliminación ya jugados con las fuerzas `value`.

    `matches`: dicts con home, away (ids), advancer (id o None) y metadatos.
    """
    correct = 0
    total = 0
    logloss = 0.0
    records: list[dict] = []
    for m in matches:
        adv = m.get("advancer")
        if adv is None:
            continue
        h, a = m["home"], m["away"]
        vh, va = value.get(h, 1500.0), value.get(a, 1500.0)
        p_home = _win_prob(vh - va, scale)
        pred_home = vh >= va
        home_adv = adv == h
        ok = pred_home == home_adv
        correct += int(ok)
        total += 1
        o = 1.0 if home_adv else 0.0
        p = min(max(p_home, 1e-6), 1 - 1e-6)
        logloss += -(o * math.log(p) + (1 - o) * math.log(1 - p))
        records.append(
            {
                "round": m["type"],
                "home": m["home_name"],
                "away": m["away_name"],
                "home_code": m.get("home_code", ""),
                "away_code": m.get("away_code", ""),
                "p_home": round(p_home, 3),
                "predicted": m["home_name"] if pred_home else m["away_name"],
                "actual": m["advancer_name"],
                "score": m.get("score", ""),
                "scorers": m.get("scorers", ""),
                "ok": ok,
            }
        )
    return {
        "accuracy": round(correct / total, 4) if total else 0.0,
        "correct": correct,
        "total": total,
        "logloss": round(logloss / total, 4) if total else 0.0,
        "records": records,
    }


def fit_corrections(
    matches: list[dict],
    base_value: dict[int, float],
    scale: float,
    step: float = 6.0,
    max_iter: int = 600,
    target: float = 1.0,
) -> dict:
    """Ajusta un corrector de rating por equipo hasta reproducir los resultados.

    Devuelve las correcciones, la precisión final y el historial de precisión
    por iteración (para animar la subida en la UI).
    """
    corr: dict[int, float] = {tid: 0.0 for tid in base_value}
    graded = [m for m in matches if m.get("advancer") is not None]

    def val(tid: int) -> float:
        return base_value.get(tid, 1500.0) + corr.get(tid, 0.0)

    def accuracy() -> float:
        if not graded:
            return 1.0
        ok = 0
        for m in graded:
            pred = m["home"] if val(m["home"]) >= val(m["away"]) else m["away"]
            ok += pred == m["advancer"]
        return ok / len(graded)

    history: list[float] = []
    iterations = 0
    for it in range(max_iter):
        acc = accuracy()
        history.append(round(acc, 4))
        if acc >= target:
            break
        iterations = it + 1
        # una pasada de corrección estilo perceptrón
        for m in graded:
            adv = m["advancer"]
            h, a = m["home"], m["away"]
            loser = a if adv == h else h
            if val(adv) < val(loser):
                corr[adv] += step
                corr[loser] -= step

    final_acc = accuracy()
    history.append(round(final_acc, 4))
    # downsample para la animación (máx ~40 puntos)
    if len(history) > 40:
        stepd = len(history) / 40
        history = [history[int(i * stepd)] for i in range(40)] + [history[-1]]

    return {
        "corrections": {tid: round(v, 1) for tid, v in corr.items() if abs(v) > 0.05},
        "accuracy": round(final_acc, 4),
        "iterations": iterations,
        "history": history,
        "step": step,
    }
