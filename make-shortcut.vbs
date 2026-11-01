Option Explicit
Dim shell, fso, folder, shortcut
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
Set shortcut = shell.CreateShortcut(shell.SpecialFolders("Desktop") & "\Phone Speaker Bridge.lnk")
shortcut.TargetPath = shell.ExpandEnvironmentStrings("%ComSpec%")
shortcut.Arguments = "/c """ & folder & "\start.cmd"""
shortcut.WorkingDirectory = folder
shortcut.WindowStyle = 1
shortcut.Description = "Use your phone as a WiFi speaker for your Windows PC"
shortcut.Save
WScript.Echo "Desktop shortcut created."
