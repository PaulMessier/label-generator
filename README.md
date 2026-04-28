# Label Generator

Generates PDF sheets of photographic paper sample labels with diamond-shaped data glyphs.  
Built with Streamlit — runs entirely in a browser, no Jupyter or VS Code required.

---

## Requirements

- **Python 3.10 or later** ([python.org/downloads](https://www.python.org/downloads/))
- **pip** (included with Python)
- Internet access for the first install (to download packages)
- Windows, macOS, or Linux

> **Optional — Aptos font (Windows only)**  
> The app uses Aptos for label text. On Windows it is typically pre-installed.  
> If it is not present the app automatically falls back to Helvetica (visually equivalent to Arial).
> You can verify by checking for `C:\Windows\Fonts\Aptos.ttf`.

---

## Installation

Open a terminal (PowerShell, Command Prompt, or Terminal) and run:

```bash
# 1. (Recommended) Create an isolated virtual environment
python -m venv .venv

# 2. Activate it
#    Windows PowerShell:
.venv\Scripts\Activate.ps1
#    Windows Command Prompt:
.venv\Scripts\activate.bat
#    macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

> If PowerShell blocks script execution, run this first:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
> ```

---

## Running the App

From the `label_generator/` folder with the virtual environment active:

```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.  
To share on a local network, use the **Network URL** printed in the terminal.

---

## Using the App

### Sidebar inputs

| Field | What to provide |
|---|---|
| **Upload CSV file** | Your sample data CSV (see format below) |
| **Working directory** | An existing folder on this machine — glyph PNGs are written here |
| **Output folder** | Where the finished PDF is saved (created automatically if absent) |
| **Upload key image** | Optional PNG/JPG — appears in the bottom-right cell of every page |

Working directory and output folder are **remembered between sessions** in `label_generator_config.json`.

### Process

1. Fill in all sidebar fields
2. Click **🚀 Process Labels**
3. Download the PDF with the **⬇️ Download PDF** button, or find it directly in your output folder

The PDF is named `Labels_MMDDYYYY.pdf` (e.g., `Labels_04282026.pdf`).

---

## CSV Format

The CSV must contain these columns (extra columns are ignored):

| Column | Type | Notes |
|---|---|---|
| `CatalogNumber` | text | Used to name glyph files; must be unique |
| `Manufacturer` | text | Warning shown if blank |
| `Brand` | text | Optional |
| `Year` | number | Page breaks occur between years |
| `Surface` | text | |
| `TextureDescription` | text | |
| `GlossDescription` | text | |
| `ColorDescription` | text | |
| `ThicknessDescription` | text | |
| `Roughness` | number | Glyph bottom axis; range 0.005–0.373 |
| `GlossUnits` | number | Glyph right axis (inverted); range 0.19–123.55 |
| `WarmthAtDmin` | number | Glyph top axis (b*); range −6.13–31.45 |
| `Thickness_mm` | number | Glyph left axis; range 0.011–0.458 |
| `Fluorescence` | number | AUC; values > 1.75 trigger bright glyph border |
| `DateIsApproximate` | text | |
| `IsResinCoated` | text | |
| `HasProcessingInstructions` | text | |
| `Backprint` | text | Blank displays as "none" |

Missing numeric values:
- **1 missing axis** → that axis collapses to 0 (triangle shape)
- **3 or more missing axes** → no glyph drawn for that label

---

## Output Structure

After a run, the working directory will contain:

```
<working_dir>/
  Radar Charts/          ← glyphs with reference gridlines
  Diamond Glyphs/        ← clean diamond glyphs (used in PDF)
  key.png                ← copied here if you uploaded one
```

Both glyph folders are **fully replaced on every run** — no stale files accumulate.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` with the venv active |
| PowerShell won't run `.ps1` | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` first |
| Glyph folders not created | Make sure the working directory path exists and you have write permission |
| PDF not found | Check the output folder path; the app creates it but must have write permission |
| Labels show "NaN" for numeric fields | Those values are genuinely missing in the CSV — this is expected behaviour |
| App doesn't reload after a code change | Click **Rerun** in the top-right banner of the Streamlit browser tab |

---

## For Agents / Developers

See [ARCHIVE.md](ARCHIVE.md) for:
- Full project intent and initiating prompt
- All design decisions with rationale
- Current constants (colors, font sizes, glyph geometry)
- Complete change log
