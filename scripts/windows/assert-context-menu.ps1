param(
    [string]$RootKey = 'HKCU:\Software\Classes\SystemFileAssociations\.amr\shell\AMRToMP3.Convert',
    [string]$ExpectedParentLabel = '格式转换'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-RegistryKey([string]$Path) {
    if (-not (Test-Path $Path)) {
        throw "Missing registry key: $Path"
    }
}

function Assert-RegistryValue([string]$Path, [string]$Name, [string]$ExpectedValue) {
    $properties = Get-ItemProperty -Path $Path
    $actualValue = $properties.$Name
    if ($null -eq $actualValue) {
        throw "Missing registry value '$Name' on key: $Path"
    }
    if ($actualValue -ne $ExpectedValue) {
        throw "Unexpected value for '$Name' at $Path. Expected '$ExpectedValue' but got '$actualValue'"
    }
}

Assert-RegistryKey -Path $RootKey
Assert-RegistryValue -Path $RootKey -Name "MUIVerb" -ExpectedValue $ExpectedParentLabel

$verbs = @(
    @{ Key = "to_mp3"; Label = "转换为 MP3"; To = "mp3" },
    @{ Key = "to_wav"; Label = "转换为 WAV"; To = "wav" },
    @{ Key = "to_aac"; Label = "转换为 AAC"; To = "aac" },
    @{ Key = "to_m4a"; Label = "转换为 M4A"; To = "m4a" }
)

foreach ($verb in $verbs) {
    $verbKey = Join-Path $RootKey "shell\$($verb.Key)"
    $commandKey = Join-Path $verbKey "command"
    Assert-RegistryKey -Path $verbKey
    Assert-RegistryValue -Path $verbKey -Name "MUIVerb" -ExpectedValue $verb.Label
    Assert-RegistryKey -Path $commandKey

    $command = (Get-ItemProperty -Path $commandKey).'(default)'
    if ($null -eq $command) {
        $command = (Get-ItemProperty -Path $commandKey).'(Default)'
    }
    if ($null -eq $command) {
        throw "Missing default command at key: $commandKey"
    }
    if ($command -notmatch "AMRToMP3\.exe") {
        throw "Verb $($verb.Key) command should invoke AMRToMP3.exe. Actual: $command"
    }
    if ($command -notmatch "--to\s+$($verb.To)\b") {
        throw "Verb $($verb.Key) command should include '--to $($verb.To)'. Actual: $command"
    }
    if ($command -notmatch "--files") {
        throw "Verb $($verb.Key) command should include '--files'. Actual: $command"
    }
}

Write-Host "Context menu registry assertions passed."
