"""Proveedor de datos real: API worldcup26.ir.

Trae equipos y partidos reales, calcula el Elo desde los resultados jugados,
deriva fatiga y forma del calendario, arma el cuadro de octavos→final y le
inyecta la capa manual de lesiones/moral (overrides.json).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import httpx

from ..calibration import evaluate
from ..config import settings
from ..elo import compute_elos
from ..morale import compute_morale
from ..models import Bracket, Match, Player, Slot, Team
from .provider import DataProvider

_HOSTS = {"USA", "MEX", "CAN"}
_ROUND_MAP = {"r16": "r16", "qf": "qf", "sf": "sf", "final": "final", "third": "third"}
_ROUND_ORDER = {"group": 0, "r32": 1, "r16": 2, "qf": 3, "sf": 4, "third": 5, "final": 6}


def _parse_date(s: str) -> datetime | None:
    try:
        return datetime.strptime(s.strip(), "%m/%d/%Y %H:%M")
    except (ValueError, AttributeError):
        return None


def _to_int(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _parse_scorers(raw) -> list[str]:
    """Convierte '{"J. Quiñones 9\'","R. Jiménez 67\'"}' en lista de goleadores."""
    if not raw or str(raw).strip().lower() in ("null", "{}", ""):
        return []
    s = str(raw)
    for ch in "{}":
        s = s.replace(ch, "")
    for q in ("“", "”", "“", "”", '"', "'"):
        s = s.replace(q, "")
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p and p.lower() != "null"]


def _fmt_scorers(home_raw, home_code, away_raw, away_code) -> str:
    h = _parse_scorers(home_raw)
    a = _parse_scorers(away_raw)
    chunks = []
    if h:
        chunks.append(f"{home_code}: " + ", ".join(h))
    if a:
        chunks.append(f"{away_code}: " + ", ".join(a))
    return " · ".join(chunks)


class ApiError(RuntimeError):
    pass


class WorldCup26Provider(DataProvider):
    def __init__(self) -> None:
        self.base = settings.wc_base_url.rstrip("/")
        self._client = httpx.Client(timeout=settings.http_timeout)

    # ---- Auth ----
    def _cached_token(self) -> str | None:
        p = Path(settings.wc_token_cache)
        if p.exists():
            tok = p.read_text(encoding="utf-8").strip()
            return tok or None
        return None

    def _save_token(self, token: str) -> None:
        Path(settings.wc_token_cache).write_text(token, encoding="utf-8")

    def _token_valid(self, token: str) -> bool:
        try:
            r = self._client.get(
                f"{self.base}/get/teams",
                headers={"Authorization": f"Bearer {token}"},
            )
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    def _login(self) -> str:
        """Autentica (o registra) y devuelve un token válido, cacheándolo."""
        cached = self._cached_token()
        if cached and self._token_valid(cached):
            return cached

        if not settings.wc_email or not settings.wc_password:
            raise ApiError(
                "Faltan credenciales WC_EMAIL / WC_PASSWORD en .env para usar el API."
            )

        # Intentar login; si el usuario no existe, registrarlo.
        r = self._client.post(
            f"{self.base}/auth/authenticate",
            json={"email": settings.wc_email, "password": settings.wc_password},
        )
        if r.status_code != 200:
            r = self._client.post(
                f"{self.base}/auth/register",
                json={
                    "name": settings.wc_name,
                    "email": settings.wc_email,
                    "password": settings.wc_password,
                },
            )
        if r.status_code != 200:
            raise ApiError(f"Login/registro falló ({r.status_code}): {r.text[:200]}")
        token = r.json().get("token")
        if not token:
            raise ApiError("La respuesta de auth no trae token.")
        self._save_token(token)
        return token

    def _get(self, path: str, token: str) -> dict:
        r = self._client.get(
            f"{self.base}{path}", headers={"Authorization": f"Bearer {token}"}
        )
        if r.status_code != 200:
            raise ApiError(f"GET {path} falló ({r.status_code})")
        return r.json()

    # ---- Overrides manuales (lesiones / moral) ----
    def _load_overrides(self) -> dict:
        p = Path(settings.overrides_file)
        if not p.exists():
            return {}
        return json.load(p.open(encoding="utf-8"))

    # ---- Construcción del bracket ----
    def get_bracket(self) -> Bracket:
        token = self._login()
        teams_raw = self._get("/get/teams", token)["teams"]
        games_raw = self._get("/get/games", token)["games"]
        overrides = self._load_overrides()

        team_by_id = {int(t["id"]): t for t in teams_raw}

        # Ordenar partidos cronológicamente (por ronda y fecha)
        def sort_key(g):
            d = _parse_date(g.get("local_date", "")) or datetime.max
            return (_ROUND_ORDER.get(g.get("type"), 9), d)

        games = sorted(games_raw, key=sort_key)

        finished = [g for g in games if str(g.get("finished")).upper() == "TRUE"]

        host_ids = {
            int(t["id"]) for t in teams_raw if t.get("fifa_code") in _HOSTS
        }

        # --- Calibración: ajustar parámetros con los partidos ya jugados ---
        # Orden en que cada equipo reaparece (para saber quién avanzó en empates
        # definidos por penales).
        appears_order: dict[int, int] = {}
        for g in games:
            order = _ROUND_ORDER.get(g.get("type"), 0)
            for tid in (_to_int(g.get("home_team_id")), _to_int(g.get("away_team_id"))):
                if tid and tid != 0:
                    appears_order[tid] = max(appears_order.get(tid, 0), order)

        fit_matches: list[dict] = []
        for g in finished:
            h, a = _to_int(g.get("home_team_id")), _to_int(g.get("away_team_id"))
            hs, as_ = _to_int(g.get("home_score")), _to_int(g.get("away_score"))
            if None in (h, a, hs, as_):
                continue
            typ = g.get("type")
            order = _ROUND_ORDER.get(typ, 0)
            advancer = None
            if typ in {"r32", "r16", "qf", "sf", "final"}:
                if hs != as_:
                    advancer = h if hs > as_ else a
                else:  # empate → avanzó el que reaparece en ronda posterior
                    for tid in (h, a):
                        if appears_order.get(tid, 0) > order:
                            advancer = tid
            th, ta = team_by_id.get(h, {}), team_by_id.get(a, {})
            scr = _fmt_scorers(g.get("home_scorers"), th.get("fifa_code", ""),
                               g.get("away_scorers"), ta.get("fifa_code", ""))
            fit_matches.append({
                "home": h, "away": a, "hs": hs, "as": as_, "type": typ,
                "home_name": th.get("name_en", str(h)),
                "away_name": ta.get("name_en", str(a)),
                "home_code": th.get("fifa_code", ""),
                "away_code": ta.get("fifa_code", ""),
                "score": f"{hs}-{as_}",
                "scorers": scr,
                "advancer": advancer,
                "advancer_name": (
                    team_by_id.get(advancer, {}).get("name_en", "")
                    if advancer else ""
                ),
            })

        # --- Elo desde todos los partidos jugados ---
        elo_matches: list[tuple[int, int, int, int]] = []
        for g in finished:
            h, a = _to_int(g.get("home_team_id")), _to_int(g.get("away_team_id"))
            hs, as_ = _to_int(g.get("home_score")), _to_int(g.get("away_score"))
            if None not in (h, a, hs, as_):
                elo_matches.append((h, a, hs, as_))
        elos = compute_elos(list(team_by_id), elo_matches)

        # --- Fatiga y forma por equipo desde el calendario real ---
        ref_now = max(
            (_parse_date(g["local_date"]) for g in finished if _parse_date(g.get("local_date", ""))),
            default=datetime(2026, 7, 6),
        )
        last_played: dict[int, datetime] = {}
        matches_30: dict[int, int] = {}
        form: dict[int, list[str]] = {}
        goals: dict[int, list[tuple[int, int]]] = {}  # (gf, ga) cronológico → moral
        for g in finished:
            d = _parse_date(g.get("local_date", ""))
            if d is None:
                continue
            h, a = _to_int(g.get("home_team_id")), _to_int(g.get("away_team_id"))
            hs, as_ = _to_int(g.get("home_score")), _to_int(g.get("away_score"))
            for tid, gf, ga in ((h, hs, as_), (a, as_, hs)):
                if tid is None:
                    continue
                if tid not in last_played or d > last_played[tid]:
                    last_played[tid] = d
                if d >= ref_now - timedelta(days=30):
                    matches_30[tid] = matches_30.get(tid, 0) + 1
                if gf is not None and ga is not None:
                    res = "W" if gf > ga else ("L" if gf < ga else "D")
                    form.setdefault(tid, []).append(res)
                    goals.setdefault(tid, []).append((gf, ga))

        # Próximo partido programado por equipo (para días de descanso)
        next_date: dict[int, datetime] = {}
        for g in games:
            if str(g.get("finished")).upper() == "TRUE":
                continue
            d = _parse_date(g.get("local_date", ""))
            if d is None:
                continue
            for tid in (_to_int(g.get("home_team_id")), _to_int(g.get("away_team_id"))):
                if tid and tid != 0 and (tid not in next_date or d < next_date[tid]):
                    next_date[tid] = d

        # --- Equipos que llegaron a octavos (participantes de r16) ---
        r16_games = [g for g in games if g.get("type") == "r16"]
        alive_ids: list[int] = []
        for g in r16_games:
            for tid in (_to_int(g.get("home_team_id")), _to_int(g.get("away_team_id"))):
                if tid and tid != 0 and tid not in alive_ids:
                    alive_ids.append(tid)

        teams: list[Team] = []
        for tid in alive_ids:
            raw = team_by_id.get(tid, {})
            code = raw.get("fifa_code", "")
            ov = overrides.get(code, {})
            rest = 4
            if tid in last_played:
                end = next_date.get(tid, ref_now)
                rest = max(0, (end - last_played[tid]).days)
            # Moral CALCULADA de los resultados reales (+ ajuste manual opcional).
            morale = compute_morale(goals.get(tid, []))
            morale = max(-1.0, min(1.0, morale + ov.get("morale_nudge", 0.0)))
            teams.append(
                Team(
                    id=tid,
                    name=raw.get("name_en", f"Team {tid}"),
                    code=code,
                    flag=raw.get("flag", ""),
                    is_host=code in _HOSTS,
                    base_rating=elos.get(tid, settings.elo_start),
                    rest_days=rest,
                    matches_last_30=matches_30.get(tid, 4),
                    recent_form=form.get(tid, [])[-4:],
                    players=[Player(**p) for p in ov.get("players", [])],
                    morale=morale,
                    note=ov.get("note", ""),
                )
            )

        # --- Calibración inicial: qué tan bien reproduce lo ya jugado ---
        # Valor por equipo = Elo base (para TODOS los equipos, incluidos los ya
        # eliminados que aparecen en partidos pasados).
        base_value = {
            tid: elos.get(tid, settings.elo_start)
            for m in fit_matches
            for tid in (m["home"], m["away"])
        }
        ev = evaluate(fit_matches, base_value, settings.elo_scale)
        calib = {
            "fitted": False,
            "initial_accuracy": ev["accuracy"],
            "accuracy": ev["accuracy"],
            "correct": ev["correct"],
            "total": ev["total"],
            "logloss": ev["logloss"],
            "records": ev["records"],
            "params": {"elo_scale": settings.elo_scale},
            "base_value": {str(k): v for k, v in base_value.items()},
            "fit_matches": fit_matches,
            "corrections": [],
        }

        # --- Partidos del cuadro (octavos en adelante) ---
        matches = self._build_matches(games, finished)
        return Bracket(teams=teams, matches=matches, calibration=calib)

    def _build_matches(self, games: list[dict], finished: list[dict]) -> list[Match]:
        # ids que reaparecen en rondas posteriores (para resolver empates a penales)
        appears_later: dict[int, int] = {}
        for g in games:
            order = _ROUND_ORDER.get(g.get("type"), 0)
            for tid in (_to_int(g.get("home_team_id")), _to_int(g.get("away_team_id"))):
                if tid and tid != 0:
                    appears_later[tid] = max(appears_later.get(tid, 0), order)

        matches: list[Match] = []
        for g in games:
            typ = g.get("type")
            if typ not in _ROUND_MAP:
                continue
            gid = str(g["id"])
            order = _ROUND_ORDER[typ]
            home = self._slot(g, "home")
            away = self._slot(g, "away")
            fin = str(g.get("finished")).upper() == "TRUE"
            hs, as_ = _to_int(g.get("home_score")), _to_int(g.get("away_score"))
            winner = None
            if fin and home.team_id and away.team_id:
                if hs is not None and as_ is not None and hs != as_:
                    winner = home.team_id if hs > as_ else away.team_id
                else:  # empate → avanzó el que reaparece en ronda posterior
                    for tid in (home.team_id, away.team_id):
                        if appears_later.get(tid, 0) > order:
                            winner = tid
            matches.append(
                Match(
                    id=gid,
                    round=_ROUND_MAP[typ],
                    home=home,
                    away=away,
                    finished=fin,
                    winner_id=winner,
                    home_score=hs,
                    away_score=as_,
                    home_scorers=_parse_scorers(g.get("home_scorers")),
                    away_scorers=_parse_scorers(g.get("away_scorers")),
                    date=g.get("local_date", ""),
                )
            )
        return matches

    def _slot(self, g: dict, side: str) -> Slot:
        tid = _to_int(g.get(f"{side}_team_id"))
        if tid and tid != 0:
            return Slot(team_id=tid)
        label = g.get(f"{side}_team_label", "") or ""
        take = "L" if label.lower().startswith("loser") else "W"
        num = "".join(ch for ch in label if ch.isdigit())
        return Slot(source=num or None, take=take)
