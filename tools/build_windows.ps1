$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Project virtual environment and system Python were not found."
    }
    $python = $pythonCommand.Source
}

& $python -m pip install -e ".[build]"
if ($LASTEXITCODE -ne 0) {
    throw "Build dependency installation failed."
}

& $python -m PyInstaller --noconfirm --clean --windowed --name Scalendar --paths src --add-data 'src\scalendar\ui;scalendar\ui' --distpath 'build\dist' --workpath 'build\pyinstaller' 'src\scalendar\main.py'
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

$exe = Join-Path $projectRoot "build\dist\Scalendar\Scalendar.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    throw "Build completed but EXE was not found: $exe"
}
Write-Output "Build completed: $exe"
