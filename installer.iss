; LeroLero Inno Setup Installer
; Compile with Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; Version is injected by CI via /D flag: iscc /DMyAppVersion=X.Y.Z

#define MyAppName "LeroLero"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppPublisher "LeroLero"
#define MyAppURL "https://github.com/nicolasf9/lerolero"
#define MyAppExeName "LeroLero.exe"

[Setup]
AppId={{B3F7E8A1-9C4D-4E2B-A6F0-1D8E3C5B7A92}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=LeroLero-{#MyAppVersion}-setup
SetupIconFile=src\lerolero\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na &Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked
Name: "startup"; Description: "Iniciar {#MyAppName} com o &Windows"; GroupDescription: "Opções:"
Name: "cleandata"; Description: "Limpar dados anteriores (configurações, modelos, histórico)"; GroupDescription: "Reinstalação limpa:"; Flags: unchecked

[Files]
Source: "dist\LeroLero\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Windows startup entry (only if task selected)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "LeroLero"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startup

[InstallDelete]
; Clean AppData if user selected "cleandata" task
Type: filesandordirs; Name: "{userappdata}\LeroLero\config.json"; Tasks: cleandata
Type: filesandordirs; Name: "{userappdata}\LeroLero\deps"; Tasks: cleandata
Type: filesandordirs; Name: "{userappdata}\LeroLero\python"; Tasks: cleandata
Type: filesandordirs; Name: "{userappdata}\LeroLero\history"; Tasks: cleandata
Type: filesandordirs; Name: "{userappdata}\LeroLero\lerolero.log"; Tasks: cleandata
Type: filesandordirs; Name: "{userappdata}\LeroLero\setup_log.txt"; Tasks: cleandata

[UninstallDelete]
; Always clean AppData on uninstall
Type: filesandordirs; Name: "{userappdata}\LeroLero"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent
