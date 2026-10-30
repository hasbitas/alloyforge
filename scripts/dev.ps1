# Implementation for start.bat; beginners should use the root launchers.
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv/Scripts/python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Python environment is missing. Run setup.bat first.'
}
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot "frontend/node_modules"))) {
    throw "Browser interface dependencies are missing. Run setup.bat first."
}
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
foreach ($port in @(8000, 5173)) {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
    try { $listener.Start() }
    catch { throw "Port $port is in use. Stop the other app and try start.bat again." }
    finally { $listener.Stop() }
}
$backend = $null
Push-Location $repoRoot
try {
    # No reloader: stopping this process also stops the backend server.
    $backend = Start-Process -FilePath $python -WindowStyle Hidden -PassThru `
        -WorkingDirectory $repoRoot `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8000")
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($backend.HasExited) { throw "Backend exited. Check whether port 8000 is in use." }
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 1
            if ($health.status -eq "ok") { $ready = $true; break }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    if (-not $ready) { throw "Backend did not become ready on port 8000." }
    Write-Host "Open http://127.0.0.1:5173 in your browser. API: http://127.0.0.1:8000/docs"
    Write-Host "Press Ctrl+C to stop the demo servers."
    Set-Location (Join-Path $repoRoot "frontend")
    & $npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
    if ($LASTEXITCODE -ne 0) { throw "Frontend exited with code $LASTEXITCODE." }
} finally {
    if ($null -ne $backend -and -not $backend.HasExited) {
        # Windows venv Python can have a child interpreter. Stop the whole tree.
        & taskkill.exe /PID $backend.Id /T /F | Out-Null
        if (-not $backend.HasExited) { Stop-Process -Id $backend.Id }
        $backend.WaitForExit()
    }
    Pop-Location
}
