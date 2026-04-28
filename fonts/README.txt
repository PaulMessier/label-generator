Place Aptos font files in this folder to enable the Aptos typeface in the label PDFs.
If the files are absent the app falls back to Helvetica automatically.

Required files (exact names):
  Aptos.ttf
  Aptos-Bold.ttf   (also accepted: AptosBold.ttf or AptosBd.ttf)

How to get the files
--------------------
OPTION A — Windows 11 23H2 or later (font already installed):
  Copy them from the system fonts folder:
    C:\Windows\Fonts\Aptos.ttf
    C:\Windows\Fonts\Aptos-Bold.ttf   (or similar — see below)
  PowerShell one-liner:
    Copy-Item "$env:WINDIR\Fonts\Aptos*.ttf" "." -ErrorAction SilentlyContinue

OPTION B — Older Windows or macOS/Linux:
  1. Apply Windows Updates. Aptos was added in the Windows 11 23H2 update (KB5031354).
  2. Alternatively, if you have access to another Windows 11 23H2+ machine, copy
     the .ttf files from its C:\Windows\Fonts\ folder.

OPTION C — Run the install helper (Windows only):
  From the label_generator\ folder with the venv active, run:
    python install_aptos.py
  This copies the font files automatically if they are found on the system.

Font licensing
--------------
Aptos is a Microsoft proprietary font distributed as part of Windows.
It is included here for convenience when you own a licensed copy of Windows.
Do NOT redistribute the font files independently.
