import type { SimResult } from "../lib/api";
import Flag from "./Flag";

export default function ChampionOdds({ data }: { data: SimResult[] }) {
  const rows = data.filter((d) => d.champion_pct > 0.05).slice(0, 12);
  const max = Math.max(...rows.map((r) => r.champion_pct), 1);
  return (
    <div className="odds">
      {rows.map((r, i) => (
        <div className="row" key={r.team_id}>
          <span className="rank">{i + 1}</span>
          <span className="team">
            <Flag src={r.flag} code={r.code} />
            <span>{r.name}</span>
          </span>
          <span className="bar">
            <span style={{ width: `${(r.champion_pct / max) * 100}%` }} />
          </span>
          <span className="val">{r.champion_pct.toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}
