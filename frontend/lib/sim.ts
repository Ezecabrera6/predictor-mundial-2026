// Simulación de UNA corrida del torneo en el cliente, para animar el bracket
// partido a partido. Usa las mismas fuerzas efectivas y la logística Elo del
// backend (elo_scale = 200).

import type { Match, Strength, TeamRef } from "./api";

const ELO_SCALE = 200;
const ROUND_ORDER: Record<string, number> = {
  r16: 0,
  qf: 1,
  sf: 2,
  final: 3,
  third: 3,
};

export function winProb(a: number, b: number): number {
  return 1 / (1 + Math.pow(10, -(a - b) / ELO_SCALE));
}

export type PlayedMatch = {
  id: string;
  round: Match["round"];
  home: TeamRef;
  away: TeamRef;
  pHome: number;
  winnerId: number | null;
  live: boolean; // true = se decidió en esta corrida (no venía jugado)
  score: string | null;
};

type Ref = { teamId: number | null; source: string | null; take: "W" | "L" };

function parseSide(side: TeamRef): Ref {
  if (side.id != null) return { teamId: side.id, source: null, take: "W" };
  const m = side.name.match(/(\d+)/);
  const take = side.name.toLowerCase().startsWith("perdedor") ? "L" : "W";
  return { teamId: null, source: m ? m[1] : null, take };
}

export type Playthrough = {
  order: PlayedMatch[];
  championId: number | null;
};

// Ejecuta una corrida. Si respectFinished, mantiene los resultados reales;
// si no, "reabre" todo desde octavos y sortea cada partido.
export function playTournament(
  matches: Match[],
  strengths: Strength[],
  respectFinished = true
): Playthrough {
  const byId = new Map<number, Strength>();
  strengths.forEach((s) => byId.set(s.team_id, s));
  const refByTeam = (id: number): TeamRef => {
    const s = byId.get(id);
    return {
      id,
      name: s?.name ?? `#${id}`,
      code: s?.code ?? "",
      flag: s?.flag ?? "",
    };
  };

  const ordered = [...matches].sort(
    (a, b) =>
      (ROUND_ORDER[a.round] - ROUND_ORDER[b.round]) ||
      a.id.localeCompare(b.id, undefined, { numeric: true })
  );

  const winners = new Map<string, number>();
  const losers = new Map<string, number>();
  const out: PlayedMatch[] = [];

  for (const m of ordered) {
    if (m.round === "third") continue; // el 3er puesto no altera la corona
    const hr = parseSide(m.home);
    const ar = parseSide(m.away);
    const homeId =
      hr.teamId ??
      (hr.source ? (hr.take === "W" ? winners : losers).get(hr.source) : undefined);
    const awayId =
      ar.teamId ??
      (ar.source ? (ar.take === "W" ? winners : losers).get(ar.source) : undefined);
    if (homeId == null || awayId == null) continue;

    const sh = byId.get(homeId)?.effective_rating ?? 1500;
    const sa = byId.get(awayId)?.effective_rating ?? 1500;
    const pHome = winProb(sh, sa);

    let winnerId: number;
    let live = true;
    if (respectFinished && m.finished && m.winner_id != null) {
      winnerId = m.winner_id;
      live = false;
    } else {
      winnerId = Math.random() < pHome ? homeId : awayId;
    }
    winners.set(m.id, winnerId);
    losers.set(m.id, winnerId === homeId ? awayId : homeId);

    out.push({
      id: m.id,
      round: m.round,
      home: refByTeam(homeId),
      away: refByTeam(awayId),
      pHome,
      winnerId,
      live,
      score: live ? null : m.score,
    });
  }

  const finalMatch = out.find((m) => m.round === "final");
  return { order: out, championId: finalMatch?.winnerId ?? null };
}
