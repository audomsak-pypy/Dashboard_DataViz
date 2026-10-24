"""
Kanchanaburi Wildfire & Durian Spatial Analytics (Ultimate Version).
Master Executive Dashboard combining Version A and Version B.
Enforces Dark Mode, Fire & Emerald Palette, Zero Emojis, and Zero Text Truncation.
"""

import streamlit as st
from src.config import (
    APP_TITLE,
    APP_SUBTITLE,
    TOTAL_EXPECTED_HOTSPOTS
)
from src.data_loader import load_and_process_data
from src.section_filters import render_header_and_filters
from src.section_spatiotemporal import render_spatiotemporal_section
from src.section_hierarchy import render_hierarchy_section
from src.section_datatable import render_datatable_and_trend_section, render_footer_metadata_bar
from src.section_statistical import render_statistical_summary_bottom

# Streamlit Page Setup - Full Width Executive Mode
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Executive Dark Theme CSS
st.markdown("""
<style>
    /* Global Base */
    html, body, [class*="css"], .stApp {
        background-color: #0E1117 !important;
        color: #F0F6FC !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        font-size: 16px !important;
    }

    /* Container padding */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 96% !important;
    }

    /* Metric Containers */
    [data-testid="stMetric"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }

    [data-testid="stMetricLabel"] {
        white-space: normal !important;
        word-break: break-word !important;
        color: #8B949E !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }

    [data-testid="stMetricValue"] {
        white-space: normal !important;
        word-break: break-word !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #F0F6FC !important;
    }

    /* Form Controls & Inputs */
    div[data-baseweb="select"] > div {
        background-color: #161B22 !important;
        border-color: #30363D !important;
        color: #F0F6FC !important;
        border-radius: 6px !important;
    }

    div[data-baseweb="select"] span {
        color: #F0F6FC !important;
    }

    /* Radio buttons */
    div[role="radiogroup"] {
        gap: 16px !important;
    }
    div[role="radiogroup"] label {
        color: #C9D1D9 !important;
        font-size: 0.85rem !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #161B22 !important;
        color: #E53935 !important;
        border: 1px solid #E53935 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover {
        background-color: #E53935 !important;
        color: #FFFFFF !important;
        border-color: #C62828 !important;
    }

    /* Dataframe Header & Cells */
    .stDataFrame {
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }

    /* Text Inputs */
    .stTextInput input {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #F0F6FC !important;
        border-radius: 6px !important;
    }

    /* Section Divider */
    hr {
        border-color: #21262D !important;
        margin: 28px 0 !important;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # 1. Load Data
    with st.spinner("กำลังโหลดข้อมูล..."):
        try:
            data = load_and_process_data()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
            st.stop()

    df_events = data['events']
    df_durian = data['durian_raw']
    df_joined = data['joined']

    # 2. Section 1 & 2: Header, Global Filters, 4 KPIs, Highlights Strip
    filtered_events, filtered_durian, filtered_joined, filter_desc, filter_meta = render_header_and_filters(df_events, df_durian)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # 3. Section 3: Spatial & Temporal Analysis (Left Temporal, Right Map)
    render_spatiotemporal_section(filtered_events)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # 4. Section 4: Hierarchy & Categorization (Treemap, Top 10 Tambons, Days, Stacked Bar)
    render_hierarchy_section(filtered_events)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # 5. Section 5: Data Details & Tables, Annual Durian Trendline
    render_datatable_and_trend_section(
        filtered_durian=filtered_durian,
        filtered_events=filtered_events,
        sel_years=filter_meta['years'],
        sel_amp=filter_meta['amphoe']
    )

    st.markdown("<hr/>", unsafe_allow_html=True)

    # 6. Section คำเตือนและผลการวิเคราะห์ทางสถิติ (ย้ายมาไว้ส่วนล่างสุดของหน้าแดชบอร์ด)
    render_statistical_summary_bottom(filtered_joined)

    # Executive Footer Metadata Bar
    render_footer_metadata_bar()



if __name__ == "__main__":
    main()

