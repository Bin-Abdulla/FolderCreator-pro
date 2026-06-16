[Setup]
AppName=Folder Creator
AppVersion=1.0
AppPublisher=Ahmed Abdulla
AppPublisherURL=https://github.com
DefaultDirName={autopf}\FolderCreator
DefaultGroupName=Folder Creator
OutputBaseFilename=FolderCreator_Setup
OutputDir=output
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\FolderCreator.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checked

[Files]
Source: "dist\FolderCreator.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Folder Creator"; Filename: "{app}\FolderCreator.exe"
Name: "{group}\Uninstall Folder Creator"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Folder Creator"; Filename: "{app}\FolderCreator.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\FolderCreator.exe"; Description: "Launch Folder Creator"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/f /im FolderCreator.exe"; Flags: runhidden
