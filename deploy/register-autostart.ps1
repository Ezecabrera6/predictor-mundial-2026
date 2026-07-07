# Registra una tarea programada para que el proyecto arranque solo al iniciar sesion.
# CORRER COMO ADMINISTRADOR.
$start = Join-Path $PSScriptRoot "start.ps1"
$action = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$start`""
schtasks /Create /TN "PredictorMundial" /TR $action /SC ONLOGON /RL HIGHEST /F
Write-Host "Tarea 'PredictorMundial' creada: arranca al iniciar sesion." -ForegroundColor Green
Write-Host "Para quitarla: schtasks /Delete /TN PredictorMundial /F" -ForegroundColor DarkGray
