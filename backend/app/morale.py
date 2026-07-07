"""Cálculo de moral/momentum desde los resultados reales del torneo.

La idea (pedido del usuario): la moral no se carga a mano, se deduce de CÓMO
le fue a cada equipo:
  - Ganar suma, y ganar por goleada suma más.
  - Empatar NO suma (aunque después se avance por penales: un 1-1 significa
    que el equipo no fue superior ese partido).
  - Perder resta, y perder por mucho resta más.
  - Los partidos más recientes pesan más (momentum).

Así, un equipo que ganó todos con claridad (ej. Argentina) tiene moral alta,
y uno que empató varios y avanzó por penales (ej. Egipto) tiene moral baja.
"""

from __future__ import annotations


def match_quality(gf: int, ga: int) -> float:
    """Calidad de un resultado en [-1, 1] según el marcador."""
    gd = gf - ga
    if gd > 0:  # victoria: 1-0 -> 0.4, 2-0 -> 0.6, 3-0 -> 0.8, 4+ -> 1.0
        return min(0.4 + (gd - 1) * 0.2, 1.0)
    if gd == 0:  # empate: no fue superior (incluye avances por penales)
        return -0.1
    # derrota: -1 -> -0.4, -2 -> -0.55, ...
    return max(-0.4 + (gd + 1) * 0.15, -1.0)


def compute_morale(results: list[tuple[int, int]]) -> float:
    """Moral en [-1, 1]. `results` = [(goles_a_favor, goles_en_contra), ...]
    en orden cronológico (más nuevo al final)."""
    if not results:
        return 0.0
    weights = [i + 1 for i in range(len(results))]  # peso creciente por recencia
    qs = [match_quality(gf, ga) for gf, ga in results]
    total = sum(w * q for w, q in zip(weights, qs)) / sum(weights)
    return round(max(-1.0, min(1.0, total)), 3)
