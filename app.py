"""
Main Streamlit Application: Kanchanaburi Interactive Wildfire & Durian Dashboard
Designed according to BRD.md, DATA_DICTIONARY.md, and UX Wireframe sketch.
"""

import streamlit as st
from src.config import (
    APP_TITLE,
    APP_SUBTITLE,
    TOTAL_EXPECTED_HOTSPOTS,
    BRD_CAUSAL_DISCLAIMER
)
from src.data_loader import load_and_process_data
from src.tab_hotspots import render_tab_hotspots
from src.tab_durian import render_tab_durian
from src.tab_comparison import render_tab_comparison

# Streamlit Page Setup
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished layout and typography
st.markdown("""
<style>
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }
    /* Tab font size */
    button[data-baseweb="tab"] {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    /* Warning alert border */
    .stAlert {
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header Section
    col_title, col_badge = st.columns([3, 1])
    with col_title:
        st.title(f"🔥 {APP_TITLE}")
        st.caption(f"{APP_SUBTITLE} | กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช & สนง.เกษตรจังหวัดกาญจนบุรี")
    with col_badge:
        st.markdown(f"""
        <div style="background-color: #E8F5E9; border: 1px solid #81C784; padding: 10px 14px; border-radius: 8px; text-align: right; margin-top: 10px;">
            <span style="color: #2E7D32; font-weight: bold; font-size: 0.9rem;">✓ Data Integrity Verified</span><br/>
            <span style="color: #333; font-size: 0.85rem;">Hotspot Count = <b>{TOTAL_EXPECTED_HOTSPOTS:,}</b> จุด</span>
        </div>
        """, unsafe_allow_html=True)

    # Load Processed Data
    with st.spinner("กำลังโหลดและประมวลผลข้อมูล..."):
        try:
            data = load_and_process_data()
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
            st.stop()

    df_events = data['events']
    df_durian = data['durian_raw']
    df_joined = data['joined']
    total_expected = data['total_hotspots']

    # Tab Navigation
    tab1, tab2, tab3 = st.tabs([
        "🔥 ภาพรวมจุดความร้อน (Hotspots Overview)",
        "🍈 พื้นที่ปลูกทุเรียน (Durian Cultivation)",
        "⚖️ เปรียบเทียบเชิงพื้นที่และสถิติ (Spatial & Statistical Comparison)"
    ])

    with tab1:
        render_tab_hotspots(df_events, total_expected)

    with tab2:
        render_tab_durian(df_durian, df_joined)

    with tab3:
        render_tab_comparison(df_joined)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #777; font-size: 0.85rem; padding: 10px 0;">
        <b>Kanchanaburi Wildfire & Durian Interactive Dashboard</b> | พัฒนาด้วย Python, Streamlit & Plotly<br/>
        ข้อมูลใช้สำหรับการศึกษาและสำรวจเชิงวิเคราะห์ทางภูมิศาสตร์เท่านั้น ห้ามนำไปใช้อ้างอิงเชิงสาเหตุโดยไม่มีการวิจัยเฉพาะทางเพิ่มเติม
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
