import streamlit as st
from database import db
from ui import dashboard, problems, practice, profiles, admin, help_page

# Page config
st.set_page_config(
    page_title="Spark Practice Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme support custom CSS
st.markdown("""
<style>
    /* Styling for cards */
    .stMetric {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333333;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stMetric label {
        color: #888888 !important;
        font-weight: bold;
    }
    .stMetric div {
        color: #ff4b4b !important;
    }
    /* Tabs custom styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1e1e1e;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Database
db.init_db()

# Sidebar Navigation
st.sidebar.markdown("<h2 style='color: #ff4b4b;'>⚡ Navigation</h2>", unsafe_allow_html=True)

# Session State active page
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "⚡ Dashboard"

pages = {
    "⚡ Dashboard": dashboard,
    "📂 Problem Bank": problems,
    "💻 Practice Sandbox": practice,
    "⚙️ Spark Profiles": profiles,
    "📥 Import Problems": admin,
    "📖 Understand Me": help_page
}

# Render sidebar radio buttons
selected_page = st.sidebar.radio(
    "Go to:",
    list(pages.keys()),
    index=list(pages.keys()).index(st.session_state["active_page"])
)

st.session_state["active_page"] = selected_page

# Run the selected page
pages[selected_page].show()
