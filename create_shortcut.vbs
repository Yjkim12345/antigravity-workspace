Set wshShell = WScript.CreateObject("WScript.Shell")
Set shortcut = wshShell.CreateShortcut("C:\Users\SAMSUNG\Desktop\새법리_입력기_작업표시줄고정용.lnk")
shortcut.TargetPath = "cmd.exe"
shortcut.Arguments = "/c ""C:\Users\SAMSUNG\Desktop\새법리_입력기.bat"""
shortcut.WindowStyle = 7
shortcut.IconLocation = "shell32.dll,21"
shortcut.Save
