param(
    [switch]$InstallTools,
    [switch]$SkipTests,
    [ValidateSet("amd64", "arm64")]
    [string]$TargetArch = "amd64"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param([Parameter(Mandatory = $true)][string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-ExternalCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $false)][string[]]$Arguments = @(),
        [Parameter(Mandatory = $false)][string]$FriendlyName = $FilePath
    )

    Write-Host "Running: $FriendlyName $($Arguments -join ' ')"
    & $FilePath @Arguments
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {
        $exitCode = 0
    }
    if ($exitCode -ne 0) {
        Write-Warning "$FriendlyName exited with code $exitCode"
        return $false
    }
    return $true
}

function Get-InnoSetupInstallLocationFromRegistry {
    $regPaths = @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1',
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1'
    )

    foreach ($regPath in $regPaths) {
        if (-not (Test-Path $regPath)) {
            continue
        }

        $installLocation = (Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue).InstallLocation
        if (-not [string]::IsNullOrWhiteSpace($installLocation)) {
            return $installLocation
        }

        $uninstallString = (Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue).UninstallString
        if (-not [string]::IsNullOrWhiteSpace($uninstallString)) {
            $matches = [regex]::Match($uninstallString, '"([^"]+)"')
            if ($matches.Success) {
                $exeDir = Split-Path -Parent $matches.Groups[1].Value
                if (-not [string]::IsNullOrWhiteSpace($exeDir)) {
                    return $exeDir
                }
            }
        }
    }

    return $null
}

function Resolve-IsccPath {
    $command = Get-Command iscc -ErrorAction SilentlyContinue
    if ($command -and $command.Source) {
        return $command.Source
    }

    $registryLocation = Get-InnoSetupInstallLocationFromRegistry
    if (-not [string]::IsNullOrWhiteSpace($registryLocation)) {
        $registryCandidate = Join-Path $registryLocation "ISCC.exe"
        if (Test-Path $registryCandidate) {
            return $registryCandidate
        }
    }

    $candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        "C:\Program Files\Inno Setup 5\ISCC.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Install-InnoSetup {
    if (Resolve-IsccPath) {
        return
    }

    $installed = $false
    if (Test-CommandExists -Name "winget") {
        Write-Host "Installing Inno Setup via winget..."
        $installed = Invoke-ExternalCommand -FilePath "winget" -FriendlyName "winget" -Arguments @(
            "install",
            "--id", "JRSoftware.InnoSetup",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--silent"
        )
    }

    if (-not $installed -and (Test-CommandExists -Name "choco")) {
        Write-Host "Installing Inno Setup via Chocolatey..."
        $installed = Invoke-ExternalCommand -FilePath "choco" -FriendlyName "choco" -Arguments @(
            "install", "innosetup", "-y", "--no-progress"
        )
    }

    if (-not $installed) {
        Write-Host "Installing Inno Setup via official installer..."
        $tempExe = Join-Path $env:TEMP "innosetup-installer.exe"
        $downloadUrls = @(
            "https://jrsoftware.org/download.php/is.exe",
            "https://files.jrsoftware.org/is/6/innosetup-6.3.3.exe"
        )

        $downloaded = $false
        foreach ($url in $downloadUrls) {
            try {
                Invoke-WebRequest -Uri $url -OutFile $tempExe -UseBasicParsing
                $downloaded = $true
                break
            }
            catch {
                Write-Warning ("Failed to download from {0}: {1}" -f $url, $_.Exception.Message)
            }
        }

        if (-not $downloaded) {
            throw "Unable to download Inno Setup installer."
        }

        $process = Start-Process -FilePath $tempExe -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-" -Wait -PassThru
        if ($process.ExitCode -ne 0) {
            throw "Inno Setup installer exited with code $($process.ExitCode)"
        }
    }

    if (-not (Resolve-IsccPath)) {
        throw "Inno Setup installation finished but ISCC.exe is still not found."
    }
}

function Ensure-Toolchain {
    if (-not $InstallTools) {
        return
    }

    if (-not (Test-CommandExists -Name "go")) {
        if (-not (Test-CommandExists -Name "winget")) {
            throw "Go is missing and winget is unavailable. Install Go manually first."
        }
        Write-Host "Installing Go..."
        [void](Invoke-ExternalCommand -FilePath "winget" -FriendlyName "winget" -Arguments @(
            "install",
            "--id", "GoLang.Go",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--silent"
        ))
    }

    if (-not (Resolve-IsccPath)) {
        Install-InnoSetup
    }

    if (-not (Test-CommandExists -Name "ffmpeg")) {
        if (Test-CommandExists -Name "choco") {
            Write-Host "Installing ffmpeg via Chocolatey..."
            [void](Invoke-ExternalCommand -FilePath "choco" -FriendlyName "choco" -Arguments @(
                "install", "ffmpeg", "-y", "--no-progress"
            ))
        }
        else {
            if (-not (Test-CommandExists -Name "winget")) {
                throw "ffmpeg is missing and neither choco nor winget is available."
            }
            Write-Host "Chocolatey is not available, installing ffmpeg via winget..."
            [void](Invoke-ExternalCommand -FilePath "winget" -FriendlyName "winget" -Arguments @(
                "install",
                "--id", "Gyan.FFmpeg",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent"
            ))
        }
    }
}

function Resolve-RealFfmpegPath {
    $ffmpegToolsDir = 'C:\ProgramData\chocolatey\lib\ffmpeg\tools'
    if (Test-Path $ffmpegToolsDir) {
        $realBinary = Get-ChildItem -Path $ffmpegToolsDir -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
        if ($realBinary) {
            return $realBinary
        }
    }

    $wingetPackagesRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path $wingetPackagesRoot) {
        $wingetBinary = Get-ChildItem -Path $wingetPackagesRoot -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
        if ($wingetBinary) {
            return $wingetBinary
        }
    }

    $command = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($command -and $command.Source) {
        return $command.Source
    }

    throw "ffmpeg.exe was not found. Install ffmpeg first or run with -InstallTools."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRootResolved = Resolve-Path (Join-Path $scriptDir "..\..")
$projectRoot = [System.IO.Path]::GetFullPath($projectRootResolved.ProviderPath)
$vendorDir = Join-Path $projectRoot "vendor\ffmpeg"
$bundledFfmpeg = Join-Path $vendorDir "ffmpeg.exe"
$buildScript = Join-Path $scriptDir "build.ps1"
$distExe = Join-Path $projectRoot "dist\AMRToMP3.exe"
$distSetup = Join-Path $projectRoot "dist\AMRToMP3-Setup.exe"

Write-Host "Project root: $projectRoot"
Write-Host "Packaging target architecture: $TargetArch"
Ensure-Toolchain

# Refresh PATH so newly installed tools are visible in this same session.
$machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = "$machinePath;$userPath"

if (-not (Test-CommandExists -Name "go")) {
    throw "go was not found in PATH."
}

$isccPath = Resolve-IsccPath
if (-not $isccPath) {
    throw "ISCC.exe (Inno Setup compiler) was not found. Try re-running with -InstallTools, or install Inno Setup manually and rerun."
}
Write-Host "Using Inno Setup compiler: $isccPath"
$isccDir = Split-Path -Parent $isccPath
$env:Path = "$isccDir;$env:Path"
$env:INNO_SETUP_ISCC = $isccPath

New-Item -ItemType Directory -Path $vendorDir -Force | Out-Null
$realFfmpeg = Resolve-RealFfmpegPath
Copy-Item $realFfmpeg $bundledFfmpeg -Force

Write-Host "Validating bundled ffmpeg: $bundledFfmpeg"
$versionOutput = & $bundledFfmpeg -version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Bundled ffmpeg failed to run: $bundledFfmpeg"
}
$versionOutput | Select-Object -First 1

Push-Location $projectRoot
try {
    if (-not $SkipTests) {
        Write-Host "Running Go tests..."
        & go test ./...
        if ($LASTEXITCODE -ne 0) {
            throw "Go tests failed."
        }

    }

    Write-Host "Running build script..."
    & powershell -ExecutionPolicy Bypass -File $buildScript -TargetArch $TargetArch
    if ($LASTEXITCODE -ne 0) {
        throw "Build script failed."
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path $distExe)) {
    throw "Expected file not found: $distExe"
}
if (-not (Test-Path $distSetup)) {
    throw "Expected file not found: $distSetup"
}

Write-Host ""
Write-Host "Packaging complete."
Get-Item $distExe, $distSetup | Select-Object FullName, Length, LastWriteTime
