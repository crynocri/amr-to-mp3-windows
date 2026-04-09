Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..\..")
$specPath = Join-Path $scriptDir "amr_to_mp3.spec"
$bundledFfmpeg = Join-Path $projectRoot "vendor\ffmpeg\ffmpeg.exe"

Write-Host "Project root: $projectRoot"

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    throw "PyInstaller is not installed. Run: py -m pip install pyinstaller"
}

if (-not (Test-Path $bundledFfmpeg)) {
    Write-Warning "Bundled ffmpeg.exe was not found at $bundledFfmpeg"
    Write-Warning "The app can still build, but end users will need ffmpeg on PATH or AMR_TO_MP3_FFMPEG configured."
}

Push-Location $projectRoot
try {
    pyinstaller --noconfirm --clean $specPath
}
finally {
    Pop-Location
}
