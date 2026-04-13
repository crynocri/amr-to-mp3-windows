Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..\..")
$installerScript = Join-Path $scriptDir "installer.iss"
$bundledFfmpeg = Join-Path $projectRoot "vendor\ffmpeg\ffmpeg.exe"
$distDir = Join-Path $projectRoot "dist"
$outputExe = Join-Path $distDir "AMRToMP3.exe"
$goMainPackage = ".\cmd\amrtoolexe"

Write-Host "Project root: $projectRoot"

if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
    throw "Go is not installed. Install Go 1.23+ and ensure it is on PATH."
}

if (-not (Get-Command iscc -ErrorAction SilentlyContinue)) {
    throw "Inno Setup compiler (iscc) is not installed. Install Inno Setup and add iscc to PATH."
}

if (-not (Test-Path $bundledFfmpeg)) {
    throw "Bundled ffmpeg.exe was not found at $bundledFfmpeg"
}

Write-Host "Validating bundled ffmpeg binary: $bundledFfmpeg"
$versionOutput = & $bundledFfmpeg -version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Bundled ffmpeg.exe exists but is not runnable. Use the real ffmpeg binary instead of a package-manager shim."
}
$versionOutput | Select-Object -First 1

if (-not (Test-Path $distDir)) {
    New-Item -Path $distDir -ItemType Directory | Out-Null
}

Push-Location $projectRoot
try {
    Write-Host "Building Go executable..."
    & go build -trimpath -ldflags "-s -w" -o $outputExe $goMainPackage
    if ($LASTEXITCODE -ne 0) {
        throw "Go build failed."
    }

    if (-not (Test-Path $outputExe)) {
        throw "Expected executable was not generated: $outputExe"
    }

    Write-Host "Compiling installer..."
    & iscc $installerScript
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed."
    }
}
finally {
    Pop-Location
}
