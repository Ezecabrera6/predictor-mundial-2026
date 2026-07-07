# Abre los puertos 8000 y 3000 en el Firewall de Windows.
# CORRER COMO ADMINISTRADOR.
New-NetFirewallRule -DisplayName "Predictor Backend 8000" -Direction Inbound `
    -Action Allow -Protocol TCP -LocalPort 8000 -ErrorAction SilentlyContinue | Out-Null
New-NetFirewallRule -DisplayName "Predictor Frontend 3000" -Direction Inbound `
    -Action Allow -Protocol TCP -LocalPort 3000 -ErrorAction SilentlyContinue | Out-Null
Write-Host "Puertos 8000 y 3000 habilitados en el firewall." -ForegroundColor Green
