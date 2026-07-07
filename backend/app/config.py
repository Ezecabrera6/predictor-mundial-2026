"""Configuración de la app y pesos del modelo.

Todos los pesos y factores están acá para poder tunearlos sin tocar la lógica.
La escala interna de fuerza es Elo (arranca en 1500).
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Fuente de datos ---
    data_source: str = "sample"  # "sample" (offline) | "api" (worldcup26.ir)

    # --- API worldcup26.ir ---
    wc_base_url: str = "https://worldcup26.ir"
    wc_email: str = ""
    wc_password: str = ""
    wc_name: str = "Predictor"
    wc_token_cache: str = str(BACKEND_DIR / ".token_cache.txt")
    http_timeout: float = 25.0

    # --- Archivos de datos ---
    overrides_file: str = str(BACKEND_DIR / "app" / "data" / "overrides.json")
    sample_file: str = str(BACKEND_DIR / "app" / "data" / "sample_data.json")

    # --- Simulación ---
    simulations: int = 20_000

    # Cada cuántos segundos se vuelven a pedir los datos al API (frescura)
    cache_ttl: int = 600

    # --- Elo (cálculo de fuerza base desde resultados reales) ---
    elo_start: float = 1500.0
    elo_k: float = 40.0            # sensibilidad por partido
    elo_scale: float = 200.0      # diff de 200 ≈ 91% ; diff ~95 ≈ 75%

    # --- Pesos del modelo (en puntos Elo) ---
    injury_weight: float = 120.0   # penalización máx por lesiones
    fatigue_weight: float = 70.0   # penalización máx por cansancio
    form_weight: float = 50.0      # ajuste por forma reciente (-1..+1)
    host_bonus: float = 45.0       # ventaja de local (anfitrión)
    morale_weight: float = 40.0    # empuje anímico (override manual)


settings = Settings()
