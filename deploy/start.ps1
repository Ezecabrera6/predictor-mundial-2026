# Arranca backend (0.0.0.0:8000) y frontend (0.0.0.0:3000) en segundo plano.
$root = Split-Path $PSScriptRoot -Parent

Write-Host "Iniciando backend en :8000 ..." -ForegroundColor Cyan
Start-Process -WindowStyle Hidden `
    -FilePath "$root\backend\.venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory "$root\backend"

Write-Host "Iniciando frontend en :3000 ..." -ForegroundColor Cyan
Start-Process -WindowStyle Hidden `
    -FilePath "npm.cmd" -ArgumentList "run", "start" `
    -WorkingDirectory "$root\frontend"

$ip = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } |
    Select-Object -First 1).IPAddress
Write-Host "`nListo. Accede desde la red en:" -ForegroundColor Green
Write-Host "   http://$ip:3000" -ForegroundColor Green
