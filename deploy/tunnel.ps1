# ===========================================================================
# Expone el predictor en un dominio FIJO y publico usando ngrok (gratis).
# Todo el trafico (incluida la API /api) pasa por ese unico dominio, porque
# el frontend ahora habla con el backend por /api en el mismo origen.
# ===========================================================================
#
# Alta (una sola vez):
#   1) Crear cuenta gratis en https://ngrok.com  (no pide tarjeta).
#   2) Copiar tu authtoken de:
#        https://dashboard.ngrok.com/get-started/your-authtoken
#   3) Reservar tu dominio estatico gratis en:
#        https://dashboard.ngrok.com/domains  ->  "New Domain"
#      Queda algo como  tu-nombre.ngrok-free.app
#
# Primera vez (guarda el token):
#   .\deploy\tunnel.ps1 -Domain "tu-nombre.ngrok-free.app" -Authtoken "TU_TOKEN"
#
# Las siguientes veces:
#   .\deploy\tunnel.ps1 -Domain "tu-nombre.ngrok-free.app"

param(
    [Parameter(Mandatory = $true)][string]$Domain,
    [string]$Authtoken = ""
)
$ErrorActionPreference = "Stop"

# 1) Instalar ngrok si falta (via winget).
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando ngrok (winget)..." -ForegroundColor Cyan
    winget install --id ngrok.ngrok -e --accept-source-agreements --accept-package-agreements
    Write-Host "Si winget no lo encontro, bajalo de https://ngrok.com/download, descomprimilo y reintenta." -ForegroundColor DarkGray
}

# 2) Guardar el authtoken (solo hace falta la primera vez).
if ($Authtoken -ne "") {
    ngrok config add-authtoken $Authtoken
}

# 3) Asegurar que la app este corriendo en :3000 (si no, la arranca).
$up = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if (-not $up) {
    Write-Host "El frontend no esta en :3000. Arranco deploy\start.ps1 ..." -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot "start.ps1")
    Start-Sleep -Seconds 6
}

# 4) Abrir el tunel al dominio fijo. Queda en primer plano (Ctrl+C corta).
Write-Host ""
Write-Host "Tunel activo:  https://$Domain  ->  http://localhost:3000" -ForegroundColor Green
Write-Host "Entra desde el celu o cualquier PC a esa URL. Ctrl+C corta el tunel." -ForegroundColor Green
Write-Host ""
# Nota: si tu version de ngrok se queja de --url, usa:  ngrok http --domain=$Domain 3000
ngrok http "--url=https://$Domain" 3000