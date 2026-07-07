"""Modelos de dominio (Pydantic)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Round = Literal["r16", "qf", "sf", "final", "third"]


class Player(BaseModel):
    name: str
    position: Literal["GK", "DEF", "MID", "FWD"] = "MID"
    importance: float = Field(0.5, ge=0.0, le=1.0)  # 0 suplente, 1 figura
    fitness: float = Field(1.0, ge=0.0, le=1.0)      # 1 pleno, 0 recién vuelto
    injured: bool = False


class Team(BaseModel):
    id: int
    name: str
    code: str = ""                      # fifa_code, ej. "ARG"
    flag: str = ""                      # URL de bandera
    is_host: bool = False

    # Fuerza base en escala Elo (~1300-1800), calculada de resultados reales
    base_rating: float = 1500.0

    # Factores de contexto (fatiga/forma derivados del calendario real)
    rest_days: int = 4
    matches_last_30: int = 4
    recent_form: list[Literal["W", "D", "L"]] = Field(default_factory=list)

    # Capa manual (overrides.json): lesiones y estado anímico
    players: list[Player] = Field(default_factory=list)
    morale: float = Field(0.0, ge=-1.0, le=1.0)  # -1 crisis, +1 euforia
    note: str = ""

    # Corrección aprendida por calibración (ajuste de rating por equipo)
    correction: float = 0.0


class Slot(BaseModel):
    """Un lado de un partido: equipo fijo, o ganador/perdedor de otro cruce."""

    team_id: int | None = None
    source: str | None = None                 # id del partido feeder
    take: Literal["W", "L"] = "W"             # tomar ganador o perdedor


class Match(BaseModel):
    id: str
    round: Round
    home: Slot
    away: Slot
    finished: bool = False
    winner_id: int | None = None
    home_score: int | None = None
    away_score: int | None = None
    home_scorers: list[str] = Field(default_factory=list)
    away_scorers: list[str] = Field(default_factory=list)
    date: str = ""


class Bracket(BaseModel):
    teams: list[Team]
    matches: list[Match]
    calibration: dict = Field(default_factory=dict)


# --- Salidas del modelo ---


class TeamStrength(BaseModel):
    team_id: int
    name: str
    code: str
    flag: str = ""
    base_rating: float
    effective_rating: float
    injury_penalty: float
    fatigue_penalty: float
    form_adjustment: float
    morale_adjustment: float
    host_bonus: float
    calibration_adj: float = 0.0
    injured_players: list[str] = Field(default_factory=list)


class MatchPrediction(BaseModel):
    match_id: str
    round: str
    home: str
    away: str
    home_code: str = ""
    away_code: str = ""
    home_win_prob: float
    away_win_prob: float
    favorite: str
    finished: bool = False
    played_result: str | None = None          # si ya se jugó, "2-1"


class SimulationResult(BaseModel):
    team_id: int
    name: str
    code: str
    flag: str = ""
    reach_qf: float
    reach_sf: float
    reach_final: float
    win_cup: float
    champion_pct: float                        # alias legible de win_cup en %
