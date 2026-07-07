import type { Match, Prediction, TeamRef } from "../lib/api";
import { ROUND_LABELS } from "../lib/api";
import type { PlayedMatch } from "../lib/sim";
import Flag from "./Flag";

const ROUNDS: Match["round"][] = ["r16", "qf", "sf", "final"];

type Props = {
  matches: Match[];
  predictions: Prediction[];
  played?: Map<string, PlayedMatch>;
};

export default function Bracket({ matches, predictions, played }: Props) {
  const predById = new Map(predictions.map((p) => [p.match_id, p]));

  function Row({
    team,
    won,
    lost,
    pct,
  }: {
    team: TeamRef;
    won: boolean;
    lost: boolean;
    pct?: number;
  }) {
    return (
      <div className={`row ${won ? "won" : ""} ${lost ? "lost" : ""}`}>
        <Flag src={team.flag} code={team.code} />
        <span className="tn">{team.name}</span>
        {pct != null && <span className="pct">{Math.round(pct * 100)}%</span>}
      </div>
    );
  }

  function Tie({ m }: { m: Match }) {
    const pm = played?.get(m.id);
    const pred = predById.get(m.id);
    const home = pm ? pm.home : m.home;
    const away = pm ? pm.away : m.away;
    const winnerId = pm ? pm.winnerId : m.finished ? m.winner_id : null;
    const decided = winnerId != null;
    const isReal = m.finished && (!pm || !pm.live);

    const scorers = [...m.home_scorers, ...m.away_scorers];
    const predScorers =
      !isReal && !decided && pred?.pred_score
        ? [
            ...(pred.home_scorers_likely ?? []),
            ...(pred.away_scorers_likely ?? []),
          ].filter(Boolean)
        : [];

    let meta: React.ReactNode = null;
    if (isReal && m.score) {
      meta = <span className="played">Fin Â· {m.score}</span>;
    } else if (pm && pm.live) {
      meta = "simulado";
    } else if (pred) {
      meta = pred.pred_score
        ? `favorito: ${pred.favorite} Â· previsto ${pred.pred_score}`
        : `favorito: ${pred.favorite}`;
    }

    return (
      <div className={`tie ${decided ? "" : "pending"}`}>
        <Row
          team={home}
          won={decided && winnerId === home.id}
          lost={decided && winnerId !== home.id}
          pct={!decided ? pred?.home_win_prob : undefined}
        />
        <Row
          team={away}
          won={decided && winnerId === away.id}
          lost={decided && winnerId !== away.id}
          pct={!decided ? pred?.away_win_prob : undefined}
        />
        {meta && <div className="meta">{meta}</div>}
        {isReal && scorers.length > 0 && (
          <div className="scorers">âš½ {scorers.join(" Â· ")}</div>
        )}
        {predScorers.length > 0 && (
          <div className="scorers pred">âš½ prob. {predScorers.join(" Â· ")}</div>
        )}
      </div>
    );
  }

  return (
    <div className="bkt">
      {ROUNDS.map((round, ri) => {
        const ms = matches
          .filter((m) => m.round === round)
          .sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }));
        return (
          <div
            className={`round round-${round} ${ri === ROUNDS.length - 1 ? "last" : ""}`}
            key={round}
          >
            <h3>{ROUND_LABELS[round]}</h3>
            <div className="round-slots">
              {ms.map((m) => (
                <div className="slot" key={m.id}>
                  <Tie m={m} />
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}