$ErrorActionPreference = "Stop"

$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Set-Location -LiteralPath $projectRoot

# Do not silently fall back to a global interpreter. The deployment environment
# must use the project's pinned PySide6/shiboken6 versions.
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Project virtual environment was not found: $python"
}

& $python -m pip install -e ".[build]"
if ($LASTEXITCODE -ne 0) {
    throw "Build dependency installation failed."
}

# Nuitka's Windows dependency scanner can corrupt non-ASCII paths while it
# inspects Qt plugins. Build from an ASCII staging directory, while preserving
# the exact packages from the project's virtual environment.
$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("ScalendarDeploy-" + [guid]::NewGuid().ToString("N"))
$stagePythonEnv = Join-Path $stage "env"
$stagePython = Join-Path $stagePythonEnv "Scripts\python.exe"
$stageCache = Join-Path $stage "cache"
$stageTemp = Join-Path $stageCache "temp"
New-Item -ItemType Directory -Path $stage, $stageCache, $stageTemp | Out-Null

try {
    & $python -m venv $stagePythonEnv
    if ($LASTEXITCODE -ne 0) {
        throw "ASCII deployment virtual environment creation failed."
    }

    $sourceSitePackages = Join-Path $projectRoot ".venv\Lib\site-packages"
    $targetSitePackages = Join-Path $stagePythonEnv "Lib\site-packages"
    Get-ChildItem -LiteralPath $sourceSitePackages -Force | Copy-Item -Destination $targetSitePackages -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot "src") -Destination $stage -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot "pysidedeploy.spec") -Destination (Join-Path $stage "pysidedeploy.spec") -Force

    $specPath = Join-Path $stage "pysidedeploy.spec"
    $specText = Get-Content -LiteralPath $specPath -Raw
    $specText = $specText -replace '(?m)^python_path\s*=.*$', ("python_path = " + $stagePython)
    Set-Content -LiteralPath $specPath -Value $specText -Encoding utf8

    # The copied environment has the Python packages but not console-script
    # launchers. This wrapper keeps qmlimportscanner on the same interpreter.
    $qmlScanner = Join-Path $stagePythonEnv "Scripts\pyside6-qmlimportscanner.cmd"
    Set-Content -LiteralPath $qmlScanner -Encoding ascii -Value @(
        "@echo off"
        ('"' + $stagePython + '" -c "from PySide6.scripts.pyside_tool import qmlimportscanner; qmlimportscanner()" %*')
    )

    $pathValue = (Join-Path $stagePythonEnv "Scripts") + ";" + $env:PATH
    $pipCache = Join-Path $stageCache "pip"
    $nuitkaCache = Join-Path $stageCache "nuitka"
    New-Item -ItemType Directory -Path $pipCache, $nuitkaCache | Out-Null

    # Warm up Nuitka's compiler/toolchain selection so its MinGW include tree
    # exists before the real deployment starts.
    $prewarmCode = "import os, subprocess; env=os.environ.copy(); env['PATH']=r'$pathValue'; env['PIP_CACHE_DIR']=r'$pipCache'; env['TEMP']=r'$stageTemp'; env['TMP']=r'$stageTemp'; env['NUITKA_CACHE_DIR']=r'$nuitkaCache'; raise SystemExit(subprocess.call([r'$stagePython','-m','nuitka','--mingw64','--assume-yes-for-downloads','--version'], env=env))"
    & $stagePython -c $prewarmCode
    if ($LASTEXITCODE -ne 0) {
        throw "Nuitka compiler preflight failed."
    }

    $mingwInclude = Get-ChildItem -LiteralPath (Join-Path $nuitkaCache "downloads\gcc") -Directory -Recurse -Filter include -ErrorAction SilentlyContinue |
        Where-Object {
            (Test-Path -LiteralPath (Join-Path $_.FullName "windows.h")) -and
            (Test-Path -LiteralPath (Join-Path $_.FullName "threadpoollegacyapiset.h"))
        } |
        Select-Object -First 1
    if (-not $mingwInclude) {
        throw "Nuitka MinGW Windows include directory was not found."
    }

    $deployScript = Join-Path $stagePythonEnv "Lib\site-packages\PySide6\scripts\deploy.py"
    $deployCode = "import os, subprocess; env=os.environ.copy(); env['PATH']=r'$pathValue'; env['PIP_CACHE_DIR']=r'$pipCache'; env['TEMP']=r'$stageTemp'; env['TMP']=r'$stageTemp'; env['NUITKA_CACHE_DIR']=r'$nuitkaCache'; env['C_INCLUDE_PATH']=r'$($mingwInclude.FullName)'; env['CPLUS_INCLUDE_PATH']=r'$($mingwInclude.FullName)'; raise SystemExit(subprocess.call([r'$stagePython',r'$deployScript','-c','pysidedeploy.spec','--force'], cwd=r'$stage', env=env))"
    & $stagePython -c $deployCode

    $stageDist = Join-Path $stage "build\pyside6\Scalendar.dist"
    $stageExe = Join-Path $stageDist "Scalendar.exe"
    if (-not (Test-Path -LiteralPath $stageExe)) {
        throw "pyside6-deploy did not produce a verified executable: $stageExe"
    }

    $releaseRoot = Join-Path $projectRoot "build\release"
    $releaseApp = Join-Path $releaseRoot "Scalendar"
    New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
    Copy-Item -LiteralPath $stageDist -Destination $releaseApp -Recurse -Force

    $requiredFiles = @(
        "Scalendar.exe",
        "shiboken6.abi3.dll",
        "shiboken6\Shiboken.pyd",
        "scalendar\ui\Main.qml",
        "scalendar\ui\Scalendar\Theme\qmldir",
        "PySide6\qt-plugins\platforms"
    )
    foreach ($relativePath in $requiredFiles) {
        $requiredPath = Join-Path $releaseApp $relativePath
        if (-not (Test-Path -LiteralPath $requiredPath)) {
            throw "Deployment output is incomplete; missing: $requiredPath"
        }
    }

    $smoke = Start-Process -FilePath (Join-Path $releaseApp "Scalendar.exe") -WorkingDirectory $releaseApp -PassThru
    try {
        Start-Sleep -Seconds 8
        if ($smoke.HasExited) {
            throw "Packaged Scalendar exited during the smoke test with code $($smoke.ExitCode)."
        }
    }
    finally {
        if (-not $smoke.HasExited) {
            Stop-Process -Id $smoke.Id -Force
        }
    }

    Write-Output "Build completed: $(Join-Path $releaseApp 'Scalendar.exe')"
}
finally {
    if (Test-Path -LiteralPath $stage) {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
}
