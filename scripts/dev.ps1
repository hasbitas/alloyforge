# Start both local demo servers after installing the dependencies in README.md.
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv/Scripts/python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Create .venv and run: python -m pip install -e ".[dev]"'
}
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot "frontend/node_modules"))) {
    throw "Install frontend dependencies first: cd frontend; npm.cmd install"
}
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
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
    Write-Host "UI: http://127.0.0.1:5173 | API: http://127.0.0.1:8000/docs"
    Write-Host "Press Ctrl+C to stop the demo servers."
    Set-Location (Join-Path $repoRoot "frontend")
    & $npm run dev -- --host 127.0.0.1 --strictPort
    if ($LASTEXITCODE -ne 0) { throw "Frontend exited with code $LASTEXITCODE." }
} finally {
    if ($null -ne $backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id
    }
    Pop-Location
}
