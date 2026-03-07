import os

vbs_code = '''
Set wshShell = WScript.CreateObject("WScript.Shell")
Set shortcut = wshShell.CreateShortcut("C:\\Users\\SAMSUNG\\Desktop\\새법리_입력기_작업표시줄고정용.lnk")
shortcut.TargetPath = "cmd.exe"
shortcut.Arguments = "/c ""C:\\Users\\SAMSUNG\\Desktop\\새법리_입력기.bat"""
shortcut.WindowStyle = 7
shortcut.IconLocation = "shell32.dll,21"
shortcut.Save
'''

with open("temp_shortcut.vbs", "w", encoding="euc-kr") as f:
    f.write(vbs_code)

os.system("cscript temp_shortcut.vbs")
os.remove("temp_shortcut.vbs")
print("Shortcut created.")
