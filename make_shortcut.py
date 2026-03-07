import os

desktop_path = os.path.join(os.environ["USERPROFILE"], "OneDrive", "Desktop")
shortcut_path = os.path.join(desktop_path, "새법리_입력기_작업표시줄고정용.lnk")
target_path = os.path.join(desktop_path, "새법리_입력기.bat")

vbs_code = f'''
Set wshShell = WScript.CreateObject("WScript.Shell")
Set shortcut = wshShell.CreateShortcut("{shortcut_path}")
shortcut.TargetPath = "cmd.exe"
shortcut.Arguments = "/c ""{target_path}"""
shortcut.WindowStyle = 7
shortcut.IconLocation = "shell32.dll,21"
shortcut.Save
'''

with open("temp_shortcut.vbs", "w", encoding="euc-kr") as f:
    f.write(vbs_code)

os.system("cscript temp_shortcut.vbs")
os.remove("temp_shortcut.vbs")
print("Shortcut created.")
