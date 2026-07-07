# Instalacion inicial en el servidor (correr UNA vez).
# Requiere Python 3.12+ y Node 20+ instalados y en el PATH.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

Write-Host "== Backend: entorno virtual + dependencias ==" -ForegroundColor Cyan
Set-Location "$root\backend"
if (-not (Test-Path .venv)) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "!! Edita backend\.env con tus credenciales del API worldcup26.ir" -ForegroundColor Yellow
}

Write-Host "== Frontend: dependencias + build de produccion ==" -ForegroundColor Cyan
Set-Location "$root\frontend"
# Sin .env.local, el frontend detecta solo la IP del backend segun el host.
if (Test-Path .env.local) { Remove-Item .env.local }
npm install
npm run build

Write-Host "`nSetup completo." -ForegroundColor Green
Write-Host "Siguiente: deploy\open-firewall.ps1 (como admin) y deploy\start.ps1" -ForegroundColor Green
