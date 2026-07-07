# Predictor Mundial 2026 · zekecabre

Predice el Mundial 2026 **desde octavos de final** combinando datos reales con
factores de contexto, y lo muestra con un cuadro estilo Mundial, batallas
animadas partido a partido y una calibración contra los resultados ya jugados.

## Cómo funciona

- **Datos reales** del API [worldcup26.ir](https://worldcup26.ir): equipos,
  cruces y resultados del torneo (se actualiza solo cada 10 min).
- **Fuerza por equipo (Elo)** calculada replayando todos los partidos jugados,
  ajustada por:
  - **Lesiones / estado físico** (capa manual editable en `backend/app/data/overrides.json`).
  - **Cansancio** (días de descanso y carga de partidos, del calendario real).
  - **Forma** reciente (últimos resultados).
  - **Moral** calculada de cómo le fue: ganar contundente suma, empatar o pasar
    por penales no.
- **Simulación Monte Carlo** del cuadro (miles de corridas → % de avanzar y de
  salir campeón), respetando los partidos ya jugados.
- **Calibración**: el modelo "predice" cada partido ya finalizado; con un botón
  aprende un ajuste de rating por selección hasta reproducir el 100% de lo
  jugado.

## Estructura

```
predictor/
├── backend/          # FastAPI: modelo, Elo, moral, Monte Carlo, calibración
│   ├── app/
│   │   ├── main.py           # endpoints
│   │   ├── data/             # proveedores (API real / sample offline) + overrides
│   │   ├── scoring.py  elo.py  morale.py  calibration.py  simulation.py
│   └── requirements.txt
└── frontend/         # Next.js: bracket, batallas animadas, odds, calibración
```

## Requisitos

- Python 3.12+
- Node.js 20+

## Puesta en marcha (desarrollo)

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows;  en Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # completar credenciales del API worldcup26.ir
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Variables en `backend/.env`:

```
DATA_SOURCE=api               # "api" (real) o "sample" (offline, sin internet)
WC_EMAIL=tu_email@example.com
WC_PASSWORD=tu_password
SIMULATIONS=20000
CACHE_TTL=600                 # segundos entre refrescos automáticos
```

> La primera vez el backend se registra solo en el API y cachea el token.

### 2. Frontend

```bash
cd frontend
npm install
# frontend/.env.local -> NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev                   # http://localhost:3000
```

## Producción / servidor local

```bash
# Backend (accesible en la LAN):
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend:
cd frontend && npm run build && npm run start   # http://localhost:3000
```

Si accedés desde otra máquina de la red, poné en `frontend/.env.local`
`NEXT_PUBLIC_API_URL=http://IP_DEL_SERVIDOR:8000` antes de `npm run build`.

## Notas

- `backend/.env` y el token nunca se commitean (están en `.gitignore`).
- Las lesiones no vienen del API: se cargan a mano en `overrides.json`.
- Llegar al 100% en la calibración ajusta también upsets y penales: es un
  ajuste a lo ya ocurrido, no una garantía a futuro.
