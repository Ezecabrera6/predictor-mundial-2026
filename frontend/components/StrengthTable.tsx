import type { Strength } from "../lib/api";
import Flag from "./Flag";

function signed(n: number, invert = false) {
  const cls = (invert ? -n : n) >= 0 ? "pos" : "neg";
  const v = n > 0 ? `+${n}` : `${n}`;
  return <span className={cls}>{v}</span>;
}

export default function StrengthTable({ data }: { data: Strength[] }) {
  return (
    <div className="tablewrap">
      <table className="str">
        <thead>
          <tr>
            <th className="team">Equipo</th>
            <th>Elo base</th>
            <th>Lesiones</th>
            <th>Cansancio</th>
            <th>Forma</th>
            <th>Moral</th>
            <th>Local</th>
            <th>Ajuste</th>
            <th>Fuerza</th>
          </tr>
        </thead>
        <tbody>
          {data.map((s) => (
            <tr key={s.team_id}>
              <td className="team">
                <Flag src={s.flag} code={s.code} />
                <span>
                  {s.name}
                  {s.injured_players.length > 0 && (
                    <span className="inj"> · {s.injured_players.join(", ")}</span>
                  )}
                </span>
              </td>
              <td>{s.base_rating}</td>
              <td>{s.injury_penalty ? signed(-s.injury_penalty) : "—"}</td>
              <td>{s.fatigue_penalty ? signed(-s.fatigue_penalty) : "—"}</td>
              <td>{s.form_adjustment ? signed(s.form_adjustment) : "—"}</td>
              <td>{s.morale_adjustment ? signed(s.morale_adjustment) : "—"}</td>
              <td>{s.host_bonus ? signed(s.host_bonus) : "—"}</td>
              <td>{s.calibration_adj ? signed(s.calibration_adj) : "—"}</td>
              <td className="eff">{s.effective_rating}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
