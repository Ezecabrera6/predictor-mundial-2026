# Detiene backend (:8000) y frontend (:3000).
foreach ($port in 8000, 3000) {
    $pids = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $pids) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        Write-Host "Detenido proceso en puerto $port (PID $processId)"
    }
}
Write-Host "Servidores detenidos." -ForegroundColor Green
