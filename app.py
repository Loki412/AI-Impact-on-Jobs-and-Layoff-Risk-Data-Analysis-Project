import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import importlib
import re
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from ai_api import Chat
from v2ex_crawler import fetch_vibe_coding_news, DataPersistence, auto_crawler

import dynamic

# Muted color palette & conditional template for all Plotly charts
MUTED_COLORS = ["#7c9aff", "#81c784", "#ffb74d", "#ce93d8", "#64b5f6", "#a1887f", "#4dd0e1", "#f06292"]
px.defaults.color_discrete_sequence = MUTED_COLORS

# Build both light & dark templates
pio.templates["vibe_light"] = pio.templates["plotly_white"]
pio.templates["vibe_light"].layout.update(
    font=dict(family="Inter, sans-serif", color="#444"),
    title=dict(font=dict(color="#1a1a2e", size=16)),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=50, r=20, t=40, b=40),
    hoverlabel=dict(bgcolor="#f0f4ff", font=dict(color="#1a1a2e")),
    xaxis=dict(title=dict(font=dict(color="#666")), tickfont=dict(color="#999"), gridcolor="rgba(0,0,0,0.05)"),
    yaxis=dict(title=dict(font=dict(color="#666")), tickfont=dict(color="#999"), gridcolor="rgba(0,0,0,0.05)"),
    legend=dict(font=dict(color="#666")),
)
pio.templates["vibe_dark"] = pio.templates["plotly_dark"]
pio.templates["vibe_dark"].layout.update(
    font=dict(family="Inter, sans-serif", color="#c0cce0"),
    title=dict(font=dict(color="#dee4f0", size=16)),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=50, r=20, t=40, b=40),
    hoverlabel=dict(bgcolor="#18203a", font=dict(color="#dee4f0")),
    xaxis=dict(title=dict(font=dict(color="#c0cce0")), tickfont=dict(color="#6a7a9a"), gridcolor="rgba(255,255,255,0.03)"),
    yaxis=dict(title=dict(font=dict(color="#c0cce0")), tickfont=dict(color="#6a7a9a"), gridcolor="rgba(255,255,255,0.03)"),
    legend=dict(font=dict(color="#c0cce0")),
)

BUILTIN_API_KEY = "请自行输入个人的api key"
BUILTIN_BASE_URL = "https://api.deepseek.com"
BUILTIN_MODEL = "deepseek-chat"

st.set_page_config(
    page_title="VibeTrends AI — AIGC Job Impact & Vibe Coding Diagnostic Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Theme state ----
if "theme" not in st.session_state:
    st.session_state.theme = "system"

theme = st.session_state.theme
if theme == "dark":
    px.defaults.template = "vibe_dark"
elif theme == "light":
    px.defaults.template = "vibe_light"
else:
    px.defaults.template = "vibe_light"

# Light CSS variables (always the base) — Clean lavender dashboard style
LIGHT_VARS = """
:root {
    --bg-app: linear-gradient(135deg, #e8e0f4 0%, #dcd4ec 50%, #e4dce8 100%);
    --bg-sidebar: linear-gradient(180deg, #ffffff 0%, #f8f6fc 100%);
    --bg-card: #ffffff; --bg-tab: rgba(255,255,255,0.85);
    --bg-tab-sel: #ffffff; --bg-input: #ffffff;
    --bg-chat: #ffffff; --bg-chat-user: linear-gradient(135deg, #f3f0fa 0%, #ede8f5 100%);
    --bg-table-header: #f8f6fc; --bg-table-even: #ffffff; --bg-table-odd: #faf9fd;
    --bg-expander: #ffffff; --bg-plotly: #ffffff;
    --bg-status: #ffffff; --bg-code: #f6f4fa;
    --bg-menu: #ffffff; --bg-info: #f0ecfa; --bg-success: #e8f5e9; --bg-error: #fce4ec;
    --text-primary: #2d2b3a; --text-secondary: #5c5a6e; --text-tertiary: #8e8c9e;
    --text-on-dark: #ffffff; --text-muted: #8e8c9e; --text-caption: #a8a6b6;
    --text-info: #6c5ce7; --text-success: #2e7d32; --text-error: #c62828;
    --text-table: #4a4858; --text-input: #2d2b3a; --text-placeholder: #c0bed0;
    --border: rgba(108,92,231,0.08); --border-hover: rgba(108,92,231,0.15);
    --border-input: rgba(108,92,231,0.12); --shadow: 0 2px 12px rgba(108,92,231,0.06);
    --shadow-lg: 0 8px 32px rgba(108,92,231,0.10);
    --accent: #6c5ce7; --accent-light: #a29bfe; --accent-bg: rgba(108,92,231,0.06);
    --tab-color: #8e8c9e; --tab-sel-color: #6c5ce7;
    --back-btn: #b8b6c8; --back-hover: #6c5ce7;
    --filter-bg: rgba(108,92,231,0.06); --filter-text: #8e8c9e;
    --hr-grad: linear-gradient(90deg, transparent, rgba(108,92,231,0.15), transparent);
    --card-shadow: 0 4px 20px rgba(108,92,231,0.08);
    --card-shadow-hover: 0 8px 32px rgba(108,92,231,0.14);
    --accent-pink: #fd79a8; --accent-blue: #74b9ff; --accent-green: #55efc4;
    --accent-orange: #ffeaa7; --accent-red: #ff7675;
}
"""

DARK_VARS = """
:root {
    --bg-app: linear-gradient(135deg, #1a1628 0%, #1e1832 50%, #1c1630 100%);
    --bg-sidebar: linear-gradient(180deg, #1e1832 0%, #1a1628 100%);
    --bg-card: rgba(30,24,50,0.85); --bg-tab: rgba(26,22,40,0.85);
    --bg-tab-sel: rgba(36,28,58,0.95); --bg-input: rgba(30,24,50,0.9);
    --bg-chat: rgba(30,24,50,0.9); --bg-chat-user: linear-gradient(135deg, rgba(36,28,58,0.9) 0%, rgba(32,24,52,0.9) 100%);
    --bg-table-header: #241c3a; --bg-table-even: rgba(26,22,40,0.7); --bg-table-odd: #1e1832;
    --bg-expander: rgba(30,24,50,0.85); --bg-plotly: rgba(30,24,50,0.9);
    --bg-status: rgba(30,24,50,0.95); --bg-code: #1a1628;
    --bg-menu: rgba(36,28,58,0.98); --bg-info: rgba(28,22,48,0.9); --bg-success: rgba(22,36,24,0.9); --bg-error: rgba(36,18,18,0.9);
    --text-primary: #e8e4f0; --text-secondary: #a8a4b8; --text-tertiary: #6a667a;
    --text-on-dark: #ffffff; --text-muted: #7a768a; --text-caption: #5a566a;
    --text-info: #a29bfe; --text-success: #55efc4; --text-error: #ff7675;
    --text-table: #c8c4d8; --text-input: #e8e4f0; --text-placeholder: #4a465a;
    --border: rgba(108,92,231,0.12); --border-hover: rgba(108,92,231,0.22);
    --border-input: rgba(108,92,231,0.16); --shadow: 0 2px 12px rgba(0,0,0,0.25);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.35);
    --accent: #a29bfe; --accent-light: #6c5ce7; --accent-bg: rgba(108,92,231,0.10);
    --tab-color: #7a768a; --tab-sel-color: #a29bfe;
    --back-btn: #5a566a; --back-hover: #a29bfe;
    --filter-bg: rgba(108,92,231,0.08); --filter-text: #6a667a;
    --hr-grad: linear-gradient(90deg, transparent, rgba(108,92,231,0.18), transparent);
    --card-shadow: 0 4px 20px rgba(0,0,0,0.3);
    --card-shadow-hover: 0 8px 32px rgba(0,0,0,0.4);
    --accent-pink: #fd79a8; --accent-blue: #74b9ff; --accent-green: #55efc4;
    --accent-orange: #ffeaa7; --accent-red: #ff7675;
}
"""

# Base layout CSS — Clean lavender dashboard style
BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.main > div { padding: 0 2rem; }
.stApp { background: var(--bg-app); background-attachment: fixed; }
.block-container { max-width: 100%; padding-top: 1rem; background: transparent !important; }
section[data-testid="stMain"] { background: transparent !important; }
.main { background: transparent !important; }
div[data-testid="stAppViewContainer"] > .main { background: transparent !important; }
.stApp > div:first-child { background: transparent !important; }
div[data-testid="stAppViewContainer"] { background: var(--bg-app); background-attachment: fixed; }
div[data-testid="stDecoration"] { display: none; }

h1, h2, h3, h4, h5, h6 { font-weight: 700; letter-spacing: -0.02em; color: var(--text-primary); line-height: 1.25; }
h1 { font-size: 1.8rem; font-weight: 800; }
h2 { font-size: 1.4rem; font-weight: 700; }
h3 { font-size: 1.15rem; font-weight: 600; }

/* Sidebar */
div[data-testid="stSidebarContent"] {
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border);
    padding: 1rem 0.75rem;
}
div[data-testid="stSidebarContent"] .sidebar-section {
    background: var(--bg-card);
    border-radius: 16px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    border: 1px solid var(--border);
    box-shadow: var(--card-shadow);
}
section[data-testid="stSidebar"] { min-width: 300px; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6c5ce7 0%, #7c6cf7 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.01em;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 12px rgba(108,92,231,0.25);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(108,92,231,0.35);
}
.stButton > button:active { transform: translateY(0); }

div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6c5ce7 0%, #7c6cf7 100%);
    box-shadow: 0 4px 16px rgba(108,92,231,0.3);
}
div.stButton > button[kind="primary"]:hover {
    box-shadow: 0 8px 28px rgba(108,92,231,0.4);
}

/* Tabs */
div[data-testid="stTabs"] {
    background: var(--bg-card);
    border-radius: 18px;
    padding: 0.5rem 0.5rem 0;
    border: 1px solid var(--border);
    margin-bottom: 1.5rem;
    box-shadow: var(--card-shadow);
}
div[data-testid="stTabs"] button {
    border-radius: 12px 12px 0 0;
    padding: 0.7rem 1.5rem;
    font-weight: 500;
    font-size: 0.85rem;
    transition: all 0.3s;
    color: var(--tab-color);
    border: none;
    background: transparent;
}
div[data-testid="stTabs"] button:hover {
    color: var(--accent);
    background: var(--accent-bg);
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    background: var(--bg-tab-sel);
    color: var(--tab-sel-color);
    font-weight: 600;
    box-shadow: 0 -2px 12px rgba(108,92,231,0.08);
    border-bottom: 2.5px solid var(--accent);
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    border: 1px solid var(--border);
    box-shadow: var(--card-shadow);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
div[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: linear-gradient(180deg, var(--accent), var(--accent-light));
    border-radius: 0 4px 4px 0;
    opacity: 0;
    transition: opacity 0.3s;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: var(--card-shadow-hover);
}
div[data-testid="stMetric"]:hover::before { opacity: 1; }
div[data-testid="stMetric"] label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-weight: 800;
    font-size: 1.7rem;
    color: var(--accent);
}

/* Preset cards */
.preset-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.5rem 1.25rem 1.25rem;
    height: 100%;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--card-shadow);
    position: relative;
    overflow: hidden;
}
.preset-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #6c5ce7, #a29bfe, #fd79a8);
    opacity: 0;
    transition: opacity 0.35s;
}
.preset-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--card-shadow-hover);
    border-color: var(--border-hover);
}
.preset-card:hover::before { opacity: 1; }
.preset-card h4 { margin: 0 0 0.35rem 0; font-size: 0.95rem; font-weight: 700; color: var(--text-primary); }
.preset-card p { margin: 0; font-size: 0.75rem; color: var(--text-tertiary); font-weight: 500; }
.preset-card .card-icon {
    font-size: 2rem;
    margin-bottom: 0.75rem;
    display: block;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

/* Status widget */
div[data-testid="stStatusWidget"] {
    border-radius: 16px;
    border: 1px solid var(--border);
    background: var(--bg-card);
    box-shadow: var(--card-shadow);
}

/* Chat messages */
div[data-testid="stChatMessage"] {
    border-radius: 16px;
    border: 1px solid var(--border);
    margin-bottom: 0.75rem;
    background: var(--bg-card);
    box-shadow: var(--card-shadow);
    transition: all 0.25s;
    padding: 0.75rem 1rem;
}
div[data-testid="stChatMessage"]:hover { box-shadow: var(--card-shadow-hover); }
div[data-testid="stChatMessage"][aria-label="user"] { background: var(--bg-chat-user); }
div[data-testid="stChatMessage"] p { color: var(--text-primary); line-height: 1.6; }

/* Data frame */
div[data-testid="stDataFrame"] {
    border-radius: 16px;
    border: 1px solid var(--border);
    overflow: hidden;
    box-shadow: var(--card-shadow);
}
div[data-testid="stDataFrame"] thead tr th {
    background: var(--bg-table-header);
    font-weight: 600;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
}
div[data-testid="stDataFrame"] tbody tr td { color: var(--text-table); padding: 0.6rem 1rem; }
div[data-testid="stDataFrame"] tbody tr:nth-child(even) { background: var(--bg-table-even); }
div[data-testid="stDataFrame"] tbody tr:nth-child(odd) { background: var(--bg-table-odd); }
div[data-testid="stDataFrame"] tbody tr:hover { background: var(--accent-bg); }

/* Expander */
div[data-testid="stExpander"] {
    border-radius: 14px;
    border: 1px solid var(--border);
    background: var(--bg-card);
    margin-bottom: 0.75rem;
    box-shadow: var(--card-shadow);
}
div[data-testid="stExpander"] summary { color: var(--text-primary); font-weight: 500; }

/* Select & Slider */
div[data-testid="stSelectbox"] label, div[data-testid="stSlider"] label {
    font-weight: 600;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: var(--bg-input) !important;
    border-color: var(--border-input) !important;
    color: var(--text-input) !important;
    border-radius: 10px !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] span { color: var(--text-input) !important; }
div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(108,92,231,0.1) !important;
}
div[data-testid="stSlider"] div[data-baseweb="slider"] div { color: var(--accent-light); }

hr { border: none; height: 1px; background: var(--hr-grad); margin: 1.5rem 0; }

/* Alerts */
div[data-testid="stInfo"] { background: var(--bg-info) !important; color: var(--text-info) !important; border-left: 3px solid var(--accent); }
div[data-testid="stSuccess"] { background: var(--bg-success) !important; color: var(--text-success) !important; border-left: 3px solid #4caf50; }
div[data-testid="stError"] { background: var(--bg-error) !important; color: var(--text-error) !important; border-left: 3px solid #f44336; }
div[data-testid="stInfo"], div[data-testid="stSuccess"], div[data-testid="stError"] {
    border-radius: 12px;
    border: 1px solid var(--border);
}

div[data-testid="stSpinner"] { text-align: center; padding: 2rem; }

/* Chat input */
div[data-testid="stChatInput"] {
    border-radius: 16px;
    border: 1px solid var(--border-input);
    background: var(--bg-card);
    box-shadow: var(--card-shadow);
    transition: all 0.3s;
}
div[data-testid="stChatInput"] input { color: var(--text-input); }
div[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(108,92,231,0.12), var(--card-shadow);
}

/* Text input */
div[data-testid="stTextInput"] input {
    border-radius: 12px;
    border: 1px solid var(--border-input);
    background: var(--bg-input);
    color: var(--text-input);
    transition: all 0.3s;
}
div[data-testid="stTextInput"] input::placeholder { color: var(--text-placeholder); }
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(108,92,231,0.1);
    outline: none;
}

/* Text area */
div[data-testid="stTextArea"] textarea {
    border-radius: 14px;
    border: 1px solid var(--border-input);
    background: var(--bg-input);
    color: var(--text-input);
    transition: all 0.3s;
}
div[data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(108,92,231,0.1);
    outline: none;
}

div[data-testid="stCheckbox"] label { font-weight: 500; color: var(--text-primary); }

/* Dropdown menu */
div[data-baseweb="menu"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    box-shadow: var(--shadow-lg) !important;
    overflow: hidden;
}
div[data-baseweb="menu"] li:hover { background: var(--accent-bg) !important; }
div[data-baseweb="menu"] li { color: var(--text-input) !important; padding: 0.5rem 1rem !important; }

.stCodeBlock {
    background: var(--bg-code) !important;
    border-radius: 12px;
    border: 1px solid var(--border);
}

/* Back button */
.back-zone .stButton > button {
    background: none !important;
    border: none !important;
    color: var(--back-btn) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 0.2rem 0.6rem !important;
    min-height: 0 !important;
    height: auto !important;
    line-height: 1.4 !important;
    box-shadow: none !important;
    transition: all 0.2s;
    border-radius: 8px;
}
.back-zone .stButton > button:hover {
    color: var(--back-hover) !important;
    background: var(--accent-bg) !important;
    transform: none !important;
    box-shadow: none !important;
}

/* Plotly chart */
.stPlotlyChart {
    background: var(--bg-card);
    border-radius: 18px;
    padding: 0.75rem;
    border: 1px solid var(--border);
    box-shadow: var(--card-shadow);
}

/* Markdown */
.stMarkdown p, .stMarkdown li, .stMarkdown span:not([class]) { color: var(--text-primary); line-height: 1.6; }
.stMarkdown strong { color: var(--text-primary); }
.stCaption { color: var(--text-caption) !important; }
div[data-testid="stRadio"] label { color: var(--text-primary) !important; }
div[role="radiogroup"] label { color: var(--text-primary) !important; }
div[data-testid="stToggle"] label { color: var(--text-primary) !important; }
"""

# Initialize header_visible if not set
if "header_visible" not in st.session_state:
    st.session_state.header_visible = False

# Assemble CSS based on theme
css_output = BASE_CSS
if not st.session_state.header_visible:
    css_output += "header[data-testid='stHeader'] { display: none !important; }"
if theme == "light":
    css_output += LIGHT_VARS
elif theme == "dark":
    css_output += DARK_VARS
else:  # system
    css_output += LIGHT_VARS
    css_output += "@media (prefers-color-scheme: dark) {" + DARK_VARS + "}"

st.markdown(f"<style>{css_output}</style>", unsafe_allow_html=True)

DATA_PATH = os.path.join(os.path.dirname(__file__), "ai-impact-jobs-layoff-risk-dataset.csv")
DYNAMIC_PATH = os.path.join(os.path.dirname(__file__), "dynamic.py")

PRESET_ANALYSES = [
    {
        "key": "preset_automation",
        "icon": "🤖",
        "title": "Automation vs Layoff Risk",
        "subtitle": "Impact Model",
        "query": "Analyze how Routine_Task_Percentage and Tasks_Automated_Percentage correlate with Layoff_Risk across different industries. Use a grouped bar chart or scatter plot.",
    },
    {
        "key": "preset_creativity",
        "icon": "🎨",
        "title": "Creativity & Human Interaction",
        "subtitle": "Safe Haven Model",
        "query": "Show the relationship between Creativity_Requirement, Human_Interaction_Level, and Layoff_Risk by industry. Use a heatmap or bubble chart.",
    },
    {
        "key": "preset_learning",
        "icon": "📚",
        "title": "AI Learning & Adaptability",
        "subtitle": "Transition Curve",
        "query": "Compare AI_Usage_Hours_Per_Week and AI_Training_Hours across Education_Level and Industry. Use a grouped bar or box plot.",
    },
    {
        "key": "preset_tools",
        "icon": "🛠️",
        "title": "AI Tools & Experience Gap",
        "subtitle": "Tech Generation Divide",
        "query": "Visualize how Age and Years_of_Experience relate to Number_of_AI_Tools_Used. Use a scatter plot colored by Industry.",
    },
]

if "df" not in st.session_state:
    st.session_state.df = pd.read_csv(DATA_PATH)
if "api_key" not in st.session_state:
    st.session_state.api_key = BUILTIN_API_KEY
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = BUILTIN_BASE_URL
if "api_model" not in st.session_state:
    st.session_state.api_model = BUILTIN_MODEL
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "generated_code" not in st.session_state:
    st.session_state.generated_code = False
if "tab2_input_key" not in st.session_state:
    st.session_state.tab2_input_key = 0
if "active_preset" not in st.session_state:
    st.session_state.active_preset = None
if "header_visible" not in st.session_state:
    st.session_state.header_visible = False
if "crawl_auto_enabled" not in st.session_state:
    st.session_state.crawl_auto_enabled = True
if "auto_crawler_started" not in st.session_state:
    if st.session_state.crawl_auto_enabled:
        auto_crawler.start(interval_minutes=30)
    st.session_state.auto_crawler_started = True
if "tab1_showing_result" not in st.session_state:
    st.session_state.tab1_showing_result = False
if "tab2_showing_chat" not in st.session_state:
    st.session_state.tab2_showing_chat = False



class AgentTools:
    @staticmethod
    def stats_analytics(query_description: str, df: pd.DataFrame) -> str:
        results = []
        q = query_description.lower()

        if any(w in q for w in ["average", "mean", "avg"]):
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            group_col = None
            for col in ["Industry", "Job_Role", "Education_Level", "Layoff_Risk"]:
                if col.lower() in q:
                    group_col = col
                    break
            if group_col:
                agg = df.groupby(group_col)[numeric_cols].mean().round(2)
                results.append(f"Mean values grouped by {group_col}:\n{agg.to_string()}")
            else:
                agg = df[numeric_cols].mean().round(2)
                results.append(f"Overall numeric means:\n{agg.to_string()}")

        if any(w in q for w in ["max", "maximum", "top", "highest"]):
            for col in ["Layoff_Risk", "AI_Adoption_Level"]:
                if col.lower() in q or "risk" in q:
                    top = df.groupby("Industry")[col].apply(
                        lambda x: x.value_counts().idxmax() if x.dtype == "object" else x.max()
                    ).reset_index()
                    results.append(f"Highest {col} by industry:\n{top.to_string()}")

        if any(w in q for w in ["industry", "sector"]):
            risk_counts = df["Industry"].value_counts()
            results.append(f"Sample count per industry:\n{risk_counts.to_string()}")
            if "Layoff_Risk" in df.columns:
                cross = pd.crosstab(df["Industry"], df["Layoff_Risk"])
                results.append(f"Industry x Layoff_Risk crosstab:\n{cross.to_string()}")

        if any(w in q for w in ["tool", "ai tools"]):
            if "Number_of_AI_Tools_Used" in df.columns:
                stats = df.groupby("Industry")["Number_of_AI_Tools_Used"].agg(["mean", "max", "min"]).round(2)
                results.append(f"AI tool usage stats by industry:\n{stats.to_string()}")

        if any(w in q for w in ["routine", "automation", "task"]):
            cols = ["Routine_Task_Percentage", "Tasks_Automated_Percentage"]
            avail = [c for c in cols if c in df.columns]
            if avail:
                corr = df[avail + ["Layoff_Risk"] if "Layoff_Risk" in df.columns else avail].corr(numeric_only=True)
                results.append(f"Correlation matrix (routine/automation):\n{corr.to_string()}")

        if any(w in q for w in ["creativity", "human", "interaction"]):
            cols = ["Creativity_Requirement", "Human_Interaction_Level"]
            avail = [c for c in cols if c in df.columns]
            if avail:
                corr = df[avail + ["Layoff_Risk"] if "Layoff_Risk" in df.columns else avail].corr(numeric_only=True)
                results.append(f"Correlation matrix (creativity/human):\n{corr.to_string()}")

        if any(w in q for w in ["education", "learning", "training", "hours"]):
            if "AI_Training_Hours" in df.columns:
                stats = df.groupby("Education_Level")["AI_Training_Hours"].agg(["mean", "max", "min"]).round(2)
                results.append(f"AI Training Hours by Education:\n{stats.to_string()}")
            if "AI_Usage_Hours_Per_Week" in df.columns:
                stats = df.groupby("Education_Level")["AI_Usage_Hours_Per_Week"].agg(["mean", "max", "min"]).round(2)
                results.append(f"AI Usage Hours/Week by Education:\n{stats.to_string()}")

        if any(w in q for w in ["age", "experience", "years", "tool"]):
            if all(c in df.columns for c in ["Age", "Years_of_Experience", "Number_of_AI_Tools_Used"]):
                corr = df[["Age", "Years_of_Experience", "Number_of_AI_Tools_Used"]].corr()
                results.append(f"Correlation (Age, Experience, AI Tools):\n{corr.to_string()}")

        if not results:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            obj_cols = df.select_dtypes(include=["object"]).columns.tolist()
            results.append(f"Dataset: {len(df)} rows, {len(df.columns)} columns")
            results.append(f"Numeric columns: {', '.join(numeric_cols)}")
            results.append(f"Categorical columns: {', '.join(obj_cols)}")
            results.append(f"Layoff_Risk distribution:\n{df['Layoff_Risk'].value_counts().to_string()}")

        return "\n\n".join(results)

    @staticmethod
    def data_fetcher(topic: str, max_items: int = 5) -> str:
        return fetch_vibe_coding_news(topic, max_items)


def load_chat_gateway():
    if not st.session_state.api_key:
        st.warning("Please enter your API Key in the sidebar first.")
        st.stop()
    return Chat(
        api_key=st.session_state.api_key,
        base_url=st.session_state.api_base_url,
        model=st.session_state.api_model,
    )


def generate_visualization(query: str):
    df = st.session_state.df
    df_head = df.head().to_string()
    columns_info = "\n".join([f"  - {col}: {dtype}" for col, dtype in df.dtypes.items()])

    prompt = f"""You are a Python data visualization expert. You have a pandas DataFrame `df` with the following structure:

Column info:
{columns_info}

First 5 rows:
{df_head}

The dataset is about AI impact on jobs and layoff risk across industries.

Generate a complete Python function named "graph(df)" that:
1. Takes the dataframe as the only argument
2. Creates a Plotly Express visualization based on this user request: "{query}"
3. Renders with st.plotly_chart(fig, use_container_width=True)
4. Includes proper labels, titles, and hover information

Only output the raw Python code starting with "import". NO markdown code blocks. NO explanations."""

    chat = Chat(
        api_key=st.session_state.api_key,
        base_url=st.session_state.api_base_url,
        model=st.session_state.api_model,
        messages=[
            {"role": "system", "content": "You are a Python data visualization expert. Output only code, no explanations."},
            {"role": "user", "content": prompt}
        ]
    )
    response = chat.get_response_message(stream=True)
    code = response["content"]

    code_clean = re.sub(r"```python\s*|\s*```", "", code).strip()
    code_clean = re.sub(r"^python\s*", "", code_clean, flags=re.IGNORECASE)
    with open(DYNAMIC_PATH, "w", encoding="utf-8") as f:
        f.write(code_clean)

    importlib.reload(sys.modules.get("dynamic"))
    st.session_state.generated_code = True


def agent_process(user_input: str):
    df = st.session_state.df

    with st.status("🤖 **Agent processing your request…**", expanded=True) as status:
        status.update(label="🧠 **Stage 1:** Intent Recognition", state="running")
        q = user_input.lower()
        calc_keywords = [
            "calculate", "statistics", "average", "mean", "sum", "count", "max", "min",
            "distribution", "ratio", "percentage", "how many", "how much",
        ]
        trend_keywords = [
            "trend", "news", "latest", "social", "vibe coding", "cursor",
            "reddit", "twitter", "hacker news", "community",
        ]

        is_calculation = any(k in q for k in calc_keywords)
        is_trend = any(k in q for k in trend_keywords)

        if is_calculation:
            thought = "Routing to stats_analytics for Pandas aggregation"
            action = "stats_analytics"
        elif is_trend:
            thought = "Routing to data_fetcher for live trend collection"
            action = "data_fetcher"
        else:
            thought = "General advisory — running stats_analytics + LLM"
            action = "stats_analytics + llm"

        st.caption(f"🧠 **Thought:** {thought}  ·  🛠️ **Action:** `{action}`")

        status.update(label="🛠️ **Stage 2:** Tool Execution", state="running")
        observation = ""

        if is_calculation or (not is_trend):
            status.update(label="📊 Running stats_analytics…", state="running")
            observation += "[Stats Analytics Results]\n"
            observation += AgentTools.stats_analytics(user_input, df)
            st.caption(f"stats_analytics → {len(observation.split(chr(10)))} lines")

        if is_trend:
            status.update(label="🌐 Running data_fetcher…", state="running")
            trend_result = AgentTools.data_fetcher(user_input)
            observation += "\n\n[Trend Collection Results]\n" + trend_result
            st.caption(f"data_fetcher → {len(trend_result.split(chr(10)))} lines")

        status.update(label="📊 **Stage 3:** Observation", state="running")
        with st.expander("🔍 View raw tool output", expanded=False):
            st.text_area("Observation", observation, height=180, disabled=True, label_visibility="collapsed")

        status.update(label="🤖 **Stage 4:** LLM Final Response", state="running")

        system_prompt = """You are an expert AIGC job impact analyst and career transition advisor.
Based on the factual tool output above, provide data-driven insights and recommendations.
Always cite your sources (Stats Analytics or Trend Collection).
Be professional, objective, and insightful."""
        chat = Chat(
            api_key=st.session_state.api_key,
            base_url=st.session_state.api_base_url,
            model=st.session_state.api_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User question: {user_input}\n\nTool data:\n{observation}"}
            ]
        )
        final_response = chat.get_response_message(stream=False)
        reply = final_response["content"]

        status.update(label="✅ Analysis complete", state="complete", expanded=False)

    return reply


st.sidebar.markdown("""
<div style="text-align:center; padding: 1.25rem 0 1rem;">
    <div style="width:48px; height:48px; background:linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:1.5rem; margin:0 auto 0.75rem; box-shadow:0 4px 16px rgba(108,92,231,0.3);">📊</div>
    <div style="font-size:1.5rem; font-weight:800; color:#6c5ce7; letter-spacing:-0.03em;">
        VibeTrends
    </div>
    <div style="font-size:0.65rem; color:var(--text-muted); letter-spacing:0.15em; text-transform:uppercase; margin-top:4px; font-weight:500;">CONTROL PANEL</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
st.sidebar.markdown("#### 🔌 API")
api_status = st.sidebar.empty()
api_status.success("✅ Built-in DeepSeek")
with st.sidebar.expander("Override Settings", expanded=False):
    override_key = st.text_input("Custom API Key", value="", type="password", help="Leave empty to use built-in key")
    if override_key:
        st.session_state.api_key = override_key
    api_provider = st.selectbox(
        "Provider",
        options=["DeepSeek (Built-in)", "SiliconFlow", "Custom"],
        index=0,
    )
    if api_provider == "SiliconFlow":
        st.session_state.api_base_url = "https://api.siliconflow.cn/v1"
        st.session_state.api_model = "MiniMaxAI/MiniMax-M2.5"
    elif api_provider == "DeepSeek (Built-in)":
        st.session_state.api_base_url = BUILTIN_BASE_URL
        st.session_state.api_model = BUILTIN_MODEL
    elif api_provider == "Custom":
        st.session_state.api_base_url = st.text_input("Base URL", value=st.session_state.api_base_url)
        st.session_state.api_model = st.text_input("Model", value=st.session_state.api_model)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
st.sidebar.markdown("#### 📡 Crawl")
auto_crawl_on = st.sidebar.toggle("Auto-crawl on startup", key="crawl_auto_enabled", help="Automatically crawl 5 preset topics when the app loads")
crawl_history_count = st.sidebar.slider("History display count", 5, 50, 10, key="crawl_history_count")
st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)

df = st.session_state.df

industries = ["All"] + sorted(df["Industry"].unique().tolist())
risk_levels = ["All"] + sorted(df["Layoff_Risk"].unique().tolist())
education_levels = ["All"] + sorted(df["Education_Level"].unique().tolist())
company_sizes = ["All"] + sorted(df["Company_Size"].unique().tolist())

# Stored values — init from session state or defaults
if "industry_filter" not in st.session_state:
    st.session_state.industry_filter = "All"
if "risk_filter" not in st.session_state:
    st.session_state.risk_filter = "All"
if "education_filter" not in st.session_state:
    st.session_state.education_filter = "All"
if "size_filter" not in st.session_state:
    st.session_state.size_filter = "All"

selected_industry = st.sidebar.selectbox("Industry", industries, key="industry_filter", label_visibility="collapsed")
selected_risk = st.sidebar.selectbox("Layoff Risk", risk_levels, key="risk_filter", label_visibility="collapsed")
selected_education = st.sidebar.selectbox("Education Level", education_levels, key="education_filter", label_visibility="collapsed")
selected_size = st.sidebar.selectbox("Company Size", company_sizes, key="size_filter", label_visibility="collapsed")

have_active_filters = any(x != "All" for x in [selected_industry, selected_risk, selected_education, selected_size])
if have_active_filters:
    def _reset_filters():
        st.session_state.industry_filter = "All"
        st.session_state.risk_filter = "All"
        st.session_state.education_filter = "All"
        st.session_state.size_filter = "All"
    st.sidebar.markdown('<div class="back-zone">', unsafe_allow_html=True)
    st.sidebar.button("← Reset Filters", key="tab3_back", help="Reset all filters", use_container_width=True, on_click=_reset_filters)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

filtered_df = df.copy()
if selected_industry != "All":
    filtered_df = filtered_df[filtered_df["Industry"] == selected_industry]
if selected_risk != "All":
    filtered_df = filtered_df[filtered_df["Layoff_Risk"] == selected_risk]
if selected_education != "All":
    filtered_df = filtered_df[filtered_df["Education_Level"] == selected_education]
if selected_size != "All":
    filtered_df = filtered_df[filtered_df["Company_Size"] == selected_size]

st.sidebar.markdown(f"""
<div style="display:flex; justify-content:space-between; padding:0.4rem 0.8rem; background:var(--accent-bg); border-radius:8px; margin-top:0.5rem; font-size:0.8rem;">
    <span style="color:var(--text-muted);">Filtered</span>
    <span style="font-weight:700; color:var(--accent);">{len(filtered_df)}</span>
    <span style="color:var(--text-tertiary);">/</span>
    <span style="color:var(--text-muted);">Total</span>
    <span style="font-weight:700; color:var(--text-primary);">{len(df)}</span>
</div>
""", unsafe_allow_html=True)

with st.sidebar.expander("📖 Schema", expanded=False):
    st.markdown("""
    - **Age**: Employee age
    - **Education_Level**: Education attainment
    - **Years_of_Experience**: Work experience
    - **Industry**: Industry sector
    - **Job_Role**: Job title
    - **Company_Size**: Company scale
    - **Job_Level**: Seniority level
    - **Routine_Task_Percentage**: % routine/repetitive tasks
    - **Creativity_Requirement**: Creativity demand
    - **Human_Interaction_Level**: Interpersonal demand
    - **AI_Adoption_Level**: AI adoption level
    - **Number_of_AI_Tools_Used**: AI tools count
    - **AI_Usage_Hours_Per_Week**: Weekly AI usage
    - **Tasks_Automated_Percentage**: % tasks automated
    - **AI_Training_Hours**: AI training received
    - **Layoff_Risk**: Layoff risk level
    """)

st.markdown("""
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem; padding:0.5rem 0;">
    <div style="display:flex; align-items:center; gap:1.25rem;">
        <div style="width:52px; height:52px; background:linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); border-radius:16px; display:flex; align-items:center; justify-content:center; font-size:1.7rem; box-shadow:0 4px 16px rgba(108,92,231,0.3);">📊</div>
        <div>
            <div style="font-size:1.8rem; font-weight:800; color:#6c5ce7; letter-spacing:-0.04em; line-height:1.1;">
                VibeTrends AI
            </div>
            <div style="font-size:0.72rem; color:var(--text-tertiary); letter-spacing:0.1em; text-transform:uppercase; margin-top:4px; font-weight:500;">
                AIGC Job Impact &amp; Vibe Coding Diagnostic Platform
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

bar_col1, bar_col2 = st.columns([6, 1])
with bar_col2:
    st.markdown('<div class="back-zone" style="text-align:right;">', unsafe_allow_html=True)
    label = "✕" if st.session_state.header_visible else "☰"
    if st.button(label, key="header_toggle", help="Show/hide Streamlit header bar", use_container_width=False):
        st.session_state.header_visible = not st.session_state.header_visible
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr style='margin:0.75rem 0 1rem;'>", unsafe_allow_html=True)

show_help = st.checkbox("📖 Guide", value=False)

if show_help:
    st.markdown("""
### 1. Getting Started — API Key Configuration
This application requires an LLM API key to power AI features. Configure it in the **sidebar** (left panel):
- **API Key**: Paste your key into the password field (e.g., `sk-477e...`)
- **API Provider**: Select `DeepSeek` if using the sample key, or choose `SiliconFlow` / `Custom` for other providers
- If you entered a key via terminal at startup, the sidebar will display a confirmation message

---

### 2. Tab 1 — Dynamic Visualization (Natural Language to Chart)
Two ways to generate charts:

**Preset Analysis Cards** (top of the page):
Click **"▶ Analyze"** on any of the four cards to instantly generate a visualization:
- 🤖 **Automation vs Layoff Risk** — relationship between routine tasks, automation, and layoff risk
- 🎨 **Creativity & Human Interaction** — how creativity and social skills affect job security
- 📚 **AI Learning & Adaptability** — training and usage patterns across education levels
- 🛠️ **AI Tools & Experience Gap** — age and experience vs. AI tool adoption

**Custom Chart Description** (below the cards):
- Type your visualization request in the text input and click **"🚀 Generate"**
- Supports both English and Chinese descriptions
- Examples: *"Bar chart of average AI usage hours by industry"*, *"Scatter plot of age vs AI usage hours colored by industry"*

The generated chart appears in the **"Rendered Result"** section below. All Plotly charts support zoom, pan, and hover tooltips.

---

### 3. Tab 2 — AI Career Advisor (Agent + Tool Use)
Interactive AI agent that answers questions with real data. Type your question in the chat box at the bottom.

Three query types:

| Query Type | Description | Examples |
|---|---|---|
| **Data Calculation** | Real Pandas aggregation on the dataset | *"Average AI training hours by industry"*, *"Which industry has the highest layoff risk?"* |
| **Live Trends** | Fetches discussions from V2EX (mock fallback if unavailable) | *"Latest Vibe Coding trends"*, *"Recent tech layoff news"* |
| **General Advisory** | Data analysis + LLM insight | *"Which jobs are safest from AI?"*, *"What skills should I learn?"* |

The agent displays its reasoning chain: **Thought → Action → Observation** before the final response.

---

### 4. Tab 3 — Data Explorer (Filtering & Overview)
**Sidebar Filters** (scroll down the sidebar to find **📂 Data Filters**):
- **Industry** / **Layoff Risk** / **Education Level** / **Company Size**

**Key Metrics** (top row): Total Records, Unique Industries, High Risk Roles, Avg AI Tools Used

**Data Table**: Scrollable view of filtered records (20,000 rows, 16 columns)

**Quick Overview**: Bar chart of layoff risk distribution

> **Note**: Sidebar filters are **global** — they apply across all three tabs.

---

### 5. Additional Notes
- Dataset source: Kaggle — 20,000 employee records, 16 columns (age, industry, job role, AI usage, layoff risk, etc.)
- Click **📖 Dataset Schema** at the bottom of the sidebar for column descriptions
- All charts support interactive features: zoom, pan, hover tooltips, and PNG export
        """)

tab1, tab2, tab3 = st.tabs(["🎨 Dynamic Visualization", "🤖 AI Career Advisor", "📋 Data Explorer"])

with tab3:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.75rem; padding:0.85rem 1.25rem; background:var(--bg-card); border-radius:16px; border:1px solid var(--border); box-shadow:var(--card-shadow);">
        <div style="width:42px; height:42px; background:linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.3rem; box-shadow:0 2px 8px rgba(108,92,231,0.25);">📋</div>
        <div>
            <div style="font-size:1.15rem; font-weight:700; color:var(--text-primary);">Dataset Preview</div>
            <div style="font-size:0.7rem; color:var(--text-tertiary); letter-spacing:0.04em;">Sidebar filters apply globally across all tabs</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric("Total Records", len(filtered_df))
    with mcol2:
        st.metric("Industries", filtered_df["Industry"].nunique())
    with mcol3:
        high_risk = len(filtered_df[filtered_df["Layoff_Risk"] == "High"]) if "High" in filtered_df["Layoff_Risk"].values else 0
        st.metric("High Risk Roles", high_risk)
    with mcol4:
        avg_tools = round(filtered_df["Number_of_AI_Tools_Used"].mean(), 1) if "Number_of_AI_Tools_Used" in filtered_df.columns else 0
        st.metric("Avg AI Tools", avg_tools)

    st.dataframe(filtered_df, use_container_width=True, height=400)

    overview_col1, overview_col2 = st.columns([1, 1])
    with overview_col1:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem; padding:0.55rem 0.85rem; background:var(--bg-card); border-radius:10px; border:1px solid var(--border); box-shadow:var(--card-shadow);">
            <div style="width:28px; height:28px; background:linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:0.85rem;">📈</div>
            <div style="font-size:0.9rem; font-weight:600; color:var(--text-primary);">Risk Distribution</div>
        </div>
        """, unsafe_allow_html=True)
        risk_counts = filtered_df["Layoff_Risk"].value_counts().reset_index()
        risk_counts.columns = ["Layoff_Risk", "Count"]
        risk_colors = {"Low": "#81c784", "Medium": "#ffb74d", "High": "#e57373"}
        fig_risk = px.bar(
            risk_counts, x="Layoff_Risk", y="Count",
            color="Layoff_Risk", color_discrete_map=risk_colors,
            title=None, text_auto=True
        )
        fig_risk.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_risk, use_container_width=True)

    with overview_col2:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem; padding:0.55rem 0.85rem; background:var(--bg-card); border-radius:10px; border:1px solid var(--border); box-shadow:var(--card-shadow);">
            <div style="width:28px; height:28px; background:linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:0.85rem;">📡</div>
            <div style="font-size:0.9rem; font-weight:600; color:var(--text-primary);">Crawl History</div>
        </div>
        """, unsafe_allow_html=True)
        crawl_df = DataPersistence.load_history(st.session_state.get("crawl_history_count", 10))
        if crawl_df.empty:
            st.info("No records yet. Background auto-crawler is running — data will appear shortly.")
        else:
            st.caption(f"Latest {len(crawl_df)} records")
            st.dataframe(crawl_df, use_container_width=True, height=280)

with tab1:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.75rem; padding:0.85rem 1.25rem; background:var(--bg-card); border-radius:16px; border:1px solid var(--border); box-shadow:var(--card-shadow);">
        <div style="width:42px; height:42px; background:linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.3rem; box-shadow:0 2px 8px rgba(108,92,231,0.25);">🎯</div>
        <div>
            <div style="font-size:1.15rem; font-weight:700; color:var(--text-primary);">Preset Analysis</div>
            <div style="font-size:0.7rem; color:var(--text-tertiary); letter-spacing:0.04em;">One-click deep-dive visualizations</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    preset_cols = st.columns(4)
    for i, (col, preset) in enumerate(zip(preset_cols, PRESET_ANALYSES)):
        with col:
            st.markdown(f"""
            <div class="preset-card">
                <span class="card-icon">{preset["icon"]}</span>
                <h4>{preset["title"]}</h4>
                <p>{preset["subtitle"]}</p>
            </div>
            """, unsafe_allow_html=True)
            clicked = st.button(f"▶ Analyze", key=preset["key"], use_container_width=True)
            if clicked:
                st.session_state.active_preset = preset["key"]
                st.session_state.preset_query = preset["query"]

    st.markdown("---")

    if st.session_state.get("active_preset"):
        with st.spinner("🤖 AI generating visualization..."):
            try:
                generate_visualization(st.session_state.preset_query)
                st.success("✅ Code generated successfully!")
                st.session_state.tab1_showing_result = True
            except Exception as e:
                st.error(f"Generation failed: {e}")
        st.session_state.active_preset = None
        st.rerun()

    st.markdown("""
    <div style="padding:0.65rem 1rem; background:var(--bg-card); border-radius:12px; border:1px solid var(--border); margin-bottom:1rem; box-shadow:var(--card-shadow);">
        <div style="font-size:1rem; font-weight:600; color:var(--text-primary);">Custom Chart</div>
        <div style="font-size:0.7rem; color:var(--text-tertiary); margin-top:2px;">Describe any chart in natural language — AI writes the Plotly code instantly</div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([4, 1])
    with col_left:
        query_placeholder = "e.g. Show distribution of AI tool usage across industries"
        tab1_query = st.text_input("Describe your chart", value=query_placeholder, key="tab1_query", label_visibility="collapsed")
    with col_right:
        generate_btn = st.button("🚀 Generate", type="primary", use_container_width=True)

    if generate_btn and tab1_query and tab1_query != query_placeholder:
        if not st.session_state.api_key:
            st.error("API Key not configured. Please check the sidebar settings.")
        else:
            with st.spinner("🤖 AI writing visualization code..."):
                try:
                    generate_visualization(tab1_query)
                    st.success("✅ Code generated successfully!")
                    st.session_state.tab1_showing_result = True
                except Exception as e:
                    st.error(f"Generation failed: {e}")

    st.markdown("---")
    header_col, back_col = st.columns([1, 1])
    with header_col:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.5rem; padding:0.6rem 0.85rem; background:var(--bg-card); border-radius:12px; border:1px solid var(--border); box-shadow:var(--card-shadow);">
            <div style="width:32px; height:32px; background:linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1rem;">📊</div>
            <div style="font-size:1rem; font-weight:600; color:var(--text-primary);">Rendered Result</div>
        </div>
        """, unsafe_allow_html=True)
    with back_col:
        if st.session_state.tab1_showing_result:
            st.markdown('<div style="text-align:right;"><div class="back-zone">', unsafe_allow_html=True)
            if st.button("← Back", key="tab1_back", help="Back to chart selection", use_container_width=False):
                st.session_state.tab1_showing_result = False
                st.rerun()
            st.markdown('</div></div>', unsafe_allow_html=True)

    if st.session_state.tab1_showing_result:
        try:
            importlib.reload(sys.modules.get("dynamic"))
            dynamic.graph(filtered_df)
        except Exception:
            st.session_state.tab1_showing_result = False
            st.rerun()
    else:
        st.info("Click 'Generate' above or use a Preset Card to create a visualization")
        with st.expander("View current dynamic.py code"):
            if os.path.exists(DYNAMIC_PATH):
                with open(DYNAMIC_PATH, "r", encoding="utf-8") as f:
                    st.code(f.read(), language="python")

with tab2:
    chat_header_col, chat_back_col = st.columns([1, 1])
    with chat_header_col:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.75rem; padding:0.85rem 1.25rem; background:var(--bg-card); border-radius:16px; border:1px solid var(--border); box-shadow:var(--card-shadow);">
            <div style="width:42px; height:42px; background:linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.3rem; box-shadow:0 2px 8px rgba(108,92,231,0.25);">🤖</div>
            <div>
                <div style="font-size:1.15rem; font-weight:700; color:var(--text-primary);">AI Career Advisor</div>
                <div style="font-size:0.7rem; color:var(--text-tertiary); letter-spacing:0.04em;">Transition Diagnostic · Data-driven insights</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with chat_back_col:
        if len(st.session_state.chat_messages) > 0:
            st.markdown('<div style="text-align:right;"><div class="back-zone">', unsafe_allow_html=True)
            if st.button("← New Chat", key="tab2_back", help="Clear conversation and start fresh", use_container_width=False):
                st.session_state.chat_messages = []
                st.session_state.tab2_input_key += 1
                st.rerun()
            st.markdown('</div></div>', unsafe_allow_html=True)

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input(
        "e.g. Calculate average AI usage by industry, or what's the latest on Vibe Coding...",
        key=f"chat_input_{st.session_state.tab2_input_key}"
    )

    if prompt:
        if not st.session_state.api_key:
            st.error("API Key not configured. Please check the sidebar settings.")
        else:
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                reply = agent_process(prompt)
                st.markdown(reply)

            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
            st.session_state.tab2_input_key += 1
            st.rerun()

st.markdown("""
<div style="margin-top:3rem; padding:1.5rem 0; text-align:center;">
    <div style="height:1px; background:var(--hr-grad); margin-bottom:1.5rem;"></div>
    <div style="font-size:0.7rem; color:var(--text-muted); letter-spacing:0.06em;">
        VibeTrends AI © 2026 · Built with Streamlit · Data: Kaggle AI Impact on Jobs &amp; Layoff Risk
    </div>
</div>
""", unsafe_allow_html=True)
