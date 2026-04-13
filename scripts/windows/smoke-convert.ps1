Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
    [string]$ExePath = ".\dist\AMRToMP3.exe"
)

if (-not (Test-Path $ExePath)) {
    throw "Packaged executable was not found at $ExePath"
}

$tempRoot = Join-Path $env:TEMP ("amr-to-mp3-smoke-" + [Guid]::NewGuid().ToString("N"))
New-Item -Path $tempRoot -ItemType Directory | Out-Null

try {
    $inputAmr = Join-Path $tempRoot "smoke.amr"
    $bytes = [byte[]](35,33,65,77,82,10,4,0,0,0,0,0,0,0,0,0,0,0,0)
    [System.IO.File]::WriteAllBytes($inputAmr, $bytes)

    & $ExePath convert --to mp3 --files $inputAmr
    if ($LASTEXITCODE -ne 0) {
        throw "Conversion command failed with exit code $LASTEXITCODE"
    }

    $outputMp3 = Join-Path $tempRoot "smoke.mp3"
    if (-not (Test-Path $outputMp3)) {
        throw "Expected output file was not generated: $outputMp3"
    }

    $size = (Get-Item $outputMp3).Length
    if ($size -le 0) {
        throw "Output file is empty: $outputMp3"
    }

    Write-Host "Smoke conversion succeeded: $outputMp3 ($size bytes)"
}
finally {
    if (Test-Path $tempRoot) {
        Remove-Item -Path $tempRoot -Force -Recurse
    }
}
