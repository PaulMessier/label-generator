"""install_aptos.py — copy Aptos font files into the project fonts/ folder.

Run this once from the label_generator/ directory:
    python install_aptos.py

Searches: system fonts, per-user fonts, and the Office cloud font cache
(where Microsoft 365 stores Aptos on machines without a system-wide install).
Requires fonttools for cloud cache detection: pip install fonttools
"""

import os
import shutil
import sys

try:
    from fontTools.ttLib import TTFont as FTFont

    HAS_FONTTOOLS = True
except ImportError:
    HAS_FONTTOOLS = False

DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
LOCAL_APP = os.environ.get("LOCALAPPDATA", "")
ROAMING = os.environ.get("APPDATA", "")

ROOTS = [
    r"C:\Windows\Fonts",
    os.path.join(LOCAL_APP, "Microsoft", "Windows", "Fonts"),
    os.path.join(ROAMING, "Microsoft", "Windows", "Fonts"),
]

BOLD_VARIANTS = ["Aptos-Bold.ttf", "AptosBold.ttf", "AptosBd.ttf"]

# Office 365 cloud font cache (fonts have numeric filenames)
CLOUD_DIRS = [
    os.path.join(LOCAL_APP, "Microsoft", "FontCache", "4", "CloudFonts", "Aptos"),
]


def find_named_file(roots, name):
    for root in roots:
        p = os.path.join(root, name)
        if os.path.exists(p):
            return p
    return None


def find_in_cloud_cache(cache_dirs):
    """Scan Office cloud font cache; return (regular_path, bold_path) or (None, None)."""
    if not HAS_FONTTOOLS:
        return None, None
    regular = bold = None
    for d in cache_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if not fname.lower().endswith(".ttf"):
                continue
            path = os.path.join(d, fname)
            try:
                tt = FTFont(path)
                subfam = (tt["name"].getDebugName(2) or "").strip().lower()
                family = (tt["name"].getDebugName(1) or "").strip().lower()
                if family == "aptos":
                    if subfam == "regular" and regular is None:
                        regular = path
                    elif subfam == "bold" and bold is None:
                        bold = path
            except Exception:
                pass
        if regular and bold:
            break
    return regular, bold


os.makedirs(DEST, exist_ok=True)
errors = []

# --- Regular ---
reg = find_named_file(ROOTS, "Aptos.ttf")
if not reg:
    reg, _ = find_in_cloud_cache(CLOUD_DIRS)
if reg:
    shutil.copy2(reg, os.path.join(DEST, "Aptos.ttf"))
    print(f"Copied  {reg}  ->  fonts/Aptos.ttf")
else:
    errors.append("Aptos.ttf (Regular) not found.")

# --- Bold ---
bold = None
for name in BOLD_VARIANTS:
    bold = find_named_file(ROOTS, name)
    if bold:
        break
if not bold:
    _, bold = find_in_cloud_cache(CLOUD_DIRS)
if bold:
    shutil.copy2(bold, os.path.join(DEST, "Aptos-Bold.ttf"))
    print(f"Copied  {bold}  ->  fonts/Aptos-Bold.ttf")
else:
    errors.append("Aptos Bold not found.")

if errors:
    print("\nProblems:")
    for e in errors:
        print(f"  x {e}")
    if not HAS_FONTTOOLS:
        print("\n  Tip: install fonttools to enable Office cloud cache search:")
        print("       pip install fonttools")
    print("\nAptos ships with Windows 11 23H2+ and Microsoft 365.")
    print(
        "Apply Windows Updates or copy the .ttf files manually into the fonts/ folder."
    )
    sys.exit(1)
else:
    print("\nDone. Restart the Streamlit app to pick up the new fonts.")
