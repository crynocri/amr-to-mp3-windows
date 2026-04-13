Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
    [string]$InstallDir = "$env:LOCALAPPDATA\Programs\AMRToMP3",
    [ValidateSet("install", "uninstall")]
    [string]$Mode = "install"
)

$exePath = Join-Path $InstallDir "AMRToMP3.exe"
if (-not (Test-Path $exePath)) {
    throw "AMRToMP3.exe not found in install directory: $InstallDir"
}

$command = if ($Mode -eq "install") { "install-shell" } else { "uninstall-shell" }
Write-Host "Running $command using: $exePath"
& $exePath $command
if ($LASTEXITCODE -ne 0) {
    throw "AMRToMP3.exe $command failed with exit code $LASTEXITCODE"
}

Write-Host "$command completed."
