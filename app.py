"""Label Generator — Streamlit App

Usage:
    streamlit run app.py

Requires:
    pip install -r requirements.txt
"""

import io
import os
import json
import math
import datetime
import tempfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import streamlit as st

# ============================================================
# PERSISTENT CONFIG
# ============================================================
_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "label_generator_config.json"
)


def _load_config():
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"working_dir": "", "output_dir": ""}


def _save_config(working_dir, output_dir):
    try:
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"working_dir": working_dir, "output_dir": output_dir}, f)
    except Exception:
        pass


# ============================================================
# CONSTANTS
# ============================================================
REQUIRED_FIELDS = [
    "CatalogNumber",
    "Manufacturer",
    "Brand",
    "Year",
    "Surface",
    "TextureDescription",
    "GlossDescription",
    "ColorDescription",
    "ThicknessDescription",
    "Roughness",
    "GlossUnits",
    "WarmthAtDmin",
    "Thickness_mm",
    "Fluorescence",
    "DateIsApproximate",
    "IsResinCoated",
    "HasProcessingInstructions",
    "Backprint",
]

NORM_RANGES = {
    "bstar_base": {"lower": -6.13, "upper": 31.45},
    "gloss": {"lower": 0.19, "upper": 123.55},
    "roughness": {"lower": 0.005, "upper": 0.373},
    "thickness": {"lower": 0.011, "upper": 0.458},
}

GLYPH_FILL = "#DCEAF7"
GLYPH_BORDER_NORMAL = "#104862"
GLYPH_BORDER_HIGH_FLUOR = "#104862"
GLYPH_LINEWIDTH_NORMAL = 0.3  # hairline
GLYPH_LINEWIDTH_HIGH_FLUOR = 0.6  # double for bright samples
FLUOR_THRESHOLD = 1.75

PAGE_W_IN = 8.5
PAGE_H_IN = 11.0
MARGIN_MM = 6.0
COLS = 3
ROWS = 4
SQUARE_CM = 6.5
LABELS_PER_PAGE = COLS * ROWS - 1  # 11
KEY_COL, KEY_ROW = COLS - 1, ROWS - 1
KEY_FILENAME = "key.png"
SORT_COLUMNS = ["Year", "Manufacturer", "Brand", "Surface", "Roughness"]
TEXT_FONT_SIZE = 9.5
PM_FONT_SIZE = 10.5
TEXT_MARGIN = 2 * mm
PM_MARGIN = 1.5 * mm

PAGE_W = PAGE_W_IN * 72
PAGE_H = PAGE_H_IN * 72
MARGIN = MARGIN_MM * mm
SQUARE = SQUARE_CM * cm
# Centre the grid horizontally; keep the original vertical margin.
GRID_LEFT = (PAGE_W - COLS * SQUARE) / 2
GRID_TOP = PAGE_H - MARGIN
GRID_RIGHT = GRID_LEFT + COLS * SQUARE
GRID_BOTTOM = GRID_TOP - ROWS * SQUARE

# ============================================================
# FONT SETUP
# ============================================================
_fonts_registered = False
FONT_NAME = "Helvetica"
FONT_BOLD_NAME = "Helvetica-Bold"

# Local fonts/ folder bundled with the project (highest priority)
_LOCAL_FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def _register_fonts():
    global _fonts_registered, FONT_NAME, FONT_BOLD_NAME
    if _fonts_registered:
        return
    user_fonts = os.path.join(
        os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"
    )
    # --- Aptos candidates (preferred) ---
    aptos_candidates = [
        # Bundled local fonts/ folder — copy files here for portable installs
        (
            os.path.join(_LOCAL_FONTS, "Aptos.ttf"),
            os.path.join(_LOCAL_FONTS, "Aptos-Bold.ttf"),
        ),
        (
            os.path.join(_LOCAL_FONTS, "Aptos.ttf"),
            os.path.join(_LOCAL_FONTS, "AptosBold.ttf"),
        ),
        (
            os.path.join(_LOCAL_FONTS, "Aptos.ttf"),
            os.path.join(_LOCAL_FONTS, "AptosBd.ttf"),
        ),
        # Windows system-wide installation
        (r"C:\Windows\Fonts\Aptos.ttf", r"C:\Windows\Fonts\Aptos-Bold.ttf"),
        (r"C:\Windows\Fonts\Aptos.ttf", r"C:\Windows\Fonts\AptosBold.ttf"),
        (r"C:\Windows\Fonts\Aptos.ttf", r"C:\Windows\Fonts\AptosBd.ttf"),
        # Windows per-user installation
        (
            os.path.join(user_fonts, "Aptos.ttf"),
            os.path.join(user_fonts, "Aptos-Bold.ttf"),
        ),
        (
            os.path.join(user_fonts, "Aptos.ttf"),
            os.path.join(user_fonts, "AptosBold.ttf"),
        ),
        (
            os.path.join(user_fonts, "Aptos.ttf"),
            os.path.join(user_fonts, "AptosBd.ttf"),
        ),
    ]
    for reg, bold in aptos_candidates:
        if os.path.exists(reg) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("Aptos", reg))
            pdfmetrics.registerFont(TTFont("Aptos-Bold", bold))
            FONT_NAME = "Aptos"
            FONT_BOLD_NAME = "Aptos-Bold"
            _fonts_registered = True
            return
    # --- Arial TrueType fallback (crisper in PDFs than Helvetica outline) ---
    arial_candidates = [
        (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
        (
            os.path.join(user_fonts, "arial.ttf"),
            os.path.join(user_fonts, "arialbd.ttf"),
        ),
        ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
        (
            "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
        ),
    ]
    for reg, bold in arial_candidates:
        if os.path.exists(reg) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("Arial", reg))
            pdfmetrics.registerFont(TTFont("Arial-Bold", bold))
            FONT_NAME = "Arial"
            FONT_BOLD_NAME = "Arial-Bold"
            break
    _fonts_registered = True


# ============================================================
# NORMALIZATION
# ============================================================
def _is_missing(val):
    """Return True if val is None, empty string, or NaN."""
    if val is None:
        return True
    try:
        return np.isnan(float(val))
    except (TypeError, ValueError):
        s = str(val).strip()
        return s == "" or s.lower() == "nan"


def _normalize(value, lower, upper, invert=False):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.1
    if np.isnan(v):
        return 0.1
    n = (v - lower) / (upper - lower)
    if invert:
        n = 1.0 - n
    return float(np.clip(n, 0.1, 1.0))


def _compute_glyph_values(row):
    """
    Returns ((top, right, bottom, left), missing_count).
    Missing values become 0.0 (collapses that axis, rendering as triangle).
    Callers should skip rendering entirely when missing_count >= 3.
    """
    axes = [
        ("WarmthAtDmin", NORM_RANGES["bstar_base"], False),
        ("GlossUnits", NORM_RANGES["gloss"], True),
        ("Roughness", NORM_RANGES["roughness"], False),
        ("Thickness_mm", NORM_RANGES["thickness"], False),
    ]
    vals, missing_count = [], 0
    for field, rng, invert in axes:
        raw = row.get(field)
        if _is_missing(raw):
            vals.append(0.0)
            missing_count += 1
        else:
            vals.append(_normalize(raw, rng["lower"], rng["upper"], invert=invert))
    return tuple(vals), missing_count


# ============================================================
# GLYPH RENDERING
# ============================================================
def _render_glyph_png(
    top, right, bottom, left, border_color, fill_color, linewidth=0.3, radar=False
):
    dpi = 150
    size_in = 300 / dpi  # 2.0 in → exact 300×300 px at 150 dpi
    fig = plt.figure(figsize=(size_in, size_in), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])  # axes fill entire figure — no whitespace
    ax.set_facecolor("none")
    fig.patch.set_alpha(0.0)
    cx, cy = 0.5, 0.5
    sf = 0.495  # value=1.0 reaches 99% of half-width → effectively edge-to-edge
    pts = [
        (cx, cy + top * sf),
        (cx + right * sf, cy),
        (cx, cy - bottom * sf),
        (cx - left * sf, cy),
    ]
    if radar:
        for lv in [0.2, 0.4, 0.6, 0.8, 1.0]:
            gpts = [
                (cx, cy + lv * sf),
                (cx + lv * sf, cy),
                (cx, cy - lv * sf),
                (cx - lv * sf, cy),
            ]
            ax.add_patch(
                Polygon(
                    gpts,
                    closed=True,
                    facecolor="none",
                    edgecolor="#888888",
                    linewidth=0.5,
                    alpha=0.4,
                    zorder=1,
                )
            )
        for ep in [(cx, cy + sf), (cx + sf, cy), (cx, cy - sf), (cx - sf, cy)]:
            ax.plot(
                [cx, ep[0]],
                [cy, ep[1]],
                color="#888888",
                linewidth=0.8,
                alpha=0.5,
                zorder=2,
            )
    ax.add_patch(
        Polygon(
            pts,
            closed=True,
            facecolor=fill_color,
            edgecolor=border_color,
            linewidth=linewidth,
            alpha=1.0,
            zorder=5,
        )
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(
        buf, format="png", transparent=True, dpi=dpi
    )  # no bbox_inches — preserves exact square
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_glyphs(df, working_dir, st_progress=None):
    """Generate radar + diamond PNGs. Adds radar_path, diamond_path columns.

    Folders are cleared before each run so stale files are never retained.
    Rows with 3+ missing glyph values receive None paths (no glyph drawn).
    """
    import shutil

    radar_dir = os.path.join(working_dir, "Radar Charts")
    diamond_dir = os.path.join(working_dir, "Diamond Glyphs")
    # Always clear and recreate to overwrite stale files
    for d in [radar_dir, diamond_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)
    r_paths, d_paths = [], []
    n = len(df)
    for i, (_, row) in enumerate(df.iterrows()):
        cat = str(row["CatalogNumber"]).replace("/", "_").replace("\\", "_")
        fluor = pd.to_numeric(row.get("Fluorescence", np.nan), errors="coerce")
        is_high_fluor = not np.isnan(fluor) and fluor > FLUOR_THRESHOLD
        border = GLYPH_BORDER_HIGH_FLUOR if is_high_fluor else GLYPH_BORDER_NORMAL
        linewidth = (
            GLYPH_LINEWIDTH_HIGH_FLUOR if is_high_fluor else GLYPH_LINEWIDTH_NORMAL
        )
        (top, right, bottom, left), missing_count = _compute_glyph_values(row)
        if missing_count >= 3:
            # Too many missing values — skip glyph entirely for this label
            r_paths.append(None)
            d_paths.append(None)
        else:
            r_path = os.path.join(radar_dir, f"{cat}.png")
            d_path = os.path.join(diamond_dir, f"{cat}.png")
            buf = _render_glyph_png(
                top,
                right,
                bottom,
                left,
                border,
                GLYPH_FILL,
                linewidth=linewidth,
                radar=True,
            )
            with open(r_path, "wb") as f:
                f.write(buf.read())
            buf = _render_glyph_png(
                top,
                right,
                bottom,
                left,
                border,
                GLYPH_FILL,
                linewidth=linewidth,
                radar=False,
            )
            with open(d_path, "wb") as f:
                f.write(buf.read())
            r_paths.append(r_path)
            d_paths.append(d_path)
        if st_progress is not None:
            st_progress.progress((i + 1) / n, text=f"Generating glyphs {i + 1}/{n}...")
    df = df.copy()
    df["radar_path"] = r_paths
    df["diamond_path"] = d_paths
    return df


# ============================================================
# VALIDATION
# ============================================================
def validate_csv(df):
    errors, warnings = [], []
    missing = [f for f in REQUIRED_FIELDS if f not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
        return False, warnings, errors
    # Only warn on missing Manufacturer; Brand is commonly absent and not required.
    for field in ["Manufacturer"]:
        mask = (
            df[field].isna()
            | (df[field].astype(str).str.strip() == "")
            | (df[field].astype(str).str.lower() == "nan")
        )
        if mask.any():
            bad = df.loc[mask, "CatalogNumber"].tolist()
            warnings.append(
                f"Blank {field} in CatalogNumber(s): {', '.join(str(c) for c in bad)}"
            )
    return True, warnings, errors


# ============================================================
# SORT
# ============================================================
def sort_dataframe(df):
    sc = [c for c in SORT_COLUMNS if c in df.columns]
    if not sc:
        return df
    df = df.copy()
    if "Year" in df.columns:
        df["_year_sort"] = pd.to_numeric(df["Year"], errors="coerce")
        sc = ["_year_sort"] + [c for c in sc if c != "Year"]
    df = df.sort_values(sc, na_position="last")
    df.drop(columns=["_year_sort"], inplace=True, errors="ignore")
    return df.reset_index(drop=True)


def build_pages(df):
    pages = []
    df["_year_key"] = df["Year"].astype(str)
    for year_key, group in df.groupby("_year_key", sort=False):
        records = group.drop(columns=["_year_key"]).to_dict("records")
        for i in range(0, max(1, len(records)), LABELS_PER_PAGE):
            chunk = records[i : i + LABELS_PER_PAGE]
            chunk += [None] * (LABELS_PER_PAGE - len(chunk))
            pages.append({"year": year_key, "rows": chunk})
    df.drop(columns=["_year_key"], inplace=True, errors="ignore")
    return pages


# ============================================================
# LABEL TEXT
# ============================================================
def _safe(val, fallback="NaN"):
    if val is None:
        return fallback
    s = str(val).strip()
    return fallback if s == "" or s.lower() == "nan" else s


def _safe_text(val):
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def _build_surface_line(row):
    parts = [
        _safe_text(row.get(k, ""))
        for k in [
            "Surface",
            "TextureDescription",
            "GlossDescription",
            "ColorDescription",
            "ThicknessDescription",
        ]
    ]
    ne = [p for p in parts if p]
    if not ne:
        return "Surface: "
    return f"Surface: {ne[0]}" + (f" - {', '.join(ne[1:])}" if len(ne) > 1 else "")


def _fmt_with_unit(val, unit):
    """Format a numeric field with its unit. If the value is NaN, omit the unit suffix."""
    s = _safe(val)
    return s if s == "NaN" else f"{s} {unit}"


def _build_label_lines(row):
    mfr = _safe_text(row.get("Manufacturer", ""))
    brand = _safe_text(row.get("Brand", ""))
    header = ", ".join(p for p in [mfr, brand] if p)
    return [
        (header, True),
        (_build_surface_line(row), False),
        (f"Texture: {_fmt_with_unit(row.get('Roughness'), 'Sq')}", False),
        (f"Reflectance: {_fmt_with_unit(row.get('GlossUnits'), 'GU')}", False),
        (f"Base color: {_fmt_with_unit(row.get('WarmthAtDmin'), 'b*')}", False),
        (f"Thickness: {_fmt_with_unit(row.get('Thickness_mm'), 'mm')}", False),
        (f"Fluor: {_fmt_with_unit(row.get('Fluorescence'), 'AUC')}", False),
        (
            f"Year is apx: {_safe_text(row.get('DateIsApproximate', '')) or 'NaN'}",
            False,
        ),
        (f"RC: {_safe_text(row.get('IsResinCoated', '')) or 'NaN'}", False),
        (
            f"Instructions: {_safe_text(row.get('HasProcessingInstructions', '')) or 'NaN'}",
            False,
        ),
        (f"Backprint: {_safe_text(row.get('Backprint', '')) or 'none'}", False),
    ]


def _wrap_text_rl(c, text, font, size, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if c.stringWidth(candidate, font, size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [""]


# ============================================================
# PAGE DRAWING
# ============================================================
def _square_origin(col, row):
    return GRID_LEFT + col * SQUARE, GRID_TOP - (row + 1) * SQUARE


def _draw_grid(c):
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)
    for r in range(ROWS + 1):
        y = GRID_TOP - r * SQUARE
        c.line(GRID_LEFT, y, GRID_RIGHT, y)
    for col in range(COLS + 1):
        x = GRID_LEFT + col * SQUARE
        c.line(x, GRID_BOTTOM, x, GRID_TOP)


def _draw_page_footer(c, year_str, page_num, total_pages):
    footer_y = GRID_BOTTOM - 4 * mm
    c.setFont(FONT_BOLD_NAME, 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(GRID_LEFT, footer_y, str(year_str))
    c.setFont(FONT_NAME, 10.5)
    c.drawRightString(GRID_RIGHT, footer_y, f"{page_num} of {total_pages}")


def _draw_glyph(c, x, y, diamond_path):
    if (
        not diamond_path
        or not isinstance(diamond_path, str)
        or not os.path.exists(diamond_path)
    ):
        return
    c.drawImage(
        diamond_path,
        x,
        y,
        width=SQUARE,
        height=SQUARE,
        mask="auto",
        preserveAspectRatio=True,
        anchor="c",
    )


def _draw_label_text(c, x, y, row, leading=11.5):
    lines = _build_label_lines(row)
    tx = x + TEXT_MARGIN
    ty = y + SQUARE - TEXT_MARGIN
    for text, bold in lines:
        font = FONT_BOLD_NAME if bold else FONT_NAME
        wrapped = _wrap_text_rl(c, text, font, TEXT_FONT_SIZE, SQUARE - 2 * TEXT_MARGIN)
        for line in wrapped:
            ty -= leading
            if ty < y + PM_FONT_SIZE + 2 * PM_MARGIN:
                break
            c.setFont(font, TEXT_FONT_SIZE)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(tx, ty, line)
    cat = _safe_text(row.get("CatalogNumber", ""))
    c.setFont(FONT_BOLD_NAME, PM_FONT_SIZE)
    c.setFillColorRGB(0, 0, 0)
    c.drawRightString(x + SQUARE - PM_MARGIN, y + PM_MARGIN, f"PM# {cat}")


def _draw_key_cell(c, working_dir):
    key_path = os.path.join(working_dir, KEY_FILENAME)
    x, y = _square_origin(KEY_COL, KEY_ROW)
    if not os.path.exists(key_path):
        return
    inner = 3 * mm
    c.drawImage(
        key_path,
        x + inner,
        y + inner,
        width=SQUARE - 2 * inner,
        height=SQUARE - 2 * inner,
        mask="auto",
        preserveAspectRatio=True,
        anchor="c",
    )


def build_pdf(df_sorted, working_dir, output_path, st_progress=None):
    _register_fonts()
    pages = build_pages(df_sorted)
    total = len(pages)
    c = rl_canvas.Canvas(output_path, pagesize=(PAGE_W, PAGE_H))
    for pi, page in enumerate(pages):
        _draw_grid(c)
        slot = 0
        for ri in range(ROWS):
            for ci in range(COLS):
                if ci == KEY_COL and ri == KEY_ROW:
                    _draw_key_cell(c, working_dir)
                    continue
                if slot >= len(page["rows"]):
                    slot += 1
                    continue
                row_data = page["rows"][slot]
                slot += 1
                if row_data is None:
                    continue
                sx, sy = _square_origin(ci, ri)
                c.saveState()
                p = c.beginPath()
                p.rect(sx, sy, SQUARE, SQUARE)
                c.clipPath(p, stroke=0, fill=0)
                _draw_glyph(c, sx, sy, row_data.get("diamond_path"))
                c.restoreState()
                _draw_label_text(c, sx, sy, row_data)
        _draw_page_footer(c, page["year"], pi + 1, total)
        if st_progress is not None:
            st_progress.progress(
                (pi + 1) / total, text=f"Building PDF page {pi + 1}/{total}..."
            )
        if pi < total - 1:
            c.showPage()
    c.save()
    return output_path


# ============================================================
# STREAMLIT UI
# ============================================================
st.set_page_config(page_title="Label Generator", layout="wide")
st.title("📄 Photographic Paper Label Generator")

# Seed session state from persisted config (runs once per session)
_cfg = _load_config()
if "working_dir" not in st.session_state:
    st.session_state["working_dir"] = _cfg.get("working_dir", "")
if "output_dir" not in st.session_state:
    st.session_state["output_dir"] = _cfg.get("output_dir", "")

with st.sidebar:
    st.header("⚙️ Settings")
    csv_file = st.file_uploader("Upload CSV file", type=["csv"])
    working_dir = st.text_input(
        "Working directory (for glyph output)", key="working_dir"
    )
    output_dir = st.text_input("Output folder (for PDF)", key="output_dir")
    st.markdown("---")
    key_file = st.file_uploader(
        "Upload key image (optional)",
        type=["png", "jpg", "jpeg"],
        help="The key image appears in the bottom-right cell of every page. Leave blank to keep that cell empty.",
    )
    if key_file is None:
        st.caption("ℹ️ No key image — bottom-right cell will be blank.")

# ---- Prerequisite check ----
prereq_missing = []
if not csv_file:
    prereq_missing.append("No CSV file uploaded.")
if not working_dir or not os.path.isdir(working_dir):
    prereq_missing.append("Working directory is missing or does not exist.")
if not output_dir:
    prereq_missing.append("No output folder specified.")
elif not os.path.isdir(output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception:
        prereq_missing.append(f"Cannot create output folder: {output_dir}")

if prereq_missing:
    st.warning("Please complete the following before processing:")
    for m in prereq_missing:
        st.error(m)

process_btn = st.button("🚀 Process Labels", disabled=bool(prereq_missing))

if csv_file and not prereq_missing:
    # Load and validate CSV
    try:
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                df_raw = pd.read_csv(csv_file, encoding=enc)
                break
            except UnicodeDecodeError:
                csv_file.seek(0)
        ok, warns, errs = validate_csv(df_raw)
        if errs:
            for e in errs:
                st.error(e)
            st.stop()
        if warns:
            st.warning("Data warnings found:")
            for w in warns:
                st.warning(w)
            proceed = st.radio(
                "Some required fields have blank data. Proceed anyway?",
                ["Yes — continue", "No — fix CSV first"],
                index=1,
            )
            if proceed == "No — fix CSV first":
                st.stop()
        st.success(f"✅ CSV loaded: {len(df_raw)} records")
    except Exception as ex:
        st.error(f"Could not load CSV: {ex}")
        st.stop()

if process_btn:
    progress = st.progress(0, text="Starting...")
    status = st.empty()

    _save_config(working_dir, output_dir)

    status.info("Sorting records...")
    df_sorted = sort_dataframe(df_raw)

    status.info("Generating glyphs...")
    df_sorted = generate_glyphs(df_sorted, working_dir, st_progress=progress)

    # Save uploaded key image to working directory before PDF build
    if key_file is not None:
        key_dest = os.path.join(working_dir, KEY_FILENAME)
        with open(key_dest, "wb") as kf:
            kf.write(key_file.getvalue())

    status.info("Building PDF...")
    today = datetime.datetime.now().strftime("%m%d%Y")
    pdf_name = f"Labels_{today}.pdf"
    pdf_path = os.path.join(output_dir, pdf_name)
    build_pdf(df_sorted, working_dir, pdf_path, st_progress=progress)

    progress.empty()
    status.success(f"✅ Done! PDF saved to: {pdf_path}")

    with open(pdf_path, "rb") as f:
        st.download_button(
            "⬇️ Download PDF", data=f, file_name=pdf_name, mime="application/pdf"
        )
