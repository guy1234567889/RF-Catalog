"""
RF & Electronic Components Catalog
-----------------------------------
A Streamlit application styled after the Analog Devices website and
parametric catalog: clean white background, deep-blue header/accents,
a prominent hero search bar, and category cards.

Data is loaded from an external CSV file (default: components_data.csv),
so the catalog (stock, pricing, specs) can be updated without touching
this code.

Run:
    streamlit run app.py
"""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------
# Page configuration
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="RF & Components Catalog",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSV_PATH = Path("components_data.csv")

NUMERIC_RANGE_COLUMNS = {
    "Gain_dB": "Gain [dB]",
    "NF_dB": "Noise Figure [dB]",
    "P1dB_dBm": "P1dB [dBm]",
    "OIP3_dBm": "OIP3 [dBm]",
    "Supply_Voltage_V": "Supply Voltage [V]",
    "Price_USD": "Price [$]",
}

FREQ_MIN_COL = "Frequency_Min_GHz"
FREQ_MAX_COL = "Frequency_Max_GHz"

# Quick-browse category tiles shown on the "home" hero section.
# `match` is a case-insensitive substring matched against the Category column,
# so it still works even if your CSV uses slightly different category names.
QUICK_CATEGORIES = [
    {"icon": "📶", "label": "Amplifiers", "match": "amplifier"},
    {"icon": "🔀", "label": "Mixers", "match": "mixer"},
    {"icon": "🔁", "label": "RF Switches", "match": "switch"},
    {"icon": "🔄", "label": "Converters", "match": "converter"},
    {"icon": "🎛", "label": "Filters", "match": "filter"},
    {"icon": "📉", "label": "Attenuators", "match": "attenuator"},
]

# --------------------------------------------------------------------------
# Theme / styling — light background, deep Analog-blue accents
# --------------------------------------------------------------------------
PRIMARY_BLUE = "#00355F"     # deep navy — header, headings
ACCENT_BLUE = "#0072CE"      # bright signal blue — buttons, links, highlights
ACCENT_BLUE_LIGHT = "#E6F2FC"  # pale blue tint for hero/backgrounds
BORDER = "#D6DEE6"
TEXT_DARK = "#1A2733"
TEXT_MUTED = "#5B6B7B"
BG_PAGE = "#FFFFFF"
BG_CARD = "#FFFFFF"

st.markdown(
    f"""
    <style>
        html, body, [class*="css"] {{
            font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
            color: {TEXT_DARK};
        }}
        .stApp {{
            background-color: {BG_PAGE};
        }}
        .block-container {{
            padding-top: 1rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }}

        /* ---- Top header bar (logo strip) ---- */
        .adi-topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: {PRIMARY_BLUE};
            padding: 14px 30px;
            border-radius: 8px 8px 0 0;
            margin-bottom: 0;
        }}
        .adi-logo {{
            display: flex;
            align-items: center;
            gap: 10px;
            color: #FFFFFF;
            font-size: 1.3rem;
            font-weight: 800;
            letter-spacing: 0.5px;
        }}
        .adi-logo span.dot {{
            color: {ACCENT_BLUE};
            font-size: 1.6rem;
            line-height: 0;
        }}
        .adi-nav {{
            display: flex;
            gap: 26px;
            color: #CFE4F7;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.3px;
            text-transform: uppercase;
        }}

        /* ---- Hero / search section ---- */
        .adi-hero {{
            background: linear-gradient(180deg, {ACCENT_BLUE_LIGHT} 0%, #FFFFFF 100%);
            border: 1px solid {BORDER};
            border-top: none;
            border-radius: 0 0 8px 8px;
            padding: 34px 30px 26px 30px;
            margin-bottom: 1.8rem;
            text-align: center;
        }}
        .adi-hero h1 {{
            color: {PRIMARY_BLUE};
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 4px;
        }}
        .adi-hero p {{
            color: {TEXT_MUTED};
            font-size: 1rem;
            margin-bottom: 0;
        }}

        /* Search input styling */
        div[data-testid="stTextInput"] input {{
            border: 2px solid {ACCENT_BLUE} !important;
            border-radius: 24px !important;
            padding: 10px 20px !important;
            font-size: 1.05rem !important;
            box-shadow: 0 2px 8px rgba(0, 53, 95, 0.08);
        }}
        div[data-testid="stTextInput"] input:focus {{
            box-shadow: 0 0 0 3px rgba(0, 114, 206, 0.25);
        }}

        /* ---- Category tiles ---- */
        .cat-card {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 18px 10px;
            text-align: center;
            transition: all 0.15s ease-in-out;
        }}
        .cat-icon {{
            font-size: 2rem;
            margin-bottom: 6px;
        }}
        .cat-label {{
            font-weight: 700;
            color: {PRIMARY_BLUE};
            font-size: 0.92rem;
        }}
        div[data-testid="column"] .stButton button {{
            width: 100%;
            border-radius: 12px;
            border: 1px solid {BORDER};
            background-color: {BG_CARD};
            color: {PRIMARY_BLUE};
            font-weight: 700;
            padding: 18px 4px;
        }}
        div[data-testid="column"] .stButton button:hover {{
            border-color: {ACCENT_BLUE};
            background-color: {ACCENT_BLUE_LIGHT};
            color: {ACCENT_BLUE};
        }}

        /* ---- Generic buttons ---- */
        .stButton > button, .stDownloadButton > button, .stLinkButton > a {{
            border-radius: 24px;
            font-weight: 600;
        }}
        .stDownloadButton > button, .stLinkButton > a {{
            background-color: {ACCENT_BLUE};
            color: #FFFFFF;
            border: none;
        }}
        .stDownloadButton > button:hover, .stLinkButton > a:hover {{
            background-color: {PRIMARY_BLUE};
            color: #FFFFFF;
        }}

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {{
            background-color: #F7FAFC;
            border-right: 1px solid {BORDER};
        }}
        .sidebar-section-title {{
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 1.1px;
            text-transform: uppercase;
            color: {ACCENT_BLUE};
            margin: 1.1rem 0 0.4rem 0;
            border-bottom: 2px solid {ACCENT_BLUE_LIGHT};
            padding-bottom: 6px;
        }}

        /* ---- Metric tiles ---- */
        div[data-testid="stMetric"] {{
            background: #F7FAFC;
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 12px 16px 8px 16px;
        }}
        div[data-testid="stMetricLabel"] {{
            font-size: 0.72rem;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            color: {TEXT_MUTED};
        }}
        div[data-testid="stMetricValue"] {{
            font-size: 1.5rem;
            color: {PRIMARY_BLUE};
        }}

        h2, h3 {{
            color: {PRIMARY_BLUE} !important;
        }}

        /* ---- Table ---- */
        .stDataFrame {{
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid {BORDER};
        }}

        /* ---- Active filter chip ---- */
        .active-chip {{
            display: inline-block;
            background-color: {ACCENT_BLUE_LIGHT};
            border: 1px solid {ACCENT_BLUE};
            color: {ACCENT_BLUE};
            padding: 4px 14px;
            border-radius: 16px;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 12px;
        }}

        /* ---- Detail card ---- */
        .detail-card {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-left: 5px solid {ACCENT_BLUE};
            border-radius: 12px;
            padding: 24px 28px;
            box-shadow: 0 2px 10px rgba(0, 53, 95, 0.06);
        }}
        .detail-title {{
            font-size: 1.55rem;
            font-weight: 800;
            color: {PRIMARY_BLUE};
            margin-bottom: 2px;
        }}
        .detail-sub {{
            color: {TEXT_MUTED};
            font-size: 0.95rem;
            margin-bottom: 14px;
        }}
        .spec-label {{
            font-size: 0.68rem;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            color: {TEXT_MUTED};
            margin-bottom: 2px;
        }}
        .spec-value {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {TEXT_DARK};
            margin-bottom: 14px;
        }}
        .stock-pill-in {{
            background-color: #E6F7EE;
            border: 1px solid #2ec27e;
            color: #1a8a54;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
        }}
        .stock-pill-out {{
            background-color: #FDECEC;
            border: 1px solid #e03c3c;
            color: #c0302f;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
        }}

        footer {{visibility: hidden;}}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading component database...")
def load_data(path: Path, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

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
# Load the dataset
# --------------------------------------------------------------------------
if not CSV_PATH.exists():
    st.error(
        f"Data file `{CSV_PATH.name}` was not found in the application folder.\n\n"
        "Create a CSV file with this name (see the recommended schema), "
        "or upload one below for a one-off preview."
    )
    uploaded = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded is None:
        st.stop()
    df_raw = pd.read_csv(uploaded)
    df_raw.columns = [c.strip() for c in df_raw.columns]
else:
    df_raw = load_data(CSV_PATH, CSV_PATH.stat().st_mtime)

df = df_raw.copy()

if "quick_category" not in st.session_state:
    st.session_state["quick_category"] = None

# --------------------------------------------------------------------------
# Top bar + Hero section (Analog Devices "home page" feel)
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="adi-topbar">
        <div class="adi-logo"><span class="dot">◆</span> ANALOG&nbsp;PARTS&nbsp;CATALOG</div>
        <div class="adi-nav">
            <span>Amplifiers</span><span>RF&nbsp;&amp;&nbsp;Microwave</span>
            <span>Converters</span><span>Support</span>
        </div>
    </div>
    <div class="adi-hero">
        <h1>Find the Right Component, Faster</h1>
        <p>Search our full parametric catalog of RF and electronic components by part number, specification or category.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

hero_search_col1, hero_search_col2, hero_search_col3 = st.columns([1, 3, 1])
with hero_search_col2:
    hero_search = st.text_input(
        "Search",
        key="filt_search",
        placeholder="🔍  Search by part number, keyword or description (e.g. \"LNA\", \"2.4 GHz\", \"low noise\")",
        label_visibility="collapsed",
    )

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
st.markdown(
    f"<div style='text-align:center; color:{TEXT_MUTED}; font-weight:700; "
    "letter-spacing:0.5px; text-transform:uppercase; font-size:0.8rem; margin-bottom:10px;'>"
    "Browse by Category</div>",
    unsafe_allow_html=True,
)

cat_cols = st.columns(len(QUICK_CATEGORIES))
for col, cat in zip(cat_cols, QUICK_CATEGORIES):
    with col:
        if st.button(f"{cat['icon']}\n\n{cat['label']}", key=f"quickcat_{cat['label']}", use_container_width=True):
            st.session_state["quick_category"] = cat["match"]

if st.session_state["quick_category"]:
    chip_col1, chip_col2 = st.columns([5, 1])
    with chip_col1:
        st.markdown(
            f"<span class='active-chip'>Category filter: {st.session_state['quick_category'].title()} ✕</span>",
            unsafe_allow_html=True,
        )
    with chip_col2:
        if st.button("Clear category", key="clear_quickcat"):
            st.session_state["quick_category"] = None
            st.rerun()

st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Sidebar — advanced filters
# --------------------------------------------------------------------------
st.sidebar.markdown(
    f"<div style='font-size:1.05rem; font-weight:800; letter-spacing:0.4px; color:{PRIMARY_BLUE};'>⚙ ADVANCED FILTERS</div>",
    unsafe_allow_html=True,
)
st.sidebar.caption("Refine the catalog using the parameters below.")

if st.sidebar.button("↺ Reset all filters", use_container_width=True):
    for key in list(st.session_state.keys()):
        if key.startswith("filt_"):
            del st.session_state[key]
    st.session_state["quick_category"] = None
    st.rerun()

st.sidebar.markdown("<div class='sidebar-section-title'>Classification</div>", unsafe_allow_html=True)

if "Category" in df.columns:
    categories = sorted(df["Category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect("Category", options=categories, key="filt_category")
else:
    selected_categories = []

if "Manufacturer" in df.columns:
    manufacturers = sorted(df["Manufacturer"].dropna().unique().tolist())
    selected_manufacturers = st.sidebar.multiselect("Manufacturer", options=manufacturers, key="filt_manufacturer")
else:
    selected_manufacturers = []

if "Package" in df.columns:
    packages = sorted(df["Package"].dropna().unique().tolist())
    selected_packages = st.sidebar.multiselect("Package", options=packages, key="filt_package")
else:
    selected_packages = []

st.sidebar.markdown("<div class='sidebar-section-title'>Availability</div>", unsafe_allow_html=True)
stock_filter = st.sidebar.radio(
    "Stock status",
    options=["All", "In Stock Only", "Out of Stock Only"],
    key="filt_stock",
    label_visibility="collapsed",
)

freq_selected_range = None
if FREQ_MIN_COL in df.columns and FREQ_MAX_COL in df.columns:
    st.sidebar.markdown("<div class='sidebar-section-title'>Frequency Range (GHz)</div>", unsafe_allow_html=True)
    combined_freq = pd.concat([df[FREQ_MIN_COL], df[FREQ_MAX_COL]])
    f_lo, f_hi = safe_min_max(combined_freq, fallback=(0.0, 40.0))
    freq_selected_range = st.sidebar.slider(
        "Include parts overlapping this range",
        min_value=round(f_lo, 3),
        max_value=round(f_hi, 3),
        value=(round(f_lo, 3), round(f_hi, 3)),
        key="filt_freq",
        label_visibility="collapsed",
    )

numeric_selected_ranges = {}
active_numeric_cols = [c for c in NUMERIC_RANGE_COLUMNS if c in df.columns and df[c].notna().any()]
if active_numeric_cols:
    st.sidebar.markdown("<div class='sidebar-section-title'>Performance Parameters</div>", unsafe_allow_html=True)
    for col in active_numeric_cols:
        label = NUMERIC_RANGE_COLUMNS[col]
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
# Apply filters
# --------------------------------------------------------------------------
filtered = df.copy()

if hero_search:
    text_cols = [c for c in ["Part_Number", "Description"] if c in filtered.columns]
    if text_cols:
        mask = pd.Series(False, index=filtered.index)
        for c in text_cols:
            mask |= filtered[c].str.contains(hero_search, case=False, na=False)
        filtered = filtered[mask]

if st.session_state["quick_category"] and "Category" in filtered.columns:
    filtered = filtered[filtered["Category"].str.contains(st.session_state["quick_category"], case=False, na=False)]

if selected_categories:
    filtered = filtered[filtered["Category"].isin(selected_categories)]

if selected_manufacturers:
    filtered = filtered[filtered["Manufacturer"].isin(selected_manufacturers)]

if selected_packages:
    filtered = filtered[filtered["Package"].isin(selected_packages)]

if stock_filter == "In Stock Only":
    filtered = filtered[filtered["In_Stock"]]
elif stock_filter == "Out of Stock Only":
    filtered = filtered[~filtered["In_Stock"]]

if freq_selected_range is not None:
    f_min_sel, f_max_sel = freq_selected_range
    filtered = filtered[
        (filtered[FREQ_MIN_COL].fillna(-1e9) <= f_max_sel)
        & (filtered[FREQ_MAX_COL].fillna(1e9) >= f_min_sel)
    ]

for col, (lo_sel, hi_sel) in numeric_selected_ranges.items():
    filtered = filtered[filtered[col].isna() | filtered[col].between(lo_sel, hi_sel)]

# --------------------------------------------------------------------------
# Summary metrics
# --------------------------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Parts in Catalog", len(df))
m2.metric("Matching Results", len(filtered))
if "In_Stock" in filtered.columns:
    m3.metric("In Stock", int(filtered["In_Stock"].sum()))
if "Price_USD" in filtered.columns and not filtered.empty:
    avg_price = filtered["Price_USD"].mean()
    m4.metric("Avg. Price (USD)", f"${avg_price:,.2f}" if pd.notna(avg_price) else "—")

st.markdown("###  ")
st.subheader("Search Results")

if filtered.empty:
    st.warning("No components match the current filters. Try widening the ranges or clearing filters.")
else:
    display_df = filtered.copy()
    if "In_Stock" in display_df.columns:
        display_df["Availability"] = display_df["In_Stock"].map({True: "✅ In Stock", False: "❌ Out of Stock"})

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
            "Availability",
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
        height=430,
        on_select="rerun",
        selection_mode="single-row",
        key="results_table",
    )

    dl_col, hint_col = st.columns([1, 4])
    with dl_col:
        csv_buffer = io.StringIO()
        filtered.drop(columns=["In_Stock"], errors="ignore").to_csv(csv_buffer, index=False)
        st.download_button(
            label="⬇ Download Filtered Results (CSV)",
            data=csv_buffer.getvalue(),
            file_name="filtered_components.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with hint_col:
        st.caption("Click any row in the table above to open its full parametric datasheet below.")

    # ----------------------------------------------------------------
    # Product Details Card
    # ----------------------------------------------------------------
    st.markdown("###  ")
    st.subheader("Product Details")

    selected_rows = event.selection.rows if event is not None else []

    if not selected_rows:
        st.info("Select a component from the table above to view its full specifications.")
    else:
        sel_idx = filtered.index[selected_rows[0]]
        part = filtered.loc[sel_idx]

        st.markdown("<div class='detail-card'>", unsafe_allow_html=True)

        header_col, badge_col = st.columns([4, 1])
        with header_col:
            title = part.get("Part_Number", "Component")
            desc = part.get("Description", "")
            manuf = part.get("Manufacturer", "")
            sub_line = " · ".join([v for v in [manuf, desc] if v])
            st.markdown(f"<div class='detail-title'>{title}</div>", unsafe_allow_html=True)
            if sub_line:
                st.markdown(f"<div class='detail-sub'>{sub_line}</div>", unsafe_allow_html=True)
        with badge_col:
            if part.get("In_Stock", True):
                st.markdown("<span class='stock-pill-in'>✅ IN STOCK</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='stock-pill-out'>❌ OUT OF STOCK</span>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        skip_cols = {"In_Stock", "Part_Number", "Description", "Manufacturer", "Datasheet_URL"}
        items = [(k, v) for k, v in part.items() if k not in skip_cols]

        n_cols = 4
        spec_cols = st.columns(n_cols)
        for i, (key, value) in enumerate(items):
            display_value = "—" if (pd.isna(value) or value == "") else str(value)
            col = spec_cols[i % n_cols]
            col.markdown(
                f"""
                <div class='spec-label'>{key.replace('_', ' ')}</div>
                <div class='spec-value'>{display_value}</div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        action_col1, action_col2, _ = st.columns([1.4, 1.4, 3])

        with action_col1:
            datasheet_url = part.get("Datasheet_URL", "")
            if isinstance(datasheet_url, str) and datasheet_url.startswith("http"):
                st.link_button("📄 Open Datasheet", datasheet_url, use_container_width=True)
            else:
                st.button("📄 Datasheet Unavailable", disabled=True, use_container_width=True)

        with action_col2:
            single_buffer = io.StringIO()
            pd.DataFrame([part.drop(labels=["In_Stock"], errors="ignore")]).to_csv(single_buffer, index=False)
            st.download_button(
                label="⬇ Export This Part (CSV)",
                data=single_buffer.getvalue(),
                file_name=f"{part.get('Part_Number', 'component')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

st.markdown("---")
st.caption(
    f"Data source: `{CSV_PATH.name}` — update this file to change stock levels, pricing or specs. "
    "The app reloads automatically when the file changes."
)
