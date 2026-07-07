import type { ScorerRow } from "../lib/api";
import Flag from "./Flag";

// Carrera por la Bota de Oro: goles esperados por jugador (reales + previstos).
export default function TopScorers({ data }: { data: ScorerRow[] }) {
  const rows = (data ?? []).filter((d) => d.exp_goals >= 0.2).slice(0, 15);
  if (!rows.length) {
    return <p className="note">TodavÃ­a no hay datos de goleadores.</p>;
  }
  const max = Math.max(...rows.map((r) => r.exp_goals), 1);
  return (
    <div className="odds">
      {rows.map((r, i) => (
        <div className="row" key={`${r.name}-${i}`}>
          <span className="rank">{i + 1}</span>
          <span className="team">
            <Flag src="" code={r.code} />
            <span>
              {r.name}
              {r.code ? ` Â· ${r.code}` : ""}
            </span>
          </span>
          <span className="bar">
            <span style={{ width: `${(r.exp_goals / max) * 100}%` }} />
          </span>
          <span className="val">
            {r.exp_goals.toFixed(1)}
            {r.goals_now > 0 ? ` (${r.goals_now}âœ“)` : ""}
          </span>
        </div>
      ))}
    </div>
  );
}