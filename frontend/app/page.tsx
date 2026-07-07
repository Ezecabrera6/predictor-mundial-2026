"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchOverview,
  recalibrate,
  type Overview,
  type TeamRef,
} from "../lib/api";
import { playTournament, type PlayedMatch, type Playthrough } from "../lib/sim";
import BattleArena, { type Phase } from "../components/BattleArena";
import Bracket from "../components/Bracket";
import Calibration from "../components/Calibration";
import ChampionOdds from "../components/ChampionOdds";
import StrengthTable from "../components/StrengthTable";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function Page() {
  const [ov, setOv] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"live" | "fresh">("live");
  const [nSims, setNSims] = useState(20000);
  const [fast, setFast] = useState(false);

  const [played, setPlayed] = useState<Map<string, PlayedMatch>>(new Map());
  const [current, setCurrent] = useState<PlayedMatch | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [champion, setChampion] = useState<TeamRef | null>(null);
  const [matchIndex, setMatchIndex] = useState(0);
  const [total, setTotal] = useState(0);
  const [running, setRunning] = useState(false);
  const abort = useRef(false);
  const ptRef = useRef<Playthrough | null>(null);

  const [calibPct, setCalibPct] = useState(0);
  const [calibBusy, setCalibBusy] = useState(false);
  const [fightDur, setFightDur] = useState(2000);
  const [refreshing, setRefreshing] = useState(false);

  const refreshData = async () => {
    if (refreshing || running) return;
    setRefreshing(true);
    await load(true);
    setRefreshing(false);
  };

  const championRef = (id: number | null): TeamRef | null => {
    const s = ov?.strengths.find((x) => x.team_id === id);
    return s ? { id: s.team_id, name: s.name, code: s.code, flag: s.flag } : null;
  };

  const load = useCallback(async (refresh = false) => {
    setError(null);
    try {
      const data = await fetchOverview(
        nSims,
        mode === "fresh" ? "r16" : undefined,
        refresh
      );
      setOv(data);
      if (data.calibration?.accuracy != null) {
        setCalibPct(data.calibration.accuracy * 100);
      }
    } catch (e: any) {
      setError(
        `No se pudo conectar con el backend (${e?.message ?? e}). ¿Está corriendo en el puerto 8000?`
      );
    }
  }, [nSims, mode]);

  useEffect(() => {
    load();
  }, [load]);

  const calibrate = async () => {
    if (!ov || calibBusy) return;
    setCalibBusy(true);
    try {
      const res = await recalibrate(1.0);
      // animar la precisión subiendo según el historial de aprendizaje
      for (const acc of res.history) {
        setCalibPct(acc * 100);
        await sleep(140);
      }
      setCalibPct(res.accuracy * 100);
      // recargar el modelo ya ajustado (predicciones y simulación cambian)
      await load();
    } catch {
      /* noop */
    }
    setCalibBusy(false);
  };

  const reset = () => {
    abort.current = true;
    setPlayed(new Map());
    setCurrent(null);
    setChampion(null);
    setPhase("idle");
    setMatchIndex(0);
    setRunning(false);
  };

  const simulate = async () => {
    if (!ov || running) return;
    abort.current = false;
    setRunning(true);
    setChampion(null);
    setCurrent(null);
    setPhase("idle");
    const acc = new Map<string, PlayedMatch>();
    setPlayed(acc);

    const pt = playTournament(ov.matches, ov.strengths, mode === "live");
    ptRef.current = pt;
    setTotal(pt.order.length);

    const fightMs = fast ? 1000 : 2000;
    const decideMs = fast ? 650 : 1150;
    setFightDur(fightMs);

    for (let i = 0; i < pt.order.length; i++) {
      if (abort.current) break;
      const pm = pt.order[i];
      setCurrent(pm);
      setMatchIndex(i);
      setPhase("fighting");
      await sleep(fightMs);
      if (abort.current) break;
      setPhase("decided");
      acc.set(pm.id, pm);
      setPlayed(new Map(acc));
      await sleep(decideMs);
    }

    if (!abort.current) {
      pt.order.forEach((pm) => acc.set(pm.id, pm));
      setPlayed(new Map(acc));
      setChampion(championRef(pt.championId));
      setCurrent(null);
    }
    setRunning(false);
  };

  // Termina instantáneamente la corrida en curso (o genera una si no hay).
  const skip = () => {
    if (!ov) return;
    abort.current = true;
    const pt =
      ptRef.current ?? playTournament(ov.matches, ov.strengths, mode === "live");
    ptRef.current = pt;
    const acc = new Map<string, PlayedMatch>();
    pt.order.forEach((pm) => acc.set(pm.id, pm));
    setPlayed(acc);
    setCurrent(null);
    setPhase("idle");
    setChampion(championRef(pt.championId));
    setRunning(false);
  };

  return (
    <div className="wrap">
      <div className="hero">
        <div className="brand">
          <span className="brand-mark">ZC</span>
          <span className="brand-name">zekecabre</span>
        </div>
        <h1>
          Predictor <span className="glow">Mundial 2026</span>
        </h1>
        <p>
          Desde octavos. Fuerza real por Elo de resultados, con lesiones,
          cansancio, forma y moral calculada. Simulación Monte Carlo y batallas
          animadas partido a partido.
        </p>
        {ov && (
          <span className={`badge ${ov.meta.data_source === "api" ? "live" : ""}`}>
            {ov.meta.data_source === "api" ? "Datos reales en vivo" : "datos de ejemplo"}
            {ov.meta.updated_ts > 0 && (
              <span className="upd">
                · act. {new Date(ov.meta.updated_ts * 1000).toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" })}
              </span>
            )}
          </span>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      {!ov && !error && <div className="loading">Cargando datos del Mundial…</div>}

      {ov && (
        <>
          <div className="controls">
            <button className="btn" onClick={simulate} disabled={running}>
              {running ? "Simulando…" : "Simular torneo"}
            </button>
            <button className="btn ghost" onClick={skip} disabled={!running}>
              Saltar al final
            </button>
            <button className="btn ghost" onClick={reset}>
              Reiniciar
            </button>
            <button
              className="btn ghost"
              onClick={refreshData}
              disabled={refreshing || running}
            >
              {refreshing ? "Actualizando…" : "↻ Actualizar datos"}
            </button>

            <label className="toggle">
              <input
                type="checkbox"
                checked={mode === "fresh"}
                disabled={running}
                onChange={(e) => setMode(e.target.checked ? "fresh" : "live")}
              />
              Reabrir octavos (simular todo de cero)
            </label>
            <label className="toggle">
              <input
                type="checkbox"
                checked={fast}
                onChange={(e) => setFast(e.target.checked)}
              />
              Rápido
            </label>
            <label className="toggle">
              Simulaciones:
              <select
                className="select"
                value={nSims}
                disabled={running}
                onChange={(e) => setNSims(Number(e.target.value))}
              >
                <option value={5000}>5.000</option>
                <option value={20000}>20.000</option>
                <option value={50000}>50.000</option>
              </select>
            </label>
          </div>

          <div className="section">
            <BattleArena
              current={current}
              phase={phase}
              champion={champion}
              matchIndex={matchIndex}
              totalMatches={total}
              fightMs={fightDur}
            />
          </div>

          <div className="section">
            <h2>Cuadro final · fixtures</h2>
            <Bracket
              matches={ov.matches}
              predictions={ov.predictions}
              played={played.size ? played : undefined}
            />
          </div>

          {ov.calibration?.records?.length > 0 && (
            <div className="section">
              <h2>Calibración · aciertos sobre lo ya jugado</h2>
              <Calibration
                data={ov.calibration}
                displayPct={calibPct}
                busy={calibBusy}
                onCalibrate={calibrate}
              />
            </div>
          )}

          <div className="section grid2">
            <div>
              <h2>Probabilidad de ser campeón</h2>
              <ChampionOdds data={ov.simulation} />
              <p className="note">
                Sobre {ov.meta.simulations.toLocaleString("es")} simulaciones Monte
                Carlo{mode === "fresh" ? " (octavos reabiertos)" : " (respetando resultados ya jugados)"}.
              </p>
            </div>
            <div>
              <h2>Fuerza de cada equipo</h2>
              <StrengthTable data={ov.strengths} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
