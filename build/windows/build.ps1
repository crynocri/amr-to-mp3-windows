Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Parse-GoVersion {
    param([Parameter(Mandatory = $true)][string]$VersionText)

    $match = [regex]::Match($VersionText, 'go version go(\d+)\.(\d+)')
    if (-not $match.Success) {
        return $null
    }

    return [PSCustomObject]@{
        Major = [int]$match.Groups[1].Value
        Minor = [int]$match.Groups[2].Value
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRootResolved = Resolve-Path (Join-Path $scriptDir "..\..")
$projectRoot = [System.IO.Path]::GetFullPath($projectRootResolved.ProviderPath)
$buildRoot = $projectRoot
$tempWorkspace = $null

$installerScript = Join-Path $buildRoot "build\windows\installer.iss"
$bundledFfmpeg = Join-Path $buildRoot "vendor\ffmpeg\ffmpeg.exe"
$distDir = Join-Path $buildRoot "dist"
$sourceDistDir = Join-Path $projectRoot "dist"
$outputExe = Join-Path $distDir "AMRToMP3.exe"
$goMainPackage = ".\cmd\amrtoolexe"
$isccCommand = $env:INNO_SETUP_ISCC

Write-Host "Project root: $projectRoot"
if ($projectRoot.StartsWith("\\")) {
    # Go build on UNC paths can fail; build in a local mirror and copy artifacts back.
    $tempWorkspace = Join-Path $env:TEMP ("amr-to-mp3-build-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempWorkspace | Out-Null
    Write-Host "UNC path detected. Mirroring project to temp workspace: $tempWorkspace"

    $robocopyOutput = & robocopy $projectRoot $tempWorkspace /MIR /XD .git .worktrees artifacts /NFL /NDL /NJH /NJS /NP 2>&1
    $robocopyExitCode = $LASTEXITCODE
    if ($robocopyOutput) {
        $robocopyOutput | ForEach-Object { Write-Host $_ }
    }
    if ($robocopyExitCode -gt 7) {
        throw "Failed to mirror project to local temp workspace (robocopy exit code: $robocopyExitCode)."
    }

    $buildRoot = $tempWorkspace
    $installerScript = Join-Path $buildRoot "build\windows\installer.iss"
    $bundledFfmpeg = Join-Path $buildRoot "vendor\ffmpeg\ffmpeg.exe"
    $distDir = Join-Path $buildRoot "dist"
    $outputExe = Join-Path $distDir "AMRToMP3.exe"
    Write-Host "Using local build workspace: $buildRoot"
}
$goVersionText = (& go version)
Write-Host ("Go version: " + $goVersionText)

$goVersionParsed = Parse-GoVersion -VersionText $goVersionText
if (-not $goVersionParsed) {
    throw "Unable to parse Go version output: $goVersionText"
}
if (($goVersionParsed.Major -lt 1) -or (($goVersionParsed.Major -eq 1) -and ($goVersionParsed.Minor -lt 23))) {
    throw "Go 1.23+ is required by go.mod, but current version is: $goVersionText"
}

if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
    throw "Go is not installed. Install Go 1.23+ and ensure it is on PATH."
}

if ([string]::IsNullOrWhiteSpace($isccCommand)) {
    $isccResolved = Get-Command iscc -ErrorAction SilentlyContinue
    if (-not $isccResolved) {
        throw "Inno Setup compiler (iscc) is not installed. Install Inno Setup and add iscc to PATH."
    }
    $isccCommand = $isccResolved.Source
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

Push-Location $buildRoot
try {
    Write-Host "Building Go executable..."
    $goBuildOutput = & go build -trimpath -ldflags "-s -w" -o $outputExe $goMainPackage 2>&1
    $goBuildExitCode = $LASTEXITCODE
    if ($goBuildOutput) {
        $goBuildOutput | ForEach-Object { Write-Host $_ }
    }
    if ($goBuildExitCode -ne 0) {
        $message = "Go build failed."
        if ($goBuildOutput) {
            $message += [Environment]::NewLine + ($goBuildOutput -join [Environment]::NewLine)
        }
        throw $message
    }

    if (-not (Test-Path $outputExe)) {
        throw "Expected executable was not generated: $outputExe"
    }

    Write-Host "Compiling installer..."
    & $isccCommand $installerScript
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed."
    }
}
finally {
    Pop-Location
    if ($tempWorkspace -and (Test-Path $tempWorkspace)) {
        New-Item -ItemType Directory -Path $sourceDistDir -Force | Out-Null
        $tempDistExe = Join-Path $tempWorkspace "dist\AMRToMP3.exe"
        $tempDistSetup = Join-Path $tempWorkspace "dist\AMRToMP3-Setup.exe"

        if (Test-Path $tempDistExe) {
            Copy-Item $tempDistExe (Join-Path $sourceDistDir "AMRToMP3.exe") -Force
        }
        if (Test-Path $tempDistSetup) {
            Copy-Item $tempDistSetup (Join-Path $sourceDistDir "AMRToMP3-Setup.exe") -Force
        }

        Remove-Item -Path $tempWorkspace -Recurse -Force -ErrorAction SilentlyContinue
    }
}
