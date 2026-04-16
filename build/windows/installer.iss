#define MyAppName "AMRToMP3"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "crynocri"
#define MyAppExeName "AMRToMP3.exe"

#ifndef TargetArch
  #define TargetArch "amd64"
#endif

#if TargetArch == "arm64"
  #define InstallerArchitecturesAllowed "arm64"
  #define InstallerArchitecturesInstallMode "arm64"
#elif TargetArch == "amd64"
  #define InstallerArchitecturesAllowed "x64"
  #define InstallerArchitecturesInstallMode "x64"
#else
  #error Unsupported TargetArch. Expected amd64 or arm64.
#endif

[Setup]
AppId={{0A1A06C6-EA3F-4C95-A02C-4B87E9B9374B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\dist
OutputBaseFilename=AMRToMP3-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed={#InstallerArchitecturesAllowed}
ArchitecturesInstallIn64BitMode={#InstallerArchitecturesInstallMode}
ShowLanguageDialog=no
LanguageDetectionMethod=none

[Languages]
Name: "chinesesimplified"; MessagesFile: "languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\AMRToMP3.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\vendor\ffmpeg\ffmpeg.exe"; DestDir: "{app}\bin"; Flags: ignoreversion
Source: "..\..\vendor\ffmpeg\README.md"; DestDir: "{app}\licenses"; Flags: ignoreversion
Source: "..\..\build\windows\assets\context-menu-logo.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "install-shell"; Flags: runhidden waituntilterminated

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "uninstall-shell"; Flags: runhidden waituntilterminated
