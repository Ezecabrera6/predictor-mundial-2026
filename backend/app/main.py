"""API FastAPI del predictor del Mundial."""

from __future__ import annotations

import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import settings
from .calibration import evaluate, fit_corrections
from .data import get_provider
from .models import Bracket
from .simulation import (
    predict_known_matches,
    run_simulation,
    team_strengths,
)

app = FastAPI(title="Predictor Mundial 2026", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache: dict = {"bracket": None, "ts": 0.0}


def _bracket(refresh: bool = False) -> Bracket:
    """Devuelve el cuadro cacheado, refrescándolo si venció el TTL o se pide."""
    age = time.time() - _cache["ts"]
    if refresh or _cache["bracket"] is None or age > settings.cache_ttl:
        try:
            _cache["bracket"] = get_provider().get_bracket()
            _cache["ts"] = time.time()
        except Exception as e:  # noqa: BLE001
            if _cache["bracket"] is not None:
                return _cache["bracket"]  # si falla el refresh, servimos lo último
            raise HTTPException(status_code=502, detail=f"No se pudo cargar datos: {e}")
    return _cache["bracket"]


def _team_map(bracket: Bracket) -> dict[int, dict]:
    return {
        t.id: {"id": t.id, "name": t.name, "code": t.code, "flag": t.flag}
        for t in bracket.teams
    }


def _serialize_match(m, teams: dict[int, dict]) -> dict:
    def side(slot):
        if slot.team_id and slot.team_id in teams:
            return teams[slot.team_id]
        if slot.source:
            label = "Ganador" if slot.take == "W" else "Perdedor"
            return {"name": f"{label} {slot.source}", "code": "", "flag": "", "id": None}
        return {"name": "?", "code": "", "flag": "", "id": None}

    return {
        "id": m.id,
        "round": m.round,
        "home": side(m.home),
        "away": side(m.away),
        "finished": m.finished,
        "winner_id": m.winner_id,
        "score": (
            f"{m.home_score}-{m.away_score}"
            if m.finished and m.home_score is not None
            else None
        ),
        "home_scorers": m.home_scorers,
        "away_scorers": m.away_scorers,
        "date": m.date,
    }


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__, "data_source": settings.data_source}


@app.get("/api/bracket")
def bracket(refresh: bool = False) -> dict:
    b = _bracket(refresh)
    teams = _team_map(b)
    return {
        "teams": list(teams.values()),
        "matches": [_serialize_match(m, teams) for m in b.matches],
    }


@app.get("/api/calibration")
def calibration(refresh: bool = False) -> dict:
    return _bracket(refresh).calibration


@app.get("/api/recalibrate")
def recalibrate(
    step: float = Query(default=6.0, ge=0.5, le=100.0),
    max_iter: int = Query(default=600, ge=1, le=5000),
    target: float = Query(default=1.0, ge=0.0, le=1.0),
) -> dict:
    """Aprende correcciones de rating por equipo hasta reproducir lo ya jugado.

    Aplica las correcciones al modelo en vivo (afecta predicciones y simulación).
    """
    b = _bracket()
    cal = b.calibration
    if not cal.get("fit_matches"):
        raise HTTPException(status_code=400, detail="Calibración no disponible (modo sample).")

    base_value = {int(k): v for k, v in cal["base_value"].items()}
    fit_matches = cal["fit_matches"]
    scale = cal["params"]["elo_scale"]

    fit = fit_corrections(fit_matches, base_value, scale, step, max_iter, target)
    corr = fit["corrections"]

    for t in b.teams:
        t.correction = corr.get(t.id, 0.0)

    new_value = {tid: base_value[tid] + corr.get(tid, 0.0) for tid in base_value}
    ev = evaluate(fit_matches, new_value, scale)

    adj = [
        {"code": t.code, "name": t.name, "adj": round(t.correction, 1)}
        for t in b.teams
        if abs(t.correction) > 0.05
    ]
    adj.sort(key=lambda x: -abs(x["adj"]))

    cal.update(
        {
            "fitted": True,
            "accuracy": ev["accuracy"],
            "correct": ev["correct"],
            "total": ev["total"],
            "logloss": ev["logloss"],
            "records": ev["records"],
            "history": fit["history"],
            "iterations": fit["iterations"],
            "corrections": adj,
        }
    )
    return {
        "initial_accuracy": cal.get("initial_accuracy", 0.0),
        "accuracy": ev["accuracy"],
        "correct": ev["correct"],
        "total": ev["total"],
        "history": fit["history"],
        "iterations": fit["iterations"],
        "corrections": adj,
    }


@app.get("/api/strengths")
def strengths(refresh: bool = False) -> list:
    return [s.model_dump() for s in team_strengths(_bracket(refresh))]


@app.get("/api/predictions")
def predictions(refresh: bool = False) -> list:
    return [p.model_dump() for p in predict_known_matches(_bracket(refresh))]


@app.get("/api/simulate")
def simulate(
    n: int = Query(default=settings.simulations, ge=100, le=200_000),
    replay_from: str | None = Query(default=None),
    seed: int | None = Query(default=None),
    refresh: bool = False,
) -> list:
    b = _bracket(refresh)
    return [r.model_dump() for r in run_simulation(b, n, seed=seed, replay_from=replay_from)]


@app.get("/api/overview")
def overview(
    n: int = Query(default=settings.simulations, ge=100, le=200_000),
    replay_from: str | None = Query(default=None),
    refresh: bool = False,
) -> dict:
    """Todo en una llamada, para el frontend."""
    b = _bracket(refresh)
    teams = _team_map(b)
    return {
        "meta": {
            "data_source": settings.data_source,
            "simulations": n,
            "updated_ts": _cache["ts"],
        },
        "calibration": b.calibration,
        "teams": list(teams.values()),
        "matches": [_serialize_match(m, teams) for m in b.matches],
        "strengths": [s.model_dump() for s in team_strengths(b)],
        "predictions": [p.model_dump() for p in predict_known_matches(b)],
        "simulation": [
            r.model_dump() for r in run_simulation(b, n, replay_from=replay_from)
        ],
    }
