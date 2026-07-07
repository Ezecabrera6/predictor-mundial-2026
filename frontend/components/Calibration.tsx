import type { Calibration as CalData } from "../lib/api";
import { ROUND_LABELS } from "../lib/api";

type Props = {
  data: CalData;
  displayPct: number;
  busy: boolean;
  onCalibrate: () => void;
};

export default function Calibration({
  data,
  displayPct,
  busy,
  onCalibrate,
}: Props) {
  const hit = data.records.filter((r) => r.ok).length;
  const perfect = displayPct >= 99.95;

  return (
    <div className="calib">
      <div className="calib-head">
        <div className="calib-score">
          <div className={`big ${perfect ? "perfect" : ""}`}>
            {displayPct.toFixed(0)}
            <span className="pct-sign">%</span>
          </div>
          <div className="calib-sub">
            {hit}/{data.records.length} resultados ya jugados acertados
            {data.fitted && !busy && " · modelo ajustado"}
          </div>
        </div>
        <button className="btn" onClick={onCalibrate} disabled={busy}>
          {busy
            ? "Aprendiendo…"
            : perfect && data.fitted
            ? "Recalibrar"
            : "Calibrar hasta 100%"}
        </button>
      </div>

      {data.fitted && data.corrections.length > 0 && (
        <div className="calib-adj">
          Ajustes aprendidos:{" "}
          {data.corrections.slice(0, 6).map((c) => (
            <span className="adj" key={c.code}>
              {c.code} {c.adj > 0 ? "+" : ""}
              {c.adj}
            </span>
          ))}
        </div>
      )}

      <div className="calib-list">
        {data.records.map((r, i) => (
          <div className={`cal-row ${r.ok ? "ok" : "miss"}`} key={i}>
            <span className="mark">{r.ok ? "✓" : "✗"}</span>
            <span className="cal-round">{ROUND_LABELS[r.round] || r.round}</span>
            <span className="cal-match">
              {r.home} <span className="cal-score">{r.score}</span> {r.away}
            </span>
            <span className="cal-pred">
              pred: <b>{r.predicted}</b>
              {!r.ok && (
                <>
                  {" · "}real: <b>{r.actual}</b>
                </>
              )}
            </span>
            {r.scorers && <span className="cal-scorers">⚽ {r.scorers}</span>}
          </div>
        ))}
      </div>

      <p className="note">
        El modelo “predice” cada partido ya jugado con la fuerza de los equipos.
        Al calibrar, aprende un ajuste de rating por selección hasta reproducir
        todos los resultados. Llegar al 100% ajusta también upsets y penales, así
        que es un ajuste a lo ocurrido, no una garantía a futuro.
      </p>
    </div>
  );
}
