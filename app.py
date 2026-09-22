"""
RF & Electronic Components Catalog
-----------------------------------
אפליקציית Streamlit לחיפוש וסינון רכיבי אלקטרוניקה ו-RF פרמטריים,
בהשראת אתרי קטלוג כמו Analog Devices / Mini-Circuits.

הנתונים נטענים מקובץ CSV חיצוני (ברירת מחדל: components_data.csv),
כך שניתן לעדכן מלאי/ביצועים בלי לגעת בקוד.

הרצה:
    streamlit run app.py
"""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------
# הגדרות כלליות של העמוד
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="RF & Components Catalog",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSV_PATH = Path("components_data.csv")

# עמודות "ליבה" שהאפליקציה יודעת לעבוד איתן. אם הן קיימות בקובץ - נבנה
# עבורן פילטרים ייעודיים. עמודות נוספות בקובץ יוצגו אוטומטית בטבלה
# ובכרטיס הפירוט, גם בלי שהאפליקציה "מכירה" אותן במיוחד.
NUMERIC_RANGE_COLUMNS = {
    "Gain_dB": "רווח (Gain) [dB]",
    "NF_dB": "רעש (Noise Figure) [dB]",
    "P1dB_dBm": "P1dB [dBm]",
    "OIP3_dBm": "OIP3 [dBm]",
    "Supply_Voltage_V": "מתח הזנה [V]",
    "Price_USD": "מחיר [$]",
}

FREQ_MIN_COL = "Frequency_Min_GHz"
FREQ_MAX_COL = "Frequency_Max_GHz"

# --------------------------------------------------------------------------
# עיצוב קל (CSS) לתחושה מודרנית ונקייה יותר
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
        div[data-testid="stMetricValue"] {font-size: 1.6rem;}
        .stDataFrame {border-radius: 8px; overflow: hidden;}
        section[data-testid="stSidebar"] {border-right: 1px solid #2b2f38;}
        .part-title {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }
        .part-sub {
            color: #8a8f98;
            margin-bottom: 1rem;
        }
        .stock-badge-in {
            background-color: #1e4620;
            color: #7ee787;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
        }
        .stock-badge-out {
            background-color: #4a1e1e;
            color: #ff8080;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# טעינת נתונים
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="טוען נתוני רכיבים...")
def load_data(path: Path, mtime: float) -> pd.DataFrame:
    """טוען את קובץ ה-CSV. הפרמטר mtime משמש רק כדי לבטל את המטמון
    אוטומטית כשהקובץ מתעדכן (streamlit מזהה שינוי בפרמטרים ומרענן)."""
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    # ניקוי/המרות טיפוסים סלחניות - כדי שקובץ CSV "מלוכלך" לא יפיל את האפליקציה
    for col in list(NUMERIC_RANGE_COLUMNS.keys()) + [FREQ_MIN_COL, FREQ_MAX_COL, "Stock_Qty"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Stock_Qty" in df.columns:
        df["In_Stock"] = df["Stock_Qty"].fillna(0) > 0
    else:
        df["In_Stock"] = True

    for col in ["Part_Number", "Category", "Manufacturer", "Description", "Package"]:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("")

    return df


def safe_min_max(series: pd.Series, fallback=(0.0, 1.0)):
    s = series.dropna()
    if s.empty:
        return fallback
    lo, hi = float(s.min()), float(s.max())
    if lo == hi:
        hi = lo + 1e-6
    return lo, hi


# --------------------------------------------------------------------------
# בדיקת קיום קובץ הנתונים
# --------------------------------------------------------------------------
if not CSV_PATH.exists():
    st.error(
        f"לא נמצא קובץ הנתונים `{CSV_PATH.name}` בתיקיית האפליקציה.\n\n"
        "צור קובץ CSV בשם הזה (ראה מבנה מומלץ בהודעה שנלוותה לקוד), "
        "או השתמש בכפתור להעלאת קובץ למטה."
    )
    uploaded = st.file_uploader("או העלה קובץ CSV להצגה חד-פעמית", type=["csv"])
    if uploaded is None:
        st.stop()
    df_raw = pd.read_csv(uploaded)
    df_raw.columns = [c.strip() for c in df_raw.columns]
else:
    df_raw = load_data(CSV_PATH, CSV_PATH.stat().st_mtime)

df = df_raw.copy()

# --------------------------------------------------------------------------
# Sidebar - פילטרים
# --------------------------------------------------------------------------
st.sidebar.title("🔎 סינון וחיפוש")

if st.sidebar.button("↺ איפוס כל הפילטרים", use_container_width=True):
    for key in list(st.session_state.keys()):
        if key.startswith("filt_"):
            del st.session_state[key]
    st.rerun()

# --- חיפוש טקסט חופשי ---
search_text = st.sidebar.text_input(
    "חיפוש חופשי (מק״ט / תיאור)",
    key="filt_search",
    placeholder="לדוגמה: LNA-2400 או Low Noise Amplifier",
)

st.sidebar.markdown("---")

# --- קטגוריה ---
if "Category" in df.columns:
    categories = sorted(df["Category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "קטגוריה", options=categories, key="filt_category"
    )
else:
    selected_categories = []

# --- יצרן ---
if "Manufacturer" in df.columns:
    manufacturers = sorted(df["Manufacturer"].dropna().unique().tolist())
    selected_manufacturers = st.sidebar.multiselect(
        "יצרן", options=manufacturers, key="filt_manufacturer"
    )
else:
    selected_manufacturers = []

# --- Package ---
if "Package" in df.columns:
    packages = sorted(df["Package"].dropna().unique().tolist())
    selected_packages = st.sidebar.multiselect(
        "חבילה (Package)", options=packages, key="filt_package"
    )
else:
    selected_packages = []

st.sidebar.markdown("---")

# --- זמינות במלאי ---
stock_filter = st.sidebar.radio(
    "זמינות במלאי",
    options=["הכל", "רק במלאי", "רק אזל מהמלאי"],
    horizontal=False,
    key="filt_stock",
)

st.sidebar.markdown("---")
st.sidebar.subheader("טווח תדרים (GHz)")

freq_selected_range = None
if FREQ_MIN_COL in df.columns and FREQ_MAX_COL in df.columns:
    combined_freq = pd.concat([df[FREQ_MIN_COL], df[FREQ_MAX_COL]])
    f_lo, f_hi = safe_min_max(combined_freq, fallback=(0.0, 40.0))
    freq_selected_range = st.sidebar.slider(
        "כלול רכיבים שהתדר שלהם חופף לטווח:",
        min_value=round(f_lo, 3),
        max_value=round(f_hi, 3),
        value=(round(f_lo, 3), round(f_hi, 3)),
        key="filt_freq",
    )

st.sidebar.markdown("---")
st.sidebar.subheader("פרמטרים נוספים")

numeric_selected_ranges = {}
for col, label in NUMERIC_RANGE_COLUMNS.items():
    if col in df.columns and df[col].notna().any():
        lo, hi = safe_min_max(df[col])
        with st.sidebar.expander(label, expanded=False):
            selected = st.slider(
                label,
                min_value=round(lo, 2),
                max_value=round(hi, 2),
                value=(round(lo, 2), round(hi, 2)),
                key=f"filt_{col}",
                label_visibility="collapsed",
            )
            numeric_selected_ranges[col] = selected

# --------------------------------------------------------------------------
# הפעלת הפילטרים
# --------------------------------------------------------------------------
filtered = df.copy()

if search_text:
    text_cols = [c for c in ["Part_Number", "Description"] if c in filtered.columns]
    if text_cols:
        mask = pd.Series(False, index=filtered.index)
        for c in text_cols:
            mask |= filtered[c].str.contains(search_text, case=False, na=False)
        filtered = filtered[mask]

if selected_categories:
    filtered = filtered[filtered["Category"].isin(selected_categories)]

if selected_manufacturers:
    filtered = filtered[filtered["Manufacturer"].isin(selected_manufacturers)]

if selected_packages:
    filtered = filtered[filtered["Package"].isin(selected_packages)]

if stock_filter == "רק במלאי":
    filtered = filtered[filtered["In_Stock"]]
elif stock_filter == "רק אזל מהמלאי":
    filtered = filtered[~filtered["In_Stock"]]

if freq_selected_range is not None:
    f_min_sel, f_max_sel = freq_selected_range
    # חפיפה בין טווח התדר של הרכיב לבין הטווח שנבחר
    filtered = filtered[
        (filtered[FREQ_MIN_COL].fillna(-1e9) <= f_max_sel)
        & (filtered[FREQ_MAX_COL].fillna(1e9) >= f_min_sel)
    ]

for col, (lo_sel, hi_sel) in numeric_selected_ranges.items():
    filtered = filtered[
        filtered[col].isna() | filtered[col].between(lo_sel, hi_sel)
    ]

# --------------------------------------------------------------------------
# אזור ראשי - כותרת ומדדים
# --------------------------------------------------------------------------
st.title("📡 קטלוג רכיבי אלקטרוניקה ו-RF")
st.caption("חיפוש, סינון והשוואה של רכיבים לפי פרמטרים טכניים וזמינות במלאי.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("סה״כ רכיבים בקטלוג", len(df))
m2.metric("תוצאות מתאימות", len(filtered))
if "In_Stock" in filtered.columns:
    m3.metric("מתוכם במלאי", int(filtered["In_Stock"].sum()))
if "Price_USD" in filtered.columns and not filtered.empty:
    avg_price = filtered["Price_USD"].mean()
    m4.metric("מחיר ממוצע ($)", f"{avg_price:,.2f}" if pd.notna(avg_price) else "—")

st.markdown("### תוצאות")

if filtered.empty:
    st.warning("לא נמצאו רכיבים התואמים לסינון הנוכחי. נסה להרחיב את הטווחים או לנקות פילטרים.")
else:
    display_df = filtered.copy()
    if "In_Stock" in display_df.columns:
        display_df["זמינות"] = display_df["In_Stock"].map(
            {True: "✅ במלאי", False: "❌ אזל"}
        )

    column_order = [
        c
        for c in [
            "Part_Number",
            "Category",
            "Manufacturer",
            "Description",
            FREQ_MIN_COL,
            FREQ_MAX_COL,
            "Gain_dB",
            "NF_dB",
            "P1dB_dBm",
            "OIP3_dBm",
            "Package",
            "Price_USD",
            "זמינות",
            "Stock_Qty",
        ]
        if c in display_df.columns
    ]
    remaining_cols = [c for c in display_df.columns if c not in column_order and c != "In_Stock"]
    column_order += remaining_cols

    event = st.dataframe(
        display_df[column_order],
        use_container_width=True,
        hide_index=True,
        height=420,
        on_select="rerun",
        selection_mode="single-row",
        key="results_table",
    )

    # כפתור הורדת התוצאות המסוננות
    csv_buffer = io.StringIO()
    filtered.drop(columns=["In_Stock"], errors="ignore").to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ הורד תוצאות מסוננות כ-CSV",
        data=csv_buffer.getvalue(),
        file_name="filtered_components.csv",
        mime="text/csv",
        use_container_width=False,
    )

    # ----------------------------------------------------------------
    # אזור פירוט רכיב נבחר
    # ----------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🧾 פירוט רכיב")

    selected_rows = event.selection.rows if event is not None else []

    if not selected_rows:
        st.info("בחר שורה בטבלה למעלה כדי לראות את כל פרטי הרכיב.")
    else:
        sel_idx = filtered.index[selected_rows[0]]
        part = filtered.loc[sel_idx]

        header_col, badge_col = st.columns([4, 1])
        with header_col:
            title = part.get("Part_Number", "רכיב")
            desc = part.get("Description", "")
            st.markdown(f"<div class='part-title'>{title}</div>", unsafe_allow_html=True)
            if desc:
                st.markdown(f"<div class='part-sub'>{desc}</div>", unsafe_allow_html=True)
        with badge_col:
            if part.get("In_Stock", True):
                st.markdown(
                    "<span class='stock-badge-in'>✅ במלאי</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<span class='stock-badge-out'>❌ אזל מהמלאי</span>",
                    unsafe_allow_html=True,
                )

        detail_cols = st.columns(3)
        skip_cols = {"In_Stock"}
        items = [(k, v) for k, v in part.items() if k not in skip_cols]

        for i, (key, value) in enumerate(items):
            col = detail_cols[i % 3]
            if pd.isna(value) or value == "":
                display_value = "—"
            else:
                display_value = value
            col.metric(label=key.replace("_", " "), value=str(display_value))

        if "Datasheet_URL" in part and isinstance(part["Datasheet_URL"], str) and part["Datasheet_URL"].startswith("http"):
            st.markdown(f"[📄 קישור ל-Datasheet]({part['Datasheet_URL']})")

st.markdown("---")
st.caption(
    f"מקור נתונים: `{CSV_PATH.name}` · עדכן את הקובץ הזה כדי לשנות מלאי, מחירים או להוסיף רכיבים חדשים — "
    "האפליקציה תיטען מחדש אוטומטית."
)
