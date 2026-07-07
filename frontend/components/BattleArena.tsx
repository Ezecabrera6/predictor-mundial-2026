"use client";

import { useEffect, useMemo, useState } from "react";
import { ROUND_LABELS, type TeamRef } from "../lib/api";
import type { PlayedMatch } from "../lib/sim";
import { emblem } from "../lib/emblems";
import Flag from "./Flag";

export type Phase = "idle" | "fighting" | "decided";

type Props = {
  current: PlayedMatch | null;
  phase: Phase;
  champion: TeamRef | null;
  matchIndex: number;
  totalMatches: number;
  fightMs: number;
};

function Confetti() {
  const pieces = useMemo(
    () =>
      Array.from({ length: 48 }, (_, i) => ({
        left: Math.random() * 100,
        delay: Math.random() * 1.2,
        dur: 1.6 + Math.random() * 1.6,
        color: ["#4cc38a", "#6ea8fe", "#e5788b", "#ededed"][i % 4],
      })),
    []
  );
  return (
    <>
      {pieces.map((p, i) => (
        <span
          key={i}
          className="confetti"
          style={{
            left: `${p.left}%`,
            background: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.dur}s`,
          }}
        />
      ))}
    </>
  );
}

export default function BattleArena({
  current,
  phase,
  champion,
  matchIndex,
  totalMatches,
  fightMs,
}: Props) {
  const [hp, setHp] = useState({ home: 100, away: 100 });
  const [hit, setHit] = useState<null | "home" | "away">(null);
  const [shake, setShake] = useState(false);
  const [blows, setBlows] = useState(0);

  useEffect(() => {
    if (!current) {
      setHp({ home: 100, away: 100 });
      setHit(null);
      setBlows(0);
      return;
    }
    if (phase === "fighting") {
      setHp({ home: 100, away: 100 });
      setBlows(0);
      const homeWins = current.winnerId === current.home.id;
      const closeness = Math.abs(current.pHome - 0.5); // 0..0.5 (peleado→claro)
      const loserEnd = 5 + Math.random() * 9;
      const winnerEnd = 40 + closeness * 90 + Math.random() * 8;
      const homeTarget = homeWins ? winnerEnd : loserEnd;
      const awayTarget = homeWins ? loserEnd : winnerEnd;
      const N = 6;
      const cadence = Math.max(180, fightMs / (N + 0.5));
      let i = 0;
      let prev = { home: 100, away: 100 };
      const iv = setInterval(() => {
        i += 1;
        const jitter = () => Math.random() * 8 - 4;
        const nh = Math.max(3, 100 - (100 - homeTarget) * (i / N) + jitter());
        const na = Math.max(3, 100 - (100 - awayTarget) * (i / N) + jitter());
        const struck = prev.home - nh >= prev.away - na ? "home" : "away";
        prev = { home: nh, away: na };
        setHp({ home: nh, away: na });
        setHit(struck);
        setShake(true);
        setBlows((b) => b + 1);
        setTimeout(() => {
          setHit(null);
          setShake(false);
        }, Math.min(160, cadence * 0.5));
        if (i >= N) clearInterval(iv);
      }, cadence);
      return () => clearInterval(iv);
    }
    if (phase === "decided") {
      const homeWins = current.winnerId === current.home.id;
      setHp((h) => ({
        home: homeWins ? Math.max(30, h.home) : 0,
        away: homeWins ? 0 : Math.max(30, h.away),
      }));
      setHit(null);
    }
  }, [current?.id, phase, fightMs]); // eslint-disable-line react-hooks/exhaustive-deps

  if (champion) {
    return (
      <div className="arena">
        <Confetti />
        <div className="champ">
          <div className="crown">Campeón del Mundo</div>
          <div className="champ-emblem">{emblem(champion.code)}</div>
          <Flag src={champion.flag} code={champion.code} />
          <div className="name">{champion.name}</div>
        </div>
      </div>
    );
  }

  if (!current) {
    return (
      <div className="arena">
        <div className="idle">
          Tocá <b>Simular torneo</b> para ver la lucha partido a partido hasta
          coronar al campeón.
        </div>
      </div>
    );
  }

  const decided = phase === "decided";
  const homeWon = decided && current.winnerId === current.home.id;
  const awayWon = decided && current.winnerId === current.away.id;

  return (
    <div className={`arena ${shake ? "shake" : ""}`}>
      <div className="round-tag">
        <b>{ROUND_LABELS[current.round]}</b> · lucha {matchIndex + 1}/
        {totalMatches}
        {!current.live && " · resultado real"}
      </div>

      <div className="duel">
        <Fighter
          team={current.home}
          side="home"
          prob={current.pHome}
          hp={hp.home}
          hurt={hit === "home"}
          striking={hit === "away" && phase === "fighting"}
          winner={homeWon}
          loser={awayWon}
        />
        <div className="vs">
          <span className={`spark ${hit ? "hit" : ""}`} />
          <span className={`swords ${hit ? "clash" : ""}`}>⚔️</span>
          {phase === "fighting" && <span className="blows">{blows} golpes</span>}
        </div>
        <Fighter
          team={current.away}
          side="away"
          prob={1 - current.pHome}
          hp={hp.away}
          hurt={hit === "away"}
          striking={hit === "home" && phase === "fighting"}
          winner={awayWon}
          loser={homeWon}
        />
      </div>
    </div>
  );
}

function Fighter({
  team,
  side,
  prob,
  hp,
  hurt,
  striking,
  winner,
  loser,
}: {
  team: TeamRef;
  side: "home" | "away";
  prob: number;
  hp: number;
  hurt: boolean;
  striking: boolean;
  winner: boolean;
  loser: boolean;
}) {
  const cls = [
    "fighter",
    side,
    hurt ? "hurt" : "",
    striking ? "strike" : "",
    winner ? "winner" : "",
    loser ? "loser" : "",
  ].join(" ");
  const hpColor =
    hp > 55 ? "var(--win)" : hp > 25 ? "#e0b341" : "var(--away)";
  return (
    <div className={cls}>
      <div className="emblem">{emblem(team.code)}</div>
      <Flag src={team.flag} code={team.code} />
      <div className="name">{team.name}</div>
      <div className="hpbar">
        <span style={{ width: `${Math.max(0, hp)}%`, background: hpColor }} />
      </div>
      <div className="prob">{Math.round(prob * 100)}% de ganar</div>
    </div>
  );
}
