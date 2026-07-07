// Tipos y cliente del backend del predictor.

// URL del backend. Prioridad:
// 1) NEXT_PUBLIC_API_URL si se define (override para dev).
// 2) En el navegador: MISMO ORIGEN (string vacÃ­o). Las llamadas van a /api/*
//    y Next las reenvÃ­a al backend (ver rewrites en next.config.mjs). AsÃ­
//    funciona igual por IP en la LAN, por localhost y detrÃ¡s de un dominio o
//    tÃºnel, todo bajo un Ãºnico host y sin exponer el puerto 8000.
// 3) SSR / build: backend local.
export function apiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== "undefined") return "";
  return "http://127.0.0.1:8000";
}

export const API_URL = apiBase();

export type TeamRef = {
  id: number | null;
  name: string;
  code: string;
  flag: string;
};

export type Match = {
  id: string;
  round: "r16" | "qf" | "sf" | "final" | "third";
  home: TeamRef;
  away: TeamRef;
  finished: boolean;
  winner_id: number | null;
  score: string | null;
  home_scorers: string[];
  away_scorers: string[];
  date: string;
};

export type Strength = {
  team_id: number;
  name: string;
  code: string;
  flag: string;
  base_rating: number;
  effective_rating: number;
  injury_penalty: number;
  fatigue_penalty: number;
  form_adjustment: number;
  morale_adjustment: number;
  host_bonus: number;
  calibration_adj: number;
  injured_players: string[];
};

export type Prediction = {
  match_id: string;
  round: string;
  home: string;
  away: string;
  home_code: string;
  away_code: string;
  home_win_prob: number;
  away_win_prob: number;
  favorite: string;
  finished: boolean;
  played_result: string | null;
  pred_score?: string | null;
  home_scorers_likely?: string[];
  away_scorers_likely?: string[];
};

export type ScorerRow = {
  name: string;
  code: string;
  team: string;
  goals_now: number;
  exp_goals: number;
};

export type SimResult = {
  team_id: number;
  name: string;
  code: string;
  flag: string;
  reach_qf: number;
  reach_sf: number;
  reach_final: number;
  win_cup: number;
  champion_pct: number;
};

export type CalibRecord = {
  round: string;
  home: string;
  away: string;
  home_code: string;
  away_code: string;
  p_home: number;
  predicted: string;
  actual: string;
  score: string;
  scorers: string;
  ok: boolean;
};

export type Calibration = {
  params: { elo_scale: number };
  fitted: boolean;
  initial_accuracy: number;
  accuracy: number;
  correct: number;
  total: number;
  logloss: number;
  records: CalibRecord[];
  corrections: { code: string; name: string; adj: number }[];
};

export type Overview = {
  meta: { data_source: string; simulations: number; updated_ts: number };
  calibration: Calibration;
  teams: TeamRef[];
  matches: Match[];
  strengths: Strength[];
  predictions: Prediction[];
  simulation: SimResult[];
  top_scorers: ScorerRow[];
};

export async function fetchOverview(
  n = 20000,
  replayFrom?: string,
  refresh = false
): Promise<Overview> {
  const params = new URLSearchParams({ n: String(n) });
  if (replayFrom) params.set("replay_from", replayFrom);
  if (refresh) params.set("refresh", "true");
  const res = await fetch(`${apiBase()}/api/overview?${params.toString()}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

export async function recalibrate(target = 1.0): Promise<{
  initial_accuracy: number;
  accuracy: number;
  correct: number;
  total: number;
  history: number[];
  iterations: number;
  corrections: { code: string; name: string; adj: number }[];
}> {
  const res = await fetch(`${apiBase()}/api/recalibrate?target=${target}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`recalibrate ${res.status}`);
  return res.json();
}

export const ROUND_LABELS: Record<string, string> = {
  r16: "Octavos",
  qf: "Cuartos",
  sf: "Semifinal",
  final: "Final",
  third: "3er puesto",
};