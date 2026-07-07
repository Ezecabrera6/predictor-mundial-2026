# ===========================================================================
# Expone el predictor en un dominio FIJO y publico usando Tailscale Funnel.
# Ventajas vs ngrok: NO muestra pagina intermedia y queda PERSISTENTE
# (revive solo despues de reiniciar la PC, mientras la app corra en :3000).
# Dominio tipo:  https://<tu-pc>.<tu-tailnet>.ts.net
# ===========================================================================
#
# Alta (una sola vez):
#   1) Este script instala Tailscale (via winget).
#   2) 'tailscale up' abre el navegador para iniciar sesion (sirve con Google).
#   3) La primera vez, Funnel puede pedir habilitarse: si el comando imprime un
#      link del admin console, abrilo, aceptalo (Enable Funnel) y reintenta.
#
# Uso:
#   .\deploy\tunnel-tailscale.ps1
#
# Ver la URL / estado:   tailscale funnel status
# Apagar el funnel:      tailscale serve reset

$ErrorActionPreference = "Stop"

# 1) Instalar Tailscale si falta.
if (-not (Get-Command tailscale -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando Tailscale (winget)..." -ForegroundColor Cyan
    winget install --id Tailscale.Tailscale -e --accept-source-agreements --accept-package-agreements
    Write-Host "Si winget no lo encontro, instalalo de https://tailscale.com/download/windows y reabri PowerShell." -ForegroundColor DarkGray
}

# 2) Iniciar sesion en tu tailnet (abre el navegador la primera vez).
Write-Host "Conectando a tu tailnet (si abre el navegador, inicia sesion)..." -ForegroundColor Cyan
tailscale up

# 3) Asegurar que la app este en :3000 (si no, la arranca).
$up = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if (-not $up) {
    Write-Host "El frontend no esta en :3000. Arranco deploy\start.ps1 ..." -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot "start.ps1")
    Start-Sleep -Seconds 6
}

# 4) Publicar el :3000 por Funnel, en segundo plano y persistente.
Write-Host "Habilitando Funnel sobre el puerto 3000..." -ForegroundColor Cyan
tailscale funnel --bg 3000

# 5) Mostrar la URL publica (tu dominio fijo).
Write-Host ""
Write-Host "Estado del Funnel:" -ForegroundColor Green
tailscale funnel status
Write-Host ""
Write-Host "Tu dominio fijo es el https://<tu-pc>.<tailnet>.ts.net que figura arriba." -ForegroundColor Green
Write-Host "Queda activo aunque reinicies la PC (mientras la app corra en :3000)." -ForegroundColor Green