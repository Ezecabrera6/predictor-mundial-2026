// Emblema "de batalla" por selección (fifa_code). Aparece en el duelo animado.
// Cada uno guiña a un símbolo del país / apodo de la selección.
const EMBLEMS: Record<string, string> = {
  ARG: "☀️", // Sol de Mayo (la Albiceleste)
  BRA: "🦜", // canarinha
  FRA: "🐓", // le coq / los Galos
  ENG: "🦁", // three lions
  ESP: "🐂", // la furia / el toro
  POR: "⚓", // los navegantes
  NED: "🧀", // la naranja mecánica
  GER: "🦅", // die Mannschaft
  BEL: "😈", // diablos rojos
  CRO: "🔥",
  URU: "🧉", // la celeste
  MAR: "⭐", // estrella verde
  USA: "🦅", // anfitrión
  MEX: "🌵", // anfitrión
  CAN: "🍁", // anfitrión
  JPN: "🌸",
  SEN: "🦁", // leones de la Teranga
  NOR: "🛡️", // vikingos
  SUI: "🏔️", // los Alpes
  COL: "☕", // los cafeteros
  EGY: "🏺", // los faraones
  PAR: "🐆",
  SWE: "❄️",
  CIV: "🐘", // elefantes
  AUS: "🦘",
  ECU: "🌋",
  AUT: "🎿",
  GHA: "⭐",
  ALG: "🌙",
  NZL: "🥝",
  BIH: "🏔️",
  CPV: "🌊",
  COD: "🐆",
  IRN: "🐆",
  JOR: "🦅",
  RSA: "🦁",
};

export function emblem(code?: string): string {
  if (!code) return "⚔️";
  return EMBLEMS[code.toUpperCase()] || "⚔️";
}
