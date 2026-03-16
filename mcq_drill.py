"""
Primary FRCA MCQ Drill
Streamlit app with fixed question bank + AI-generated questions, timed/untimed modes,
per-topic performance tracking, and Supabase persistence.

Secrets required (.streamlit/secrets.toml):
  SUPABASE_URL = "..."
  SUPABASE_KEY = "..."
  ANTHROPIC_API_KEY = "..."
"""

import streamlit as st
import json
import uuid
import random
import time
from datetime import datetime, timedelta
from anthropic import Anthropic
import math

st.set_page_config(
    page_title="FRCA MCQ Drill",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,400;1,300&family=IBM+Plex+Sans:wght@300;400;500&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --bg: #0e1117;
    --surface: #161b27;
    --surface2: #1e2535;
    --border: #252e42;
    --border2: #2e3a52;
    --nav: #4f9cf9;       /* accent ONLY for nav/interactive */
    --text: #e8edf5;
    --muted: #6b7a99;
    --green: #4ade80;
    --green-bg: #0a1f14;
    --green-border: #14532d;
    --red: #f87171;
    --red-bg: #1c0a0a;
    --red-border: #7f1d1d;
}

html, body, [class*="css"],
.stApp, .stApp > div,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"], [data-testid="stMainBlockContainer"],
.main, .main > div, .block-container {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 16px !important;
    background: var(--bg) !important;
    color: var(--text) !important;
    letter-spacing: -0.01em !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    transition: transform 0.25s ease, width 0.25s ease !important;
    overflow: hidden !important;
}
/* Hide Streamlit's own collapse controls — we use our own */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
.st-emotion-cache-pb6fr7,
.st-emotion-cache-czk5ss { display: none !important; }

[data-testid="stSidebar"] *,
[data-testid="stSidebarContent"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebarContent"] .stButton > button {
    background: transparent !important;
    border: none !important;
    border-radius: 6px !important;
    color: var(--muted) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 400 !important;
    font-size: 14px !important;
    text-align: left !important;
    padding: 10px 14px !important;
    justify-content: flex-start !important;
    width: 100% !important;
    transition: all 0.1s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebarContent"] .stButton > button:hover {
    background: var(--surface2) !important;
    color: var(--text) !important;
}
/* Close button — first button in sidebar */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button {
    border: 1px solid #252e42 !important;
    color: #6b7a99 !important;
    font-size: 16px !important;
    padding: 6px !important;
    text-align: center !important;
    justify-content: center !important;
    min-height: 36px !important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button:hover {
    border-color: #f87171 !important;
    color: #f87171 !important;
    background: transparent !important;
}

/* ── Buttons — default ── */
.stButton > button {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    border-radius: 8px !important;
    border: 1px solid var(--border2) !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    transition: all 0.12s ease !important;
    letter-spacing: 0 !important;
    padding: 10px 18px !important;
    min-height: 44px !important;
}
.stButton > button:hover {
    background: var(--surface2) !important;
    border-color: var(--nav) !important;
    color: var(--text) !important;
}

/* ── Answer option cards (target .answer-opt class via button key naming) ── */
button[kind="secondary"] {
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 14px 18px !important;
    min-height: 52px !important;
    white-space: normal !important;
    height: auto !important;
    line-height: 1.5 !important;
}

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 15px !important;
    padding: 12px 14px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--nav) !important;
    box-shadow: 0 0 0 2px rgba(79,156,249,0.15) !important;
}
.stTextArea label, .stTextInput label, .stFileUploader label {
    color: var(--muted) !important;
    font-size: 11px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] { padding: 0 !important; }
.stSlider label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: var(--muted) !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 20px 24px !important;
}
[data-testid="metric-container"] label {
    color: var(--muted) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Fraunces', serif !important;
    font-size: 38px !important;
    font-weight: 300 !important;
    color: var(--text) !important;
}

/* ── Progress bar ── */
.stProgress > div > div { border-radius: 2px !important; }
.stProgress > div {
    background: var(--border) !important;
    border-radius: 2px !important;
    height: 3px !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-size: 15px !important;
    min-height: 44px !important;
}
.stSelectbox label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: var(--muted) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
}

/* ── DataFrame ── */
[data-testid="stDataFrame"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--border2) !important;
    border-radius: 8px !important;
}

/* ── Alerts / toast ── */
.stAlert {
    border-radius: 8px !important;
    border: none !important;
    font-size: 14px !important;
}

/* ── Radio answer cards ── */
.stRadio > div {
    gap: 0 !important;
    flex-direction: column !important;
}
.stRadio > div > label {
    background: #161b27 !important;
    border: 1.5px solid #252e42 !important;
    border-radius: 10px !important;
    padding: 16px 20px !important;
    margin: 5px 0 !important;
    cursor: pointer !important;
    transition: border-color 0.1s, background 0.1s !important;
    align-items: flex-start !important;
    min-height: 52px !important;
}
.stRadio > div > label:hover {
    border-color: #4f9cf9 !important;
    background: #1e2535 !important;
}
.stRadio > div > label[data-checked="true"],
.stRadio > div > label:has(input:checked) {
    border-color: #4f9cf9 !important;
    background: #1a2a40 !important;
}
.stRadio > div > label > div:first-child {
    margin-top: 4px !important;
}
.stRadio > div > label p {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 15px !important;
    line-height: 1.5 !important;
    color: #e8edf5 !important;
    margin: 0 !important;
}
/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }

hr { border-color: var(--border) !important; margin: 28px 0 !important; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar toggle state ─────────────────────────────────────────────────────
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = False

# ── Sidebar JS controller ─────────────────────────────────────────────────────
sidebar_open = st.session_state.sidebar_visible
_sb_css = """
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] {
        width: 260px !important;
        min-width: 260px !important;
        transform: none !important;
        visibility: visible !important;
    }
""" if sidebar_open else """
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] {
        width: 0px !important;
        min-width: 0px !important;
        transform: translateX(-260px) !important;
        visibility: hidden !important;
    }
"""
st.markdown(f"<style>{_sb_css}</style>", unsafe_allow_html=True)

st.markdown("""
<script>
(function hideSteamControls() {
    function run() {
        ['[data-testid="stSidebarCollapseButton"]',
         '[data-testid="collapsedControl"]',
         'button[kind="header"]'].forEach(function(sel) {
            document.querySelectorAll(sel).forEach(function(el) {
                el.style.display = 'none';
            });
        });
    }
    run(); setTimeout(run, 400); setTimeout(run, 1000);
    new MutationObserver(run).observe(document.body, {childList:true, subtree:true});
})();
</script>
""", unsafe_allow_html=True)

# ── Toggle button (top of main content) ───────────────────────────────────────
toggle_label = "☰  Menu" if not st.session_state.sidebar_visible else "✕  Close"
st.markdown("""<style>
button[data-testid="baseButton-secondary"][kind="secondary"]:first-of-type {
    background: transparent !important;
    border: 1px solid #252e42 !important;
    color: #6b7a99 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    min-height: 38px !important;
    margin-bottom: 4px !important;
}
</style>""", unsafe_allow_html=True)
if st.button(toggle_label, key="sidebar_toggle"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()

# ── Topic colours ─────────────────────────────────────────────────────────────
TOPICS = {
    "Physiology":                   {"colour": "#2dd4bf", "emoji": ""},
    "Pharmacology":                 {"colour": "#a78bfa", "emoji": ""},
    "Physics & Clinical Measurement": {"colour": "#38bdf8", "emoji": ""},
    "Clinical Anaesthesia":         {"colour": "#fb923c", "emoji": ""},
}

# ── Topic → suggested flashcard decks mapping ────────────────────────────────
TOPIC_DECK_SUGGESTIONS = {
    "Physiology": [
        ("phy_resp",  "Respiratory Physiology"),
        ("phy_cvs",   "Cardiovascular Physiology"),
        ("phy_neuro", "Neurophysiology & Pain"),
        ("phy_renal", "Renal & Acid-Base"),
        ("phy_gi",    "Hepatic, GI & Metabolic"),
        ("phy_haem",  "Haematology & Immunology"),
        ("phy_endo",  "Endocrine & Obstetric Physiology"),
    ],
    "Pharmacology": [
        ("ph_inh",    "Inhalational Agents"),
        ("ph_iv",     "IV Induction Agents & Sedatives"),
        ("ph_opioid", "Opioids & Analgesics"),
        ("ph_nmb",    "NMBs & Reversal"),
        ("ph_la",     "Local Anaesthetics"),
        ("ph_cvd",    "Cardiovascular Drugs"),
        ("ph_other",  "Antiemetics, Antacids & Other"),
    ],
    "Physics & Clinical Measurement": [
        ("phx_elec",  "Electricity, Safety & Equipment"),
        ("phx_gas",   "Gas Laws & Vaporisers"),
        ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
        ("phx_resp",  "Respiratory Mechanics & Spirometry"),
        ("phx_stats", "Statistics & Clinical Trials"),
    ],
    "Clinical Anaesthesia": [
        ("ca_airway",   "Airway Anatomy & Management"),
        ("ca_regional", "Regional Anatomy & Blocks"),
        ("ca_preop",    "Preoperative Assessment"),
        ("ca_emerg",    "Perioperative Emergencies"),
        ("ca_obs",      "Obstetric Anaesthesia"),
        ("ca_paeds",    "Paediatric Anaesthesia"),
    ],
}

# ── Question → subtopic/deck mapping ────────────────────────────────────────
# Each entry: question_id → (deck_id, subtopic display name)
Q_SUBTOPICS = {
    # ── Physiology ──────────────────────────────────────────────────────────
    "phy001": ("phy_resp",   "Respiratory Physiology"),
    "phy002": ("phy_resp",   "Respiratory Physiology"),
    "phy003": ("phy_cvs",    "Cardiovascular Physiology"),
    "phy004": ("phy_renal",  "Renal & Acid-Base"),
    "phy005": ("phy_cvs",    "Cardiovascular Physiology"),
    "phy006": ("phy_cvs",    "Cardiovascular Physiology"),
    "phy007": ("phy_cvs",    "Cardiovascular Physiology"),
    "phy008": ("phy_cvs",    "Cardiovascular Physiology"),
    "phy009": ("phy_renal",  "Renal & Acid-Base"),
    "phy010": ("phy_resp",   "Respiratory Physiology"),
    "phy011": ("phy_resp",   "Respiratory Physiology"),
    "phy012": ("phy_neuro",  "Neurophysiology & Pain"),
    "phy013": ("phy_renal",  "Renal & Acid-Base"),
    "phy014": ("phy_endo",   "Endocrine & Obstetric Physiology"),
    "phy015": ("phy_renal",  "Renal & Acid-Base"),
    "phy016": ("phy_resp",   "Respiratory Physiology"),
    "phy017": ("phy_cvs",    "Cardiovascular Physiology"),
    "phy018": ("phy_haem",   "Haematology & Immunology"),
    "phy019": ("phy_resp",   "Respiratory Physiology"),
    "phy020": ("phy_resp",   "Respiratory Physiology"),
    "phy021": ("phy_renal",  "Renal & Acid-Base"),
    "phy022": ("phy_cvs",    "Cardiovascular Physiology"),
    "phy023": ("phy_cvs",    "Cardiovascular Physiology"),
    "phy024": ("phy_resp",   "Respiratory Physiology"),
    "phy025": ("phy_neuro",  "Neurophysiology & Pain"),
    # ── Pharmacology ────────────────────────────────────────────────────────
    "phar001": ("ph_iv",      "IV Induction Agents & Sedatives"),
    "phar002": ("ph_nmb",     "NMBs & Reversal"),
    "phar003": ("ph_opioid",  "Opioids & Analgesics"),
    "phar004": ("ph_iv",      "IV Induction Agents & Sedatives"),
    "phar005": ("ph_inh",     "Inhalational Agents"),
    "phar006": ("ph_iv",      "IV Induction Agents & Sedatives"),
    "phar007": ("ph_opioid",  "Opioids & Analgesics"),
    "phar008": ("ph_nmb",     "NMBs & Reversal"),
    "phar009": ("ph_iv",      "IV Induction Agents & Sedatives"),
    "phar010": ("ph_iv",      "IV Induction Agents & Sedatives"),
    "phar011": ("ph_nmb",     "NMBs & Reversal"),
    "phar012": ("ph_inh",     "Inhalational Agents"),
    "phar013": ("ph_inh",     "Inhalational Agents"),
    "phar014": ("ph_opioid",  "Opioids & Analgesics"),
    "phar015": ("ph_la",      "Local Anaesthetics"),
    "phar016": ("ph_nmb",     "NMBs & Reversal"),
    "phar017": ("ph_opioid",  "Opioids & Analgesics"),
    "phar018": ("ph_iv",      "IV Induction Agents & Sedatives"),
    "phar019": ("ph_opioid",  "Opioids & Analgesics"),
    "phar020": ("ph_inh",     "Inhalational Agents"),
    "phar021": ("ph_other",   "Antiemetics, Antacids & Other"),
    "phar022": ("ph_other",   "Antiemetics, Antacids & Other"),
    "phar023": ("ph_inh",     "Inhalational Agents"),
    "phar024": ("ph_cvd",     "Cardiovascular Drugs"),
    "phar025": ("ph_other",   "Antiemetics, Antacids & Other"),
    # ── Physics & Clinical Measurement ──────────────────────────────────────
    "phys001": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys002": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys003": ("phx_gas",   "Gas Laws & Vaporisers"),
    "phys004": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys005": ("phx_gas",   "Gas Laws & Vaporisers"),
    "phys006": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys007": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys008": ("phx_elec",  "Electricity, Safety & Equipment"),
    "phys009": ("phx_gas",   "Gas Laws & Vaporisers"),
    "phys010": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys011": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys012": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys013": ("phx_gas",   "Gas Laws & Vaporisers"),
    "phys014": ("phx_gas",   "Gas Laws & Vaporisers"),
    "phys015": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys016": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys017": ("phx_elec",  "Electricity, Safety & Equipment"),
    "phys018": ("phx_gas",   "Gas Laws & Vaporisers"),
    "phys019": ("phx_elec",  "Electricity, Safety & Equipment"),
    "phys020": ("phx_resp",  "Respiratory Mechanics & Spirometry"),
    "phys021": ("phx_stats", "Statistics & Clinical Trials"),
    "phys022": ("phx_elec",  "Electricity, Safety & Equipment"),
    "phys023": ("phx_stats", "Statistics & Clinical Trials"),
    "phys024": ("phx_mon",   "Monitoring (CO, Neuro, Temp)"),
    "phys025": ("phx_resp",  "Respiratory Mechanics & Spirometry"),
    # ── Clinical Anaesthesia ─────────────────────────────────────────────────
    "clin001": ("ca_preop",    "Preoperative Assessment"),
    "clin002": ("ca_airway",   "Airway Anatomy & Management"),
    "clin003": ("ca_regional", "Regional Anatomy & Blocks"),
    "clin004": ("ca_obs",      "Obstetric Anaesthesia"),
    "clin005": ("ca_emerg",    "Perioperative Emergencies"),
    "clin006": ("ca_preop",    "Preoperative Assessment"),
    "clin007": ("ca_airway",   "Airway Anatomy & Management"),
    "clin008": ("ca_emerg",    "Perioperative Emergencies"),
    "clin009": ("ca_regional", "Regional Anatomy & Blocks"),
    "clin010": ("ca_airway",   "Airway Anatomy & Management"),
    "clin011": ("ca_emerg",    "Perioperative Emergencies"),
    "clin012": ("ca_emerg",    "Perioperative Emergencies"),
    "clin013": ("ca_regional", "Regional Anatomy & Blocks"),
    "clin014": ("ca_emerg",    "Perioperative Emergencies"),
    "clin015": ("ca_preop",    "Preoperative Assessment"),
    "clin016": ("ca_emerg",    "Perioperative Emergencies"),
    "clin017": ("ca_regional", "Regional Anatomy & Blocks"),
    "clin018": ("ca_airway",   "Airway Anatomy & Management"),
    "clin019": ("ca_obs",      "Obstetric Anaesthesia"),
    "clin020": ("ca_airway",   "Airway Anatomy & Management"),
    "clin021": ("ca_preop",    "Preoperative Assessment"),
    "clin022": ("ca_regional", "Regional Anatomy & Blocks"),
    "clin023": ("ca_emerg",    "Perioperative Emergencies"),
    "clin024": ("ca_regional", "Regional Anatomy & Blocks"),
    "clin025": ("ca_obs",      "Obstetric Anaesthesia"),
}

# ── Question diagrams (SVG, dark-themed, generated at module load) ─────────────
Q_IMAGES = {
    'phy001': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 230" style="width:100%;max-width:420px;background:#161b27;border-radius:8px;display:block;margin:0 auto 16px;"><line x1="52" y1="20.0" x2="404" y2="20.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="63.5" x2="404" y2="63.5" stroke="#252e42" stroke-width="1"/><line x1="52" y1="107.0" x2="404" y2="107.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="150.5" x2="404" y2="150.5" stroke="#252e42" stroke-width="1"/><line x1="52" y1="194.0" x2="404" y2="194.0" stroke="#252e42" stroke-width="1"/><line x1="52.0" y1="20" x2="52.0" y2="194" stroke="#252e42" stroke-width="1"/><line x1="122.4" y1="20" x2="122.4" y2="194" stroke="#252e42" stroke-width="1"/><line x1="192.8" y1="20" x2="192.8" y2="194" stroke="#252e42" stroke-width="1"/><line x1="263.2" y1="20" x2="263.2" y2="194" stroke="#252e42" stroke-width="1"/><line x1="333.6" y1="20" x2="333.6" y2="194" stroke="#252e42" stroke-width="1"/><line x1="404.0" y1="20" x2="404.0" y2="194" stroke="#252e42" stroke-width="1"/><line x1="52" y1="20" x2="52" y2="194" stroke="#6b7a99" stroke-width="1.5"/><line x1="52" y1="194" x2="404" y2="194" stroke="#6b7a99" stroke-width="1.5"/><polyline points="52.0,194.0 54.6,194.0 57.3,193.9 59.9,193.8 62.6,193.5 65.2,193.1 67.9,192.5 70.5,191.8 73.2,190.8 75.8,189.7 78.5,188.3 81.1,186.7 83.8,184.8 86.4,182.8 89.1,180.5 91.7,178.0 94.3,175.2 97.0,172.3 99.6,169.2 102.3,166.0 104.9,162.5 107.6,159.0 110.2,155.4 112.9,151.6 115.5,147.8 118.2,144.0 120.8,140.2 123.5,136.3 126.1,132.4 128.8,128.6 131.4,124.8 134.0,121.1 136.7,117.5 139.3,113.9 142.0,110.4 144.6,107.0 147.3,103.7 149.9,100.5 152.6,97.4 155.2,94.4 157.9,91.5 160.5,88.7 163.2,86.0 165.8,83.4 168.5,80.9 171.1,78.6 173.7,76.3 176.4,74.1 179.0,72.0 181.7,70.0 184.3,68.1 187.0,66.2 189.6,64.5 192.3,62.8 194.9,61.2 197.6,59.6 200.2,58.2 202.9,56.8 205.5,55.4 208.2,54.1 210.8,52.9 213.4,51.7 216.1,50.6 218.7,49.5 221.4,48.5 224.0,47.5 226.7,46.6 229.3,45.7 232.0,44.8 234.6,44.0 237.3,43.2 239.9,42.4 242.6,41.7 245.2,41.0 247.8,40.4 250.5,39.7 253.1,39.1 255.8,38.5 258.4,37.9 261.1,37.4 263.7,36.9 266.4,36.4 269.0,35.9 271.7,35.4 274.3,35.0 277.0,34.5 279.6,34.1 282.3,33.7 284.9,33.3 287.5,33.0 290.2,32.6 292.8,32.3 295.5,31.9 298.1,31.6 300.8,31.3 303.4,31.0 306.1,30.7 308.7,30.4 311.4,30.2 314.0,29.9 316.7,29.7 319.3,29.4 322.0,29.2 324.6,29.0 327.2,28.7 329.9,28.5 332.5,28.3 335.2,28.1 337.8,27.9 340.5,27.7 343.1,27.6 345.8,27.4 348.4,27.2 351.1,27.1 353.7,26.9 356.4,26.7 359.0,26.6 361.7,26.4 364.3,26.3 366.9,26.2 369.6,26.0 372.2,25.9 374.9,25.8 377.5,25.7 380.2,25.5 382.8,25.4 385.5,25.3 388.1,25.2 390.8,25.1 393.4,25.0 396.1,24.9 398.7,24.8 401.4,24.7 404.0,24.6" fill="none" stroke="#e8edf5" stroke-width="2.5"/><polyline points="52.0,194.0 54.6,194.0 57.3,194.0 59.9,193.9 62.6,193.7 65.2,193.5 67.9,193.2 70.5,192.9 73.2,192.4 75.8,191.8 78.5,191.1 81.1,190.2 83.8,189.2 86.4,188.1 89.1,186.9 91.7,185.5 94.3,184.0 97.0,182.3 99.6,180.5 102.3,178.5 104.9,176.5 107.6,174.3 110.2,172.0 112.9,169.6 115.5,167.1 118.2,164.5 120.8,161.8 123.5,159.0 126.1,156.2 128.8,153.3 131.4,150.4 134.0,147.4 136.7,144.4 139.3,141.4 142.0,138.4 144.6,135.4 147.3,132.4 149.9,129.5 152.6,126.5 155.2,123.6 157.9,120.7 160.5,117.9 163.2,115.1 165.8,112.3 168.5,109.6 171.1,107.0 173.7,104.4 176.4,101.9 179.0,99.4 181.7,97.0 184.3,94.7 187.0,92.4 189.6,90.2 192.3,88.1 194.9,86.0 197.6,84.0 200.2,82.0 202.9,80.1 205.5,78.3 208.2,76.5 210.8,74.8 213.4,73.2 216.1,71.5 218.7,70.0 221.4,68.5 224.0,67.0 226.7,65.6 229.3,64.3 232.0,63.0 234.6,61.7 237.3,60.5 239.9,59.3 242.6,58.2 245.2,57.1 247.8,56.0 250.5,55.0 253.1,54.0 255.8,53.1 258.4,52.1 261.1,51.2 263.7,50.4 266.4,49.5 269.0,48.7 271.7,48.0 274.3,47.2 277.0,46.5 279.6,45.8 282.3,45.1 284.9,44.5 287.5,43.8 290.2,43.2 292.8,42.6 295.5,42.0 298.1,41.5 300.8,40.9 303.4,40.4 306.1,39.9 308.7,39.4 311.4,39.0 314.0,38.5 316.7,38.1 319.3,37.6 322.0,37.2 324.6,36.8 327.2,36.4 329.9,36.0 332.5,35.7 335.2,35.3 337.8,35.0 340.5,34.6 343.1,34.3 345.8,34.0 348.4,33.7 351.1,33.4 353.7,33.1 356.4,32.8 359.0,32.5 361.7,32.3 364.3,32.0 366.9,31.7 369.6,31.5 372.2,31.3 374.9,31.0 377.5,30.8 380.2,30.6 382.8,30.4 385.5,30.2 388.1,30.0 390.8,29.8 393.4,29.6 396.1,29.4 398.7,29.2 401.4,29.0 404.0,28.9" fill="none" stroke="#f87171" stroke-width="2.5"/><polyline points="52.0,194.0 54.6,194.0 57.3,193.8 59.9,193.5 62.6,193.0 65.2,192.2 67.9,191.1 70.5,189.6 73.2,187.7 75.8,185.5 78.5,182.9 81.1,179.8 83.8,176.5 86.4,172.8 89.1,168.7 91.7,164.5 94.3,159.9 97.0,155.2 99.6,150.4 102.3,145.4 104.9,140.4 107.6,135.4 110.2,130.5 112.9,125.5 115.5,120.7 118.2,116.0 120.8,111.4 123.5,107.0 126.1,102.7 128.8,98.6 131.4,94.7 134.0,91.0 136.7,87.4 139.3,84.0 142.0,80.8 144.6,77.7 147.3,74.8 149.9,72.1 152.6,69.5 155.2,67.0 157.9,64.7 160.5,62.6 163.2,60.5 165.8,58.6 168.5,56.7 171.1,55.0 173.7,53.4 176.4,51.8 179.0,50.4 181.7,49.0 184.3,47.7 187.0,46.5 189.6,45.3 192.3,44.2 194.9,43.2 197.6,42.2 200.2,41.3 202.9,40.4 205.5,39.6 208.2,38.8 210.8,38.1 213.4,37.3 216.1,36.7 218.7,36.0 221.4,35.4 224.0,34.8 226.7,34.3 229.3,33.8 232.0,33.3 234.6,32.8 237.3,32.3 239.9,31.9 242.6,31.5 245.2,31.1 247.8,30.7 250.5,30.4 253.1,30.0 255.8,29.7 258.4,29.4 261.1,29.1 263.7,28.8 266.4,28.5 269.0,28.3 271.7,28.0 274.3,27.8 277.0,27.5 279.6,27.3 282.3,27.1 284.9,26.9 287.5,26.7 290.2,26.5 292.8,26.3 295.5,26.1 298.1,26.0 300.8,25.8 303.4,25.6 306.1,25.5 308.7,25.3 311.4,25.2 314.0,25.1 316.7,24.9 319.3,24.8 322.0,24.7 324.6,24.6 327.2,24.4 329.9,24.3 332.5,24.2 335.2,24.1 337.8,24.0 340.5,23.9 343.1,23.8 345.8,23.7 348.4,23.7 351.1,23.6 353.7,23.5 356.4,23.4 359.0,23.3 361.7,23.3 364.3,23.2 366.9,23.1 369.6,23.0 372.2,23.0 374.9,22.9 377.5,22.9 380.2,22.8 382.8,22.7 385.5,22.7 388.1,22.6 390.8,22.6 393.4,22.5 396.1,22.5 398.7,22.4 401.4,22.4 404.0,22.3" fill="none" stroke="#60a5fa" stroke-width="2.5"/><line x1="144.6" y1="20" x2="144.6" y2="194" stroke="#e8edf5" stroke-width="1" stroke-dasharray="3,3"/><line x1="52" y1="107.0" x2="404" y2="107.0" stroke="#e8edf5" stroke-width="1" stroke-dasharray="3,3"/><text x="52.0" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">0</text><text x="104.93233082706766" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">2</text><text x="157.86466165413532" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">4</text><text x="210.796992481203" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">6</text><text x="263.72932330827064" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">8</text><text x="316.6616541353383" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">10</text><text x="46" y="197.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">0</text><text x="46" y="153.5" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">25</text><text x="46" y="110.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">50</text><text x="46" y="66.5" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">75</text><text x="46" y="23.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">100</text><text x="210" y="228" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">PO₂ (kPa)</text><text x="12" y="115" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" transform="rotate(-90,12,115)">SaO₂ (%)</text><rect x="274" y="20" width="120" height="62" fill="#0e1117" rx="4" opacity="0.9"/><line x1="282" y1="32" x2="300" y2="32" stroke="#e8edf5" stroke-width="2.5"/><text x="304" y="35" fill="#e8edf5" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Normal</text><line x1="282" y1="48" x2="300" y2="48" stroke="#f87171" stroke-width="2.5"/><text x="304" y="51" fill="#f87171" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Right shift ↑CO₂</text><line x1="282" y1="64" x2="300" y2="64" stroke="#60a5fa" stroke-width="2.5"/><text x="304" y="67" fill="#60a5fa" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Left shift ↓CO₂</text><text x="342" y="78" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="middle" font-weight="normal">P50 = 3.5 kPa</text></svg>''',
    'phy018': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 230" style="width:100%;max-width:420px;background:#161b27;border-radius:8px;display:block;margin:0 auto 16px;"><line x1="52" y1="20.0" x2="404" y2="20.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="63.5" x2="404" y2="63.5" stroke="#252e42" stroke-width="1"/><line x1="52" y1="107.0" x2="404" y2="107.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="150.5" x2="404" y2="150.5" stroke="#252e42" stroke-width="1"/><line x1="52" y1="194.0" x2="404" y2="194.0" stroke="#252e42" stroke-width="1"/><line x1="52.0" y1="20" x2="52.0" y2="194" stroke="#252e42" stroke-width="1"/><line x1="122.4" y1="20" x2="122.4" y2="194" stroke="#252e42" stroke-width="1"/><line x1="192.8" y1="20" x2="192.8" y2="194" stroke="#252e42" stroke-width="1"/><line x1="263.2" y1="20" x2="263.2" y2="194" stroke="#252e42" stroke-width="1"/><line x1="333.6" y1="20" x2="333.6" y2="194" stroke="#252e42" stroke-width="1"/><line x1="404.0" y1="20" x2="404.0" y2="194" stroke="#252e42" stroke-width="1"/><line x1="52" y1="20" x2="52" y2="194" stroke="#6b7a99" stroke-width="1.5"/><line x1="52" y1="194" x2="404" y2="194" stroke="#6b7a99" stroke-width="1.5"/><polyline points="52.0,194.0 54.6,194.0 57.3,193.9 59.9,193.8 62.6,193.5 65.2,193.1 67.9,192.5 70.5,191.8 73.2,190.8 75.8,189.7 78.5,188.3 81.1,186.7 83.8,184.8 86.4,182.8 89.1,180.5 91.7,178.0 94.3,175.2 97.0,172.3 99.6,169.2 102.3,166.0 104.9,162.5 107.6,159.0 110.2,155.4 112.9,151.6 115.5,147.8 118.2,144.0 120.8,140.2 123.5,136.3 126.1,132.4 128.8,128.6 131.4,124.8 134.0,121.1 136.7,117.5 139.3,113.9 142.0,110.4 144.6,107.0 147.3,103.7 149.9,100.5 152.6,97.4 155.2,94.4 157.9,91.5 160.5,88.7 163.2,86.0 165.8,83.4 168.5,80.9 171.1,78.6 173.7,76.3 176.4,74.1 179.0,72.0 181.7,70.0 184.3,68.1 187.0,66.2 189.6,64.5 192.3,62.8 194.9,61.2 197.6,59.6 200.2,58.2 202.9,56.8 205.5,55.4 208.2,54.1 210.8,52.9 213.4,51.7 216.1,50.6 218.7,49.5 221.4,48.5 224.0,47.5 226.7,46.6 229.3,45.7 232.0,44.8 234.6,44.0 237.3,43.2 239.9,42.4 242.6,41.7 245.2,41.0 247.8,40.4 250.5,39.7 253.1,39.1 255.8,38.5 258.4,37.9 261.1,37.4 263.7,36.9 266.4,36.4 269.0,35.9 271.7,35.4 274.3,35.0 277.0,34.5 279.6,34.1 282.3,33.7 284.9,33.3 287.5,33.0 290.2,32.6 292.8,32.3 295.5,31.9 298.1,31.6 300.8,31.3 303.4,31.0 306.1,30.7 308.7,30.4 311.4,30.2 314.0,29.9 316.7,29.7 319.3,29.4 322.0,29.2 324.6,29.0 327.2,28.7 329.9,28.5 332.5,28.3 335.2,28.1 337.8,27.9 340.5,27.7 343.1,27.6 345.8,27.4 348.4,27.2 351.1,27.1 353.7,26.9 356.4,26.7 359.0,26.6 361.7,26.4 364.3,26.3 366.9,26.2 369.6,26.0 372.2,25.9 374.9,25.8 377.5,25.7 380.2,25.5 382.8,25.4 385.5,25.3 388.1,25.2 390.8,25.1 393.4,25.0 396.1,24.9 398.7,24.8 401.4,24.7 404.0,24.6" fill="none" stroke="#e8edf5" stroke-width="2.5"/><polyline points="52.0,194.0 54.6,194.0 57.3,194.0 59.9,193.9 62.6,193.7 65.2,193.5 67.9,193.2 70.5,192.9 73.2,192.4 75.8,191.8 78.5,191.1 81.1,190.2 83.8,189.2 86.4,188.1 89.1,186.9 91.7,185.5 94.3,184.0 97.0,182.3 99.6,180.5 102.3,178.5 104.9,176.5 107.6,174.3 110.2,172.0 112.9,169.6 115.5,167.1 118.2,164.5 120.8,161.8 123.5,159.0 126.1,156.2 128.8,153.3 131.4,150.4 134.0,147.4 136.7,144.4 139.3,141.4 142.0,138.4 144.6,135.4 147.3,132.4 149.9,129.5 152.6,126.5 155.2,123.6 157.9,120.7 160.5,117.9 163.2,115.1 165.8,112.3 168.5,109.6 171.1,107.0 173.7,104.4 176.4,101.9 179.0,99.4 181.7,97.0 184.3,94.7 187.0,92.4 189.6,90.2 192.3,88.1 194.9,86.0 197.6,84.0 200.2,82.0 202.9,80.1 205.5,78.3 208.2,76.5 210.8,74.8 213.4,73.2 216.1,71.5 218.7,70.0 221.4,68.5 224.0,67.0 226.7,65.6 229.3,64.3 232.0,63.0 234.6,61.7 237.3,60.5 239.9,59.3 242.6,58.2 245.2,57.1 247.8,56.0 250.5,55.0 253.1,54.0 255.8,53.1 258.4,52.1 261.1,51.2 263.7,50.4 266.4,49.5 269.0,48.7 271.7,48.0 274.3,47.2 277.0,46.5 279.6,45.8 282.3,45.1 284.9,44.5 287.5,43.8 290.2,43.2 292.8,42.6 295.5,42.0 298.1,41.5 300.8,40.9 303.4,40.4 306.1,39.9 308.7,39.4 311.4,39.0 314.0,38.5 316.7,38.1 319.3,37.6 322.0,37.2 324.6,36.8 327.2,36.4 329.9,36.0 332.5,35.7 335.2,35.3 337.8,35.0 340.5,34.6 343.1,34.3 345.8,34.0 348.4,33.7 351.1,33.4 353.7,33.1 356.4,32.8 359.0,32.5 361.7,32.3 364.3,32.0 366.9,31.7 369.6,31.5 372.2,31.3 374.9,31.0 377.5,30.8 380.2,30.6 382.8,30.4 385.5,30.2 388.1,30.0 390.8,29.8 393.4,29.6 396.1,29.4 398.7,29.2 401.4,29.0 404.0,28.9" fill="none" stroke="#f87171" stroke-width="2.5"/><polyline points="52.0,194.0 54.6,194.0 57.3,193.8 59.9,193.5 62.6,193.0 65.2,192.2 67.9,191.1 70.5,189.6 73.2,187.7 75.8,185.5 78.5,182.9 81.1,179.8 83.8,176.5 86.4,172.8 89.1,168.7 91.7,164.5 94.3,159.9 97.0,155.2 99.6,150.4 102.3,145.4 104.9,140.4 107.6,135.4 110.2,130.5 112.9,125.5 115.5,120.7 118.2,116.0 120.8,111.4 123.5,107.0 126.1,102.7 128.8,98.6 131.4,94.7 134.0,91.0 136.7,87.4 139.3,84.0 142.0,80.8 144.6,77.7 147.3,74.8 149.9,72.1 152.6,69.5 155.2,67.0 157.9,64.7 160.5,62.6 163.2,60.5 165.8,58.6 168.5,56.7 171.1,55.0 173.7,53.4 176.4,51.8 179.0,50.4 181.7,49.0 184.3,47.7 187.0,46.5 189.6,45.3 192.3,44.2 194.9,43.2 197.6,42.2 200.2,41.3 202.9,40.4 205.5,39.6 208.2,38.8 210.8,38.1 213.4,37.3 216.1,36.7 218.7,36.0 221.4,35.4 224.0,34.8 226.7,34.3 229.3,33.8 232.0,33.3 234.6,32.8 237.3,32.3 239.9,31.9 242.6,31.5 245.2,31.1 247.8,30.7 250.5,30.4 253.1,30.0 255.8,29.7 258.4,29.4 261.1,29.1 263.7,28.8 266.4,28.5 269.0,28.3 271.7,28.0 274.3,27.8 277.0,27.5 279.6,27.3 282.3,27.1 284.9,26.9 287.5,26.7 290.2,26.5 292.8,26.3 295.5,26.1 298.1,26.0 300.8,25.8 303.4,25.6 306.1,25.5 308.7,25.3 311.4,25.2 314.0,25.1 316.7,24.9 319.3,24.8 322.0,24.7 324.6,24.6 327.2,24.4 329.9,24.3 332.5,24.2 335.2,24.1 337.8,24.0 340.5,23.9 343.1,23.8 345.8,23.7 348.4,23.7 351.1,23.6 353.7,23.5 356.4,23.4 359.0,23.3 361.7,23.3 364.3,23.2 366.9,23.1 369.6,23.0 372.2,23.0 374.9,22.9 377.5,22.9 380.2,22.8 382.8,22.7 385.5,22.7 388.1,22.6 390.8,22.6 393.4,22.5 396.1,22.5 398.7,22.4 401.4,22.4 404.0,22.3" fill="none" stroke="#60a5fa" stroke-width="2.5"/><line x1="144.6" y1="20" x2="144.6" y2="194" stroke="#e8edf5" stroke-width="1" stroke-dasharray="3,3"/><line x1="52" y1="107.0" x2="404" y2="107.0" stroke="#e8edf5" stroke-width="1" stroke-dasharray="3,3"/><text x="52.0" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">0</text><text x="104.93233082706766" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">2</text><text x="157.86466165413532" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">4</text><text x="210.796992481203" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">6</text><text x="263.72932330827064" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">8</text><text x="316.6616541353383" y="208" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">10</text><text x="46" y="197.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">0</text><text x="46" y="153.5" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">25</text><text x="46" y="110.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">50</text><text x="46" y="66.5" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">75</text><text x="46" y="23.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">100</text><text x="210" y="228" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">PO₂ (kPa)</text><text x="12" y="115" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" transform="rotate(-90,12,115)">SaO₂ (%)</text><rect x="274" y="20" width="120" height="62" fill="#0e1117" rx="4" opacity="0.9"/><line x1="282" y1="32" x2="300" y2="32" stroke="#e8edf5" stroke-width="2.5"/><text x="304" y="35" fill="#e8edf5" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Normal</text><line x1="282" y1="48" x2="300" y2="48" stroke="#f87171" stroke-width="2.5"/><text x="304" y="51" fill="#f87171" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Right shift ↑CO₂</text><line x1="282" y1="64" x2="300" y2="64" stroke="#60a5fa" stroke-width="2.5"/><text x="304" y="67" fill="#60a5fa" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Left shift ↓CO₂</text><text x="342" y="78" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="middle" font-weight="normal">P50 = 3.5 kPa</text></svg>''',
    'phy003': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 220" style="width:100%;max-width:420px;background:#161b27;border-radius:8px;display:block;margin:0 auto 16px;"><line x1="52" y1="20.0" x2="400" y2="20.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="61.0" x2="400" y2="61.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="102.0" x2="400" y2="102.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="143.0" x2="400" y2="143.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="184.0" x2="400" y2="184.0" stroke="#252e42" stroke-width="1"/><line x1="52.0" y1="20" x2="52.0" y2="184" stroke="#252e42" stroke-width="1"/><line x1="121.6" y1="20" x2="121.6" y2="184" stroke="#252e42" stroke-width="1"/><line x1="191.2" y1="20" x2="191.2" y2="184" stroke="#252e42" stroke-width="1"/><line x1="260.8" y1="20" x2="260.8" y2="184" stroke="#252e42" stroke-width="1"/><line x1="330.4" y1="20" x2="330.4" y2="184" stroke="#252e42" stroke-width="1"/><line x1="400.0" y1="20" x2="400.0" y2="184" stroke="#252e42" stroke-width="1"/><line x1="52" y1="20" x2="52" y2="184" stroke="#6b7a99" stroke-width="1.5"/><line x1="52" y1="184" x2="400" y2="184" stroke="#6b7a99" stroke-width="1.5"/><polyline points="52.0,184.0 56.4,184.0 58.1,32.6 69.4,45.2 226.0,57.8 313.0,64.2 356.5,95.7 382.6,177.7 400.0,184.0" fill="none" stroke="#2dd4bf" stroke-width="2.5" stroke-linejoin="round"/><text x="57.22" y="22.523076923076914" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="bold">0</text><text x="65.05" y="35.13846153846154" fill="#a78bfa" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="bold">1</text><text x="208.6" y="47.75384615384615" fill="#38bdf8" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="bold">2</text><text x="365.2" y="76.76923076923077" fill="#f87171" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="bold">3</text><text x="65.05" y="181.47692307692307" fill="#4ade80" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="bold">4</text><text x="46" y="187.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">-90</text><text x="46" y="149.15384615384613" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">-60</text><text x="46" y="111.3076923076923" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">-30</text><text x="46" y="73.46153846153847" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">0</text><text x="46" y="35.615384615384606" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">30</text><text x="52.0" y="198" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">0</text><text x="139.0" y="198" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">100</text><text x="226.0" y="198" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">200</text><text x="313.0" y="198" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">300</text><text x="400.0" y="198" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">400</text><text x="210" y="218" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">Time (ms)</text><text x="12" y="110" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" transform="rotate(-90,12,110)">mV</text><text x="58.09" y="14.953846153846172" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="middle" font-weight="normal">Na⁺ in</text><text x="226.0" y="40.184615384615384" fill="#38bdf8" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="middle" font-weight="normal">Ca²⁺ in</text><text x="369.55" y="114.61538461538461" fill="#f87171" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="middle" font-weight="normal">K⁺ out</text></svg>''',
    'phy016': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 220" style="width:100%;max-width:420px;background:#161b27;border-radius:8px;display:block;margin:0 auto 16px;"><line x1="56" y1="16.0" x2="400" y2="16.0" stroke="#252e42" stroke-width="1" stroke-dasharray="3,3"/><line x1="56" y1="57.1" x2="400" y2="57.1" stroke="#252e42" stroke-width="1" stroke-dasharray="3,3"/><line x1="56" y1="83.5" x2="400" y2="83.5" stroke="#252e42" stroke-width="1" stroke-dasharray="3,3"/><line x1="56" y1="127.5" x2="400" y2="127.5" stroke="#252e42" stroke-width="1" stroke-dasharray="3,3"/><rect x="56" y="16.0" width="264" height="26.4" fill="#2dd4bf22"/><rect x="56" y="42.4" width="264" height="14.7" fill="#e8edf522"/><rect x="56" y="57.1" width="264" height="26.4" fill="#38bdf822"/><rect x="56" y="83.5" width="264" height="44.0" fill="#a78bfa22"/><polyline points="56.0,57.1 77.1,71.7 98.2,57.1 108.8,57.1 129.9,71.7 151.0,57.1 161.6,57.1 182.7,71.7 203.8,57.1 214.4,57.1 235.5,16.0 235.5,16.0 277.8,127.5 277.8,127.5 298.9,83.5" fill="none" stroke="#e8edf5" stroke-width="2" stroke-linejoin="round"/><line x1="56" y1="83.5" x2="320" y2="83.5" stroke="#4ade80" stroke-width="1.5" stroke-dasharray="5,3"/><text x="330" y="32.2" fill="#2dd4bf" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="start" font-weight="normal">IRV</text><text x="330" y="52.733333333333334" fill="#e8edf5" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="start" font-weight="normal">TV</text><text x="330" y="73.26666666666667" fill="#38bdf8" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="start" font-weight="normal">ERV</text><text x="330" y="108.46666666666667" fill="#a78bfa" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="start" font-weight="normal">RV</text><text x="330" y="102.6" fill="#4ade80" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="start" font-weight="normal">FRC →</text><text x="14" y="110" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" transform="rotate(-90,14,110)">Volume (mL)</text><text x="188" y="216" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">Spirometry trace</text></svg>''',
    'phy017': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 200" style="width:100%;max-width:420px;background:#161b27;border-radius:8px;display:block;margin:0 auto 16px;"><line x1="52" y1="20.0" x2="404" y2="20.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="57.0" x2="404" y2="57.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="94.0" x2="404" y2="94.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="131.0" x2="404" y2="131.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="168.0" x2="404" y2="168.0" stroke="#252e42" stroke-width="1"/><line x1="52.0" y1="20" x2="52.0" y2="168" stroke="#252e42" stroke-width="1"/><line x1="122.4" y1="20" x2="122.4" y2="168" stroke="#252e42" stroke-width="1"/><line x1="192.8" y1="20" x2="192.8" y2="168" stroke="#252e42" stroke-width="1"/><line x1="263.2" y1="20" x2="263.2" y2="168" stroke="#252e42" stroke-width="1"/><line x1="333.6" y1="20" x2="333.6" y2="168" stroke="#252e42" stroke-width="1"/><line x1="404.0" y1="20" x2="404.0" y2="168" stroke="#252e42" stroke-width="1"/><line x1="52" y1="20" x2="52" y2="168" stroke="#6b7a99" stroke-width="1.5"/><line x1="52" y1="168" x2="404" y2="168" stroke="#6b7a99" stroke-width="1.5"/><polyline points="52.0,151.6 162.0,118.7 166.4,28.2 175.2,28.2 192.8,69.3 210.4,151.6 228.0,151.6" fill="none" stroke="#a78bfa" stroke-width="2.5" stroke-linejoin="round"/><polyline points="228.0,151.6 338.0,118.7 342.4,28.2 351.2,28.2 368.8,69.3 386.4,151.6 404.0,151.6" fill="none" stroke="#a78bfa" stroke-width="2.5" stroke-linejoin="round"/><line x1="52" y1="118.7" x2="404" y2="118.7" stroke="#fbbf24" stroke-width="1" stroke-dasharray="4,3"/><text x="402" y="114.66666666666667" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="end" font-weight="normal">Threshold −40mV</text><text x="107.0" y="131.82222222222222" fill="#4ade80" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="middle" font-weight="normal">Phase 4</text><text x="167.28" y="20.0" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="bold">0</text><text x="201.6" y="61.111111111111114" fill="#f87171" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="bold">3</text><text x="107.0" y="154.84444444444443" fill="#38bdf8" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="middle" font-weight="normal">If (funny) current</text><text x="46" y="171.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">-70</text><text x="46" y="121.66666666666667" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">-40</text><text x="46" y="88.77777777777777" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">-20</text><text x="46" y="55.888888888888886" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">0</text><text x="46" y="23.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">20</text><text x="210" y="198" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">Time (ms)</text><text x="12" y="100" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" transform="rotate(-90,12,100)">mV</text></svg>''',
    'phy022': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 180" style="width:100%;max-width:420px;background:#161b27;border-radius:8px;display:block;margin:0 auto 16px;"><line x1="48" y1="20.0" x2="404" y2="20.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="62.7" x2="404" y2="62.7" stroke="#252e42" stroke-width="1"/><line x1="48" y1="105.3" x2="404" y2="105.3" stroke="#252e42" stroke-width="1"/><line x1="48" y1="148.0" x2="404" y2="148.0" stroke="#252e42" stroke-width="1"/><line x1="48.0" y1="20" x2="48.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="107.3" y1="20" x2="107.3" y2="148" stroke="#252e42" stroke-width="1"/><line x1="166.7" y1="20" x2="166.7" y2="148" stroke="#252e42" stroke-width="1"/><line x1="226.0" y1="20" x2="226.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="285.3" y1="20" x2="285.3" y2="148" stroke="#252e42" stroke-width="1"/><line x1="344.7" y1="20" x2="344.7" y2="148" stroke="#252e42" stroke-width="1"/><line x1="404.0" y1="20" x2="404.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="48" y1="20" x2="48" y2="148" stroke="#6b7a99" stroke-width="1.5"/><line x1="48" y1="148" x2="404" y2="148" stroke="#6b7a99" stroke-width="1.5"/><polyline points="48.0,78.2 56.9,78.2 65.8,49.1 80.0,66.5 87.2,60.7 94.3,72.4 110.3,95.6 128.1,95.6 145.9,54.9 172.6,54.9 186.8,78.2 208.2,78.2 226.0,78.2 226.0,78.2 234.9,78.2 243.8,49.1 258.0,66.5 265.2,60.7 272.3,72.4 288.3,95.6 306.1,95.6 323.9,54.9 350.6,54.9 364.8,78.2 386.2,78.2 404.0,78.2" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linejoin="round"/><text x="65.8" y="45.09090909090909" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="10" text-anchor="middle" font-weight="bold">a</text><text x="243.8" y="45.09090909090909" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="10" text-anchor="middle" font-weight="bold">a</text><text x="87.16" y="56.727272727272734" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="10" text-anchor="middle" font-weight="bold">c</text><text x="265.15999999999997" y="56.727272727272734" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="10" text-anchor="middle" font-weight="bold">c</text><text x="110.3" y="95.12727272727273" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="10" text-anchor="middle" font-weight="bold">x</text><text x="288.3" y="95.12727272727273" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="10" text-anchor="middle" font-weight="bold">x</text><text x="154.8" y="48.58181818181819" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="10" text-anchor="middle" font-weight="bold">v</text><text x="332.8" y="48.58181818181819" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="10" text-anchor="middle" font-weight="bold">v</text><text x="186.84" y="76.50909090909092" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="10" text-anchor="middle" font-weight="bold">y</text><text x="364.84000000000003" y="76.50909090909092" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="10" text-anchor="middle" font-weight="bold">y</text><text x="42" y="139.36363636363637" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">0</text><text x="42" y="81.18181818181819" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">5</text><text x="42" y="23.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">10</text><text x="210" y="178" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">Time →</text><text x="12" y="90" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" transform="rotate(-90,12,90)">cmH₂O</text></svg>''',
    'phys002': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 180" style="width:100%;max-width:420px;background:#161b27;border-radius:8px;display:block;margin:0 auto 16px;"><line x1="48" y1="16.0" x2="404" y2="16.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="60.0" x2="404" y2="60.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="104.0" x2="404" y2="104.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="148.0" x2="404" y2="148.0" stroke="#252e42" stroke-width="1"/><line x1="48.0" y1="16" x2="48.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="107.3" y1="16" x2="107.3" y2="148" stroke="#252e42" stroke-width="1"/><line x1="166.7" y1="16" x2="166.7" y2="148" stroke="#252e42" stroke-width="1"/><line x1="226.0" y1="16" x2="226.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="285.3" y1="16" x2="285.3" y2="148" stroke="#252e42" stroke-width="1"/><line x1="344.7" y1="16" x2="344.7" y2="148" stroke="#252e42" stroke-width="1"/><line x1="404.0" y1="16" x2="404.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="48" y1="16" x2="48" y2="148" stroke="#6b7a99" stroke-width="1.5"/><line x1="48" y1="148" x2="404" y2="148" stroke="#6b7a99" stroke-width="1.5"/><polyline points="48.0,148.0 89.5,148.0 92.5,100.9 101.4,82.0 110.3,68.8 119.2,59.4 128.1,53.7 134.0,148.0 166.7,148.0 166.7,148.0 208.2,148.0 211.2,100.9 220.1,82.0 229.0,68.8 237.9,59.4 246.8,53.7 252.7,148.0 285.3,148.0 285.3,148.0 326.9,148.0 329.8,100.9 338.7,82.0 347.6,68.8 356.5,59.4 365.4,53.7 371.4,148.0 404.0,148.0" fill="none" stroke="#fbbf24" stroke-width="2.5" stroke-linejoin="round"/><text x="42" y="151.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">0</text><text x="42" y="113.28571428571429" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">2</text><text x="42" y="75.57142857142858" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">4</text><text x="42" y="37.85714285714286" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">6</text><text x="42" y="56.714285714285715" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="end" font-weight="normal">5.0</text><line x1="48" y1="53.7" x2="404" y2="53.7" stroke="#6b7a99" stroke-width="1" stroke-dasharray="4,3"/><text x="210" y="178" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">Time →</text><text x="12" y="90" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" transform="rotate(-90,12,90)">EtCO₂ (kPa)</text><text x="210" y="26" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">Obstructive (COPD/bronchospasm)</text></svg>''',
    'phys007': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 180" style="width:100%;max-width:420px;background:#161b27;border-radius:8px;display:block;margin:0 auto 16px;"><line x1="48" y1="20.0" x2="404" y2="20.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="52.0" x2="404" y2="52.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="84.0" x2="404" y2="84.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="116.0" x2="404" y2="116.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="148.0" x2="404" y2="148.0" stroke="#252e42" stroke-width="1"/><line x1="48.0" y1="20" x2="48.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="107.3" y1="20" x2="107.3" y2="148" stroke="#252e42" stroke-width="1"/><line x1="166.7" y1="20" x2="166.7" y2="148" stroke="#252e42" stroke-width="1"/><line x1="226.0" y1="20" x2="226.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="285.3" y1="20" x2="285.3" y2="148" stroke="#252e42" stroke-width="1"/><line x1="344.7" y1="20" x2="344.7" y2="148" stroke="#252e42" stroke-width="1"/><line x1="404.0" y1="20" x2="404.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="48" y1="20" x2="48" y2="148" stroke="#6b7a99" stroke-width="1.5"/><line x1="48" y1="148" x2="404" y2="148" stroke="#6b7a99" stroke-width="1.5"/><polyline points="48.0,123.1 55.1,91.1 61.4,94.7 79.2,108.9 83.6,111.0 101.4,118.1 137.0,123.1" fill="none" stroke="#4ade80" stroke-width="2" stroke-linejoin="round"/><polyline points="163.7,123.1 170.8,91.1 177.0,94.7 194.8,108.9 199.3,111.0 217.1,118.1 252.7,123.1" fill="none" stroke="#4ade80" stroke-width="2" stroke-linejoin="round"/><polyline points="279.4,123.1 286.5,80.4 292.8,94.7 297.2,85.4 306.1,93.2 315.0,96.8 319.5,94.7 332.8,119.6 368.4,123.1" fill="none" stroke="#f87171" stroke-width="2" stroke-linejoin="round"/><text x="42" y="151.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="end" font-weight="normal">40</text><text x="42" y="122.55555555555556" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="end" font-weight="normal">80</text><text x="42" y="94.11111111111111" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="end" font-weight="normal">120</text><text x="42" y="65.66666666666667" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="end" font-weight="normal">160</text><text x="42" y="37.22222222222223" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="end" font-weight="normal">200</text><text x="42" y="23.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="end" font-weight="normal">220</text><text x="210" y="178" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">Time →</text><text x="12" y="90" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" transform="rotate(-90,12,90)">BP (mmHg)</text><rect x="58" y="24" width="160" height="36" fill="#0e1117" rx="4" opacity="0.9"/><line x1="64" y1="34" x2="76" y2="34" stroke="#4ade80" stroke-width="2"/><text x="80" y="37" fill="#4ade80" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Optimal (ζ ≈ 0.64)</text><line x1="64" y1="48" x2="76" y2="48" stroke="#f87171" stroke-width="2"/><text x="80" y="51" fill="#f87171" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Underdamped — systolic overshoot</text></svg>''',
    'phys010': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 180" style="width:100%;max-width:420px;background:#161b27;border-radius:8px;display:block;margin:0 auto 16px;"><line x1="48" y1="16.0" x2="404" y2="16.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="60.0" x2="404" y2="60.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="104.0" x2="404" y2="104.0" stroke="#252e42" stroke-width="1"/><line x1="48" y1="148.0" x2="404" y2="148.0" stroke="#252e42" stroke-width="1"/><line x1="48.0" y1="16" x2="48.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="107.3" y1="16" x2="107.3" y2="148" stroke="#252e42" stroke-width="1"/><line x1="166.7" y1="16" x2="166.7" y2="148" stroke="#252e42" stroke-width="1"/><line x1="226.0" y1="16" x2="226.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="285.3" y1="16" x2="285.3" y2="148" stroke="#252e42" stroke-width="1"/><line x1="344.7" y1="16" x2="344.7" y2="148" stroke="#252e42" stroke-width="1"/><line x1="404.0" y1="16" x2="404.0" y2="148" stroke="#252e42" stroke-width="1"/><line x1="48" y1="16" x2="48" y2="148" stroke="#6b7a99" stroke-width="1.5"/><line x1="48" y1="148" x2="404" y2="148" stroke="#6b7a99" stroke-width="1.5"/><polyline points="48.0,119.7 89.5,119.7 92.5,53.7 95.5,53.7 131.1,53.7 134.0,119.7 166.7,119.7 166.7,119.7 208.2,119.7 211.2,53.7 214.1,53.7 249.7,53.7 252.7,119.7 285.3,119.7 285.3,119.7 326.9,119.7 329.8,53.7 332.8,53.7 368.4,53.7 371.4,119.7 404.0,119.7" fill="none" stroke="#f87171" stroke-width="2.5" stroke-linejoin="round"/><text x="42" y="151.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">0</text><text x="42" y="113.28571428571429" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">2</text><text x="42" y="75.57142857142858" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">4</text><text x="42" y="37.85714285714286" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">6</text><text x="42" y="56.714285714285715" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="end" font-weight="normal">5.0</text><line x1="48" y1="53.7" x2="404" y2="53.7" stroke="#6b7a99" stroke-width="1" stroke-dasharray="4,3"/><text x="210" y="178" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">Time →</text><text x="12" y="90" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" transform="rotate(-90,12,90)">EtCO₂ (kPa)</text><text x="210" y="26" fill="#f87171" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">Rebreathing (elevated baseline)</text></svg>''',
    'phys020': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 200" style="width:100%;max-width:420px;background:#161b27;border-radius:8px;display:block;margin:0 auto 16px;"><line x1="52" y1="20.0" x2="404" y2="20.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="57.0" x2="404" y2="57.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="94.0" x2="404" y2="94.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="131.0" x2="404" y2="131.0" stroke="#252e42" stroke-width="1"/><line x1="52" y1="168.0" x2="404" y2="168.0" stroke="#252e42" stroke-width="1"/><line x1="52.0" y1="20" x2="52.0" y2="168" stroke="#252e42" stroke-width="1"/><line x1="122.4" y1="20" x2="122.4" y2="168" stroke="#252e42" stroke-width="1"/><line x1="192.8" y1="20" x2="192.8" y2="168" stroke="#252e42" stroke-width="1"/><line x1="263.2" y1="20" x2="263.2" y2="168" stroke="#252e42" stroke-width="1"/><line x1="333.6" y1="20" x2="333.6" y2="168" stroke="#252e42" stroke-width="1"/><line x1="404.0" y1="20" x2="404.0" y2="168" stroke="#252e42" stroke-width="1"/><line x1="52" y1="20" x2="52" y2="168" stroke="#6b7a99" stroke-width="1.5"/><line x1="52" y1="168" x2="404" y2="168" stroke="#6b7a99" stroke-width="1.5"/><polyline points="52.0,168.0 52.0,168.0 54.9,154.5 57.9,142.0 60.8,130.4 63.7,119.9 66.7,110.3 69.6,101.6 72.5,93.8 75.5,86.9 78.4,80.8 81.3,75.4 84.3,70.8 87.2,66.9 90.1,63.7 93.1,61.1 96.0,59.0 98.9,57.5 101.9,56.5 104.8,55.9 107.7,55.6 110.7,55.5 113.6,54.0 116.5,52.6 119.5,51.2 122.4,49.9 125.3,48.7 128.3,47.5 131.2,46.4 134.1,45.4 137.1,44.4 140.0,43.4 142.9,42.5 145.9,41.7 148.8,40.9 151.7,40.1 154.7,39.4 157.6,38.7 160.5,38.0 163.5,37.4 166.4,36.8 169.3,36.3 172.3,35.8 175.2,35.2 178.1,34.8 181.1,34.3 184.0,33.9 186.9,33.5 189.9,33.1 192.8,32.7 195.7,32.4 198.7,32.0 201.6,31.7 204.5,31.4 207.5,31.2 210.4,30.9 213.3,30.6 216.3,30.4 219.2,30.2 222.1,29.9 225.1,29.7 228.0,29.5 230.9,29.4 233.9,29.2 236.8,29.0 239.7,28.9 242.7,28.7 245.6,28.6 248.5,28.4 251.5,28.3 254.4,28.2 257.3,28.1 260.3,28.0 263.2,27.9 266.1,27.8 269.1,27.7 272.0,27.6 274.9,27.5 277.9,27.4 280.8,27.3 283.7,27.3 286.7,27.2 289.6,27.1 292.5,27.1 295.5,27.0 298.4,26.9 301.3,26.9 304.3,26.8 307.2,26.8 310.1,26.8 313.1,26.7 316.0,26.7 318.9,26.6 321.9,26.6 324.8,26.6 327.7,26.5 330.7,26.5 333.6,26.5 336.5,26.4 339.5,26.4 342.4,26.4 345.3,26.4 348.3,26.3 351.2,26.3 354.1,26.3 357.1,26.3 360.0,26.3 362.9,26.2 365.9,26.2 368.8,26.2 371.7,26.2 374.7,26.2 377.6,26.2 380.5,26.2 383.5,26.1 386.4,26.1 389.3,26.1 392.3,26.1 395.2,26.1 398.1,26.1 401.1,26.1 404.0,26.1" fill="none" stroke="#4ade80" stroke-width="2.5" stroke-linejoin="round"/><polyline points="52.0,168.0 52.0,168.0 54.9,160.9 57.9,154.3 60.8,148.2 63.7,142.7 66.7,137.6 69.6,133.1 72.5,129.0 75.5,125.3 78.4,122.1 81.3,119.3 84.3,116.8 87.2,114.8 90.1,113.1 93.1,111.7 96.0,110.7 98.9,109.9 101.9,109.3 104.8,109.0 107.7,108.8 110.7,108.8 113.6,105.8 116.5,102.9 119.5,100.2 122.4,97.6 125.3,95.1 128.3,92.8 131.2,90.6 134.1,88.5 137.1,86.5 140.0,84.6 142.9,82.8 145.9,81.1 148.8,79.5 151.7,78.0 154.7,76.5 157.6,75.2 160.5,73.9 163.5,72.6 166.4,71.4 169.3,70.3 172.3,69.3 175.2,68.3 178.1,67.3 181.1,66.4 184.0,65.5 186.9,64.7 189.9,63.9 192.8,63.2 195.7,62.5 198.7,61.9 201.6,61.2 204.5,60.6 207.5,60.1 210.4,59.5 213.3,59.0 216.3,58.5 219.2,58.1 222.1,57.7 225.1,57.2 228.0,56.9 230.9,56.5 233.9,56.1 236.8,55.8 239.7,55.5 242.7,55.2 245.6,54.9 248.5,54.6 251.5,54.4 254.4,54.1 257.3,53.9 260.3,53.7 263.2,53.5 266.1,53.3 269.1,53.1 272.0,52.9 274.9,52.7 277.9,52.6 280.8,52.4 283.7,52.3 286.7,52.1 289.6,52.0 292.5,51.9 295.5,51.8 298.4,51.7 301.3,51.6 304.3,51.5 307.2,51.4 310.1,51.3 313.1,51.2 316.0,51.1 318.9,51.0 321.9,51.0 324.8,50.9 327.7,50.8 330.7,50.8 333.6,50.7 336.5,50.6 339.5,50.6 342.4,50.5 345.3,50.5 348.3,50.4 351.2,50.4 354.1,50.4 357.1,50.3 360.0,50.3 362.9,50.2 365.9,50.2 368.8,50.2 371.7,50.2 374.7,50.1 377.6,50.1 380.5,50.1 383.5,50.0 386.4,50.0 389.3,50.0 392.3,50.0 395.2,50.0 398.1,49.9 401.1,49.9 404.0,49.9" fill="none" stroke="#fbbf24" stroke-width="2.5" stroke-linejoin="round"/><polyline points="52.0,168.0 52.0,168.0 54.9,159.5 57.9,151.5 60.8,144.3 63.7,137.6 66.7,131.6 69.6,126.1 72.5,121.2 75.5,116.8 78.4,112.9 81.3,109.5 84.3,106.6 87.2,104.1 90.1,102.1 93.1,100.5 96.0,99.2 98.9,98.2 101.9,97.6 104.8,97.2 107.7,97.0 110.7,97.0 113.6,96.1 116.5,95.2 119.5,94.4 122.4,93.6 125.3,92.9 128.3,92.2 131.2,91.5 134.1,90.9 137.1,90.3 140.0,89.7 142.9,89.2 145.9,88.7 148.8,88.2 151.7,87.7 154.7,87.3 157.6,86.9 160.5,86.5 163.5,86.1 166.4,85.8 169.3,85.4 172.3,85.1 175.2,84.8 178.1,84.5 181.1,84.2 184.0,84.0 186.9,83.7 189.9,83.5 192.8,83.3 195.7,83.1 198.7,82.9 201.6,82.7 204.5,82.5 207.5,82.3 210.4,82.2 213.3,82.0 216.3,81.9 219.2,81.7 222.1,81.6 225.1,81.5 228.0,81.4 230.9,81.3 233.9,81.2 236.8,81.1 239.7,81.0 242.7,80.9 245.6,80.8 248.5,80.7 251.5,80.6 254.4,80.6 257.3,80.5 260.3,80.4 263.2,80.4 266.1,80.3 269.1,80.2 272.0,80.2 274.9,80.1 277.9,80.1 280.8,80.0 283.7,80.0 286.7,80.0 289.6,79.9 292.5,79.9 295.5,79.9 298.4,79.8 301.3,79.8 304.3,79.8 307.2,79.7 310.1,79.7 313.1,79.7 316.0,79.7 318.9,79.6 321.9,79.6 324.8,79.6 327.7,79.6 330.7,79.5 333.6,79.5 336.5,79.5 339.5,79.5 342.4,79.5 345.3,79.5 348.3,79.5 351.2,79.4 354.1,79.4 357.1,79.4 360.0,79.4 362.9,79.4 365.9,79.4 368.8,79.4 371.7,79.4 374.7,79.4 377.6,79.3 380.5,79.3 383.5,79.3 386.4,79.3 389.3,79.3 392.3,79.3 395.2,79.3 398.1,79.3 401.1,79.3 404.0,79.3" fill="none" stroke="#60a5fa" stroke-width="2.5" stroke-linejoin="round"/><line x1="110.7" y1="20" x2="110.7" y2="168" stroke="#6b7a99" stroke-width="1" stroke-dasharray="4,3"/><text x="110.66666666666666" y="182" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">1s</text><text x="46" y="171.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">0</text><text x="46" y="141.4" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">1</text><text x="46" y="111.8" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">2</text><text x="46" y="82.2" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">3</text><text x="46" y="52.599999999999994" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">4</text><text x="46" y="23.0" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="end" font-weight="normal">5</text><text x="52.0" y="182" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">0</text><text x="169.33333333333331" y="182" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">2</text><text x="286.66666666666663" y="182" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">4</text><text x="404.0" y="182" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">6</text><text x="210" y="198" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" font-weight="normal">Time (s)</text><text x="12" y="100" fill="#6b7a99" font-family="IBM Plex Mono,monospace" font-size="9" text-anchor="middle" transform="rotate(-90,12,100)">Volume (L)</text><rect x="274" y="20" width="120" height="56" fill="#0e1117" rx="4" opacity="0.9"/><line x1="280" y1="32" x2="292" y2="32" stroke="#4ade80" stroke-width="2"/><text x="296" y="35" fill="#4ade80" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Normal 79%</text><line x1="280" y1="48" x2="292" y2="48" stroke="#fbbf24" stroke-width="2"/><text x="296" y="51" fill="#fbbf24" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Obstructive 50%</text><line x1="280" y1="64" x2="292" y2="64" stroke="#60a5fa" stroke-width="2"/><text x="296" y="67" fill="#60a5fa" font-family="IBM Plex Mono,monospace" font-size="8" text-anchor="start" font-weight="normal">Restrictive 83%</text></svg>''',
}

# ── Canonical flashcard deck structure ───────────────────────────────────────
CANONICAL_DECKS = [
    {"id": "phy_resp",    "name": "Respiratory Physiology",           "colour": "#2dd4bf", "cards": []},
    {"id": "phy_cvs",     "name": "Cardiovascular Physiology",        "colour": "#2dd4bf", "cards": []},
    {"id": "phy_neuro",   "name": "Neurophysiology & Pain",           "colour": "#2dd4bf", "cards": []},
    {"id": "phy_renal",   "name": "Renal & Acid-Base",                "colour": "#2dd4bf", "cards": []},
    {"id": "phy_gi",      "name": "Hepatic, GI & Metabolic",          "colour": "#2dd4bf", "cards": []},
    {"id": "phy_haem",    "name": "Haematology & Immunology",         "colour": "#2dd4bf", "cards": []},
    {"id": "phy_endo",    "name": "Endocrine & Obstetric Physiology",  "colour": "#2dd4bf", "cards": []},
    {"id": "ph_inh",      "name": "Inhalational Agents",              "colour": "#a78bfa", "cards": []},
    {"id": "ph_iv",       "name": "IV Induction Agents & Sedatives",  "colour": "#a78bfa", "cards": []},
    {"id": "ph_opioid",   "name": "Opioids & Analgesics",             "colour": "#a78bfa", "cards": []},
    {"id": "ph_nmb",      "name": "NMBs & Reversal",                  "colour": "#a78bfa", "cards": []},
    {"id": "ph_la",       "name": "Local Anaesthetics",               "colour": "#a78bfa", "cards": []},
    {"id": "ph_cvd",      "name": "Cardiovascular Drugs",             "colour": "#a78bfa", "cards": []},
    {"id": "ph_other",    "name": "Antiemetics, Antacids & Other",    "colour": "#a78bfa", "cards": []},
    {"id": "phx_elec",    "name": "Electricity, Safety & Equipment",  "colour": "#38bdf8", "cards": []},
    {"id": "phx_gas",     "name": "Gas Laws & Vaporisers",            "colour": "#38bdf8", "cards": []},
    {"id": "phx_mon",     "name": "Monitoring (CO, Neuro, Temp)",     "colour": "#38bdf8", "cards": []},
    {"id": "phx_resp",    "name": "Respiratory Mechanics & Spirometry","colour": "#38bdf8", "cards": []},
    {"id": "phx_stats",   "name": "Statistics & Clinical Trials",     "colour": "#38bdf8", "cards": []},
    {"id": "ca_airway",   "name": "Airway Anatomy & Management",      "colour": "#fb923c", "cards": []},
    {"id": "ca_regional", "name": "Regional Anatomy & Blocks",        "colour": "#fb923c", "cards": []},
    {"id": "ca_preop",    "name": "Preoperative Assessment",          "colour": "#fb923c", "cards": []},
    {"id": "ca_emerg",    "name": "Perioperative Emergencies",        "colour": "#fb923c", "cards": []},
    {"id": "ca_obs",      "name": "Obstetric Anaesthesia",            "colour": "#fb923c", "cards": []},
    {"id": "ca_paeds",    "name": "Paediatric Anaesthesia",           "colour": "#fb923c", "cards": []},
]

# ── Fixed question bank ───────────────────────────────────────────────────────
FIXED_BANK = [
    # ── Physiology ──────────────────────────────────────────────────────────
    {
        "id": "phy001", "topic": "Physiology",
        "question": "Which of the following best describes the Bohr effect?",
        "options": {
            "A": "Increased CO₂ shifts the oxygen-haemoglobin dissociation curve to the right",
            "B": "Increased pH shifts the oxygen-haemoglobin dissociation curve to the right",
            "C": "Decreased temperature shifts the oxygen-haemoglobin dissociation curve to the right",
            "D": "2,3-DPG shifts the oxygen-haemoglobin dissociation curve to the left",
            "E": "Foetal haemoglobin shifts the curve to the right",
        },
        "answer": "A",
        "explanation": "The Bohr effect describes the rightward shift of the ODC in the presence of increased CO₂ (or H⁺, decreased pH), promoting O₂ offloading in metabolically active tissues. Decreased temperature, alkalosis, and HbF all shift the curve leftward.",
    },
    {
        "id": "phy002", "topic": "Physiology",
        "question": "The FRC is the volume of air remaining after:",
        "options": {
            "A": "A maximal forced expiration",
            "B": "A maximal forced inspiration",
            "C": "A normal tidal expiration",
            "D": "A normal tidal inspiration",
            "E": "Functional residual capacity cannot be measured by spirometry",
        },
        "answer": "C",
        "explanation": "FRC = ERV + RV. It is the volume in the lungs at the end of a normal passive expiration, where elastic recoil of the lung and chest wall are in equilibrium. It cannot be measured directly by spirometry (requires helium dilution or body plethysmography) — but the volume itself is defined by the end of normal tidal expiration.",
    },
    {
        "id": "phy003", "topic": "Physiology",
        "question": "Regarding the cardiac action potential in a ventricular myocyte, phase 2 (the plateau) is primarily maintained by:",
        "options": {
            "A": "Rapid influx of Na⁺ through fast channels",
            "B": "Efflux of K⁺ through inward rectifier channels",
            "C": "Influx of Ca²⁺ through L-type voltage-gated channels",
            "D": "Influx of Cl⁻",
            "E": "Efflux of Na⁺",
        },
        "answer": "C",
        "explanation": "Phase 2 (plateau) is characterised by a balance between slow Ca²⁺ influx via L-type channels and K⁺ efflux. The Ca²⁺ influx triggers calcium-induced calcium release from the SR, driving myocardial contraction. Phase 0 is the rapid Na⁺ influx; Phase 3 is K⁺ efflux repolarisation.",
    },
    {
        "id": "phy004", "topic": "Physiology",
        "question": "The Henderson-Hasselbalch equation for blood pH gives a normal value of 7.4 when HCO₃⁻ is 24 mmol/L and PaCO₂ is 5.3 kPa. If PaCO₂ rises acutely to 8 kPa without renal compensation, which of the following is expected?",
        "options": {
            "A": "pH rises due to increased CO₂ buffering",
            "B": "pH falls and HCO₃⁻ rises slightly due to chemical buffering",
            "C": "pH falls and HCO₃⁻ remains unchanged",
            "D": "pH rises and HCO₃⁻ rises due to renal compensation",
            "E": "pH is unchanged as CO₂ is a volatile acid",
        },
        "answer": "B",
        "explanation": "In acute respiratory acidosis, CO₂ reacts with water to form H₂CO₃, dissociating to H⁺ and HCO₃⁻. Chemical (non-renal) buffering by haemoglobin and proteins consumes H⁺ and slightly raises HCO₃⁻ (~1 mmol/L per 1.3 kPa rise in PaCO₂). Renal compensation (larger HCO₃⁻ rise) takes 3–5 days.",
    },
    {
        "id": "phy005", "topic": "Physiology",
        "question": "During exercise, which of the following contributes MOST to increased cardiac output?",
        "options": {
            "A": "Increased stroke volume from the Bainbridge reflex",
            "B": "Increased heart rate driven by sympathetic activation",
            "C": "Decreased systemic vascular resistance alone",
            "D": "Increased preload from venoconstriction only",
            "E": "Parasympathetic withdrawal alone",
        },
        "answer": "B",
        "explanation": "During vigorous exercise, cardiac output can increase 5-fold. Heart rate increase (driven by sympathetic activation and parasympathetic withdrawal) is the dominant contributor. Stroke volume increases due to increased preload (Starling mechanism), increased contractility, and reduced afterload — but HR rise accounts for the majority of CO increase at high workloads.",
    },

    # ── Pharmacology ────────────────────────────────────────────────────────
    {
        "id": "phar001", "topic": "Pharmacology",
        "question": "Regarding propofol pharmacokinetics, which of the following is correct?",
        "options": {
            "A": "It is predominantly renally excreted unchanged",
            "B": "Its context-sensitive half-time is independent of infusion duration",
            "C": "It undergoes hepatic conjugation to inactive glucuronide metabolites",
            "D": "Its high pKa means it is largely ionised at physiological pH",
            "E": "Redistribution is not responsible for awakening after a single bolus",
        },
        "answer": "C",
        "explanation": "Propofol is hepatically metabolised (and extrahepatic — lung, kidney) to inactive glucuronide and sulphate conjugates excreted renally. Its context-sensitive half-time increases with prolonged infusion. High lipid solubility and low pKa (not high) explain its rapid CNS entry. Awakening after a bolus is due to redistribution from brain to vessel-rich and then muscle/fat compartments.",
    },
    {
        "id": "phar002", "topic": "Pharmacology",
        "question": "Which feature of suxamethonium's mechanism explains phase II block?",
        "options": {
            "A": "Competitive antagonism at the nicotinic receptor",
            "B": "Persistent depolarisation causing Na⁺ channel inactivation, followed by desensitisation of the receptor",
            "C": "Inhibition of acetylcholinesterase at the neuromuscular junction",
            "D": "Blockade of voltage-gated Ca²⁺ channels in the motor nerve terminal",
            "E": "Selective inhibition of fast-twitch muscle fibres",
        },
        "answer": "B",
        "explanation": "Suxamethonium binds the nicotinic AChR causing persistent depolarisation (Phase I / depolarising block). With repeated or prolonged dosing, the receptor desensitises — it returns to resting configuration but becomes unresponsive. This Phase II (desensitisation) block resembles a non-depolarising block (fade on TOF, reversal with neostigmine).",
    },
    {
        "id": "phar003", "topic": "Pharmacology",
        "question": "Remifentanil differs from other opioids primarily because:",
        "options": {
            "A": "It is metabolised by plasma cholinesterase",
            "B": "It has an ester linkage hydrolysed by non-specific tissue esterases",
            "C": "It is the only opioid that does not cause respiratory depression",
            "D": "Its context-sensitive half-time increases markedly after 2 hours",
            "E": "It undergoes zero-order kinetics at clinical doses",
        },
        "answer": "B",
        "explanation": "Remifentanil contains a methyl ester group hydrolysed by ubiquitous non-specific tissue and plasma esterases (not plasma cholinesterase). This gives it an ultra-short, context-insensitive offset (~3–5 min) regardless of infusion duration. It does cause respiratory depression. Its context-sensitive half-time remains ~3 min even after prolonged infusion.",
    },
    {
        "id": "phar004", "topic": "Pharmacology",
        "question": "The volume of distribution (Vd) of a drug is MOST increased by:",
        "options": {
            "A": "High water solubility and low protein binding",
            "B": "High lipid solubility, extensive tissue binding, and low plasma protein binding",
            "C": "High plasma protein binding and low lipid solubility",
            "D": "Rapid hepatic metabolism",
            "E": "Large molecular weight preventing membrane crossing",
        },
        "answer": "B",
        "explanation": "Vd = amount in body / plasma concentration. High lipid solubility allows extensive tissue penetration; high tissue binding 'sequesters' drug away from plasma; low plasma protein binding means more free drug available for distribution. Drugs like amiodarone and chloroquine have enormous Vd (hundreds of litres) due to these properties.",
    },
    {
        "id": "phar005", "topic": "Pharmacology",
        "question": "Which of the following correctly describes the MAC of a volatile anaesthetic?",
        "options": {
            "A": "The concentration at which 50% of patients respond to a verbal command",
            "B": "The minimum alveolar concentration preventing movement in 95% of patients to surgical incision",
            "C": "The minimum alveolar concentration preventing movement in 50% of patients to surgical incision at 1 atmosphere",
            "D": "The concentration equivalent to 1 mg/kg IV propofol",
            "E": "A fixed value unaffected by age, temperature or opioid co-administration",
        },
        "answer": "C",
        "explanation": "MAC is the minimum alveolar concentration of a volatile agent at 1 atm that prevents purposeful movement in 50% of patients in response to a standardised surgical stimulus (skin incision). MAC-awake (~0.3–0.4 MAC) is where 50% respond to verbal command. MAC is reduced by age, hypothermia, opioids, N₂O, pregnancy, and increased by hyperthermia and chronic alcohol use.",
    },

    # ── Physics & Clinical Measurement ──────────────────────────────────────
    {
        "id": "phys001", "topic": "Physics & Clinical Measurement",
        "question": "Which of the following best describes the Fick principle as applied to cardiac output measurement?",
        "options": {
            "A": "CO = O₂ consumption / (arterial O₂ content − mixed venous O₂ content)",
            "B": "CO = (arterial O₂ content − venous O₂ content) / O₂ consumption",
            "C": "CO = stroke volume × arterial O₂ saturation",
            "D": "CO is calculated from the rate of indicator dye dilution over time",
            "E": "CO = mean arterial pressure / systemic vascular resistance × 80",
        },
        "answer": "A",
        "explanation": "Fick principle: CO (L/min) = O₂ consumption (mL/min) ÷ (CaO₂ − CvO₂) (mL/L). A-V O₂ content difference reflects oxygen extraction. Option D describes thermodilution/dye dilution. Option E is the SVR formula rearranged (CO = MAP/SVR × 80).",
    },
    {
        "id": "phys002", "topic": "Physics & Clinical Measurement",
        "question": "A capnograph trace shows a slowly rising phase 3 (alveolar plateau) that never reaches a plateau before the next inspiration. This is most consistent with:",
        "options": {
            "A": "Normal breathing",
            "B": "Oesophageal intubation",
            "C": "Obstructive airways disease (e.g. COPD or bronchospasm)",
            "D": "Hyperventilation",
            "E": "Rebreathing of CO₂",
        },
        "answer": "C",
        "explanation": "In obstructive disease, uneven V/Q leads to asynchronous emptying of lung units with different CO₂ concentrations, causing a sloping upward phase 3 ('shark fin' or 'obstructive' waveform). Oesophageal intubation gives absent/flat trace. Rebreathing elevates the baseline. Normal breathing has a flat phase 3 plateau.",
    },
    {
        "id": "phys003", "topic": "Physics & Clinical Measurement",
        "question": "Regarding the physics of flow through a tube, which of the following is correct according to the Hagen-Poiseuille law?",
        "options": {
            "A": "Flow is proportional to the square of the radius",
            "B": "Flow is inversely proportional to the length of the tube",
            "C": "Doubling the radius increases flow 16-fold",
            "D": "Flow is independent of fluid viscosity under laminar conditions",
            "E": "Turbulent flow obeys Hagen-Poiseuille provided Reynolds number < 4000",
        },
        "answer": "C",
        "explanation": "Hagen-Poiseuille: Q = πr⁴ΔP / 8ηL. Flow is proportional to r⁴ — doubling radius increases flow 2⁴ = 16-fold. Flow is inversely proportional to length (longer tube → more resistance). Viscosity (η) directly reduces flow. Hagen-Poiseuille applies only to laminar flow (Re < ~2000).",
    },
    {
        "id": "phys004", "topic": "Physics & Clinical Measurement",
        "question": "The Severinghaus electrode measures:",
        "options": {
            "A": "PO₂ by amperometric reduction of oxygen",
            "B": "pH by a glass electrode in contact with blood",
            "C": "PCO₂ via pH change in a bicarbonate solution separated from blood by a CO₂-permeable membrane",
            "D": "Oxygen saturation via spectrophotometry at two wavelengths",
            "E": "CO₂ by infrared absorption",
        },
        "answer": "C",
        "explanation": "The Severinghaus electrode measures PCO₂: CO₂ diffuses across a silicone membrane into NaHCO₃ solution, altering its pH, detected by a glass pH electrode. The Clark electrode measures PO₂ (amperometric). Pulse oximetry uses two wavelengths. Capnography uses infrared absorption.",
    },
    {
        "id": "phys005", "topic": "Physics & Clinical Measurement",
        "question": "Which of the following best explains why nitrous oxide can expand pneumothorax?",
        "options": {
            "A": "N₂O has a higher blood:gas coefficient than nitrogen",
            "B": "N₂O is delivered at higher partial pressures than N₂ in air, so net diffusion into the cavity exceeds N₂ egress",
            "C": "N₂O directly stimulates surfactant degradation",
            "D": "N₂O increases pulmonary vascular resistance, raising cavity pressure",
            "E": "N₂O reacts with haemoglobin to release nitrogen gas",
        },
        "answer": "B",
        "explanation": "N₂O is 34× more soluble in blood than N₂. When N₂O is administered, it diffuses into gas-filled cavities (pneumothorax, bowel, middle ear, air emboli) much faster than N₂ can diffuse out, because the N₂O partial pressure gradient into the cavity vastly exceeds the N₂ gradient out. This can double a pneumothorax in ~10 minutes.",
    },

    # ── Clinical Anaesthesia ─────────────────────────────────────────────────
    {
        "id": "clin001", "topic": "Clinical Anaesthesia",
        "question": "A 68-year-old presents for elective hip replacement. Echo shows severe aortic stenosis (valve area 0.7 cm², mean gradient 52 mmHg). Which haemodynamic goal is MOST important intraoperatively?",
        "options": {
            "A": "Allow tachycardia to maintain cardiac output",
            "B": "Maintain sinus rhythm, adequate preload and avoid hypotension",
            "C": "Reduce afterload aggressively with vasodilators to offload the LV",
            "D": "Target heart rate of 90–100 bpm to maintain forward flow",
            "E": "Avoid all opioids as they worsen outflow obstruction",
        },
        "answer": "B",
        "explanation": "Severe AS: the LV is hypertrophied and pressure-dependent. Goals are: sinus rhythm (atrial kick contributes ~40% filling in AS), adequate preload (stiff LV needs filling), normal-to-slow heart rate (more diastolic filling time), and maintenance of SVR (avoid vasodilation/hypotension — coronary perfusion pressure depends on DBP in a hypertrophied LV). Tachycardia and vasodilation are particularly dangerous.",
    },
    {
        "id": "clin002", "topic": "Clinical Anaesthesia",
        "question": "During RSI, the patient desaturates rapidly to 80% despite preoxygenation. Laryngoscopy reveals a Cormack-Lehane grade 3 view. First attempt at intubation fails. According to DAS guidelines, what is the correct next step?",
        "options": {
            "A": "Immediately proceed to surgical airway",
            "B": "Declare 'cannot intubate cannot oxygenate' and call for help",
            "C": "Optimise position, use external laryngeal manipulation, and limit to one further intubation attempt",
            "D": "Insert a supraglottic airway device and awaken the patient",
            "E": "Perform a second laryngoscopy immediately without any changes",
        },
        "answer": "C",
        "explanation": "DAS failed intubation guidelines (2015): after a failed first attempt, optimise conditions (head position, BURP/ELM, change blade/operator) and make a maximum of one further attempt. If intubation fails again, declare failed intubation, insert an SGA to oxygenate, and decide: wake up vs proceed. CICO is only declared when oxygenation is impossible by all means — at that point surgical airway is indicated.",
    },
    {
        "id": "clin003", "topic": "Clinical Anaesthesia",
        "question": "Local anaesthetic systemic toxicity (LAST) — which of the following is the MOST appropriate early intervention?",
        "options": {
            "A": "IV metaraminol 500 mcg bolus",
            "B": "IV 20% lipid emulsion 1.5 mL/kg bolus",
            "C": "Immediate DC cardioversion for any arrhythmia",
            "D": "IV adrenaline 1 mg bolus",
            "E": "Hyperventilation to raise PaCO₂ and improve cerebral perfusion",
        },
        "answer": "B",
        "explanation": "AAGBI LAST guidelines: stop LA injection, call for help, maintain airway/oxygenation, control seizures (benzodiazepine), then give 20% Intralipid 1.5 mL/kg IV bolus followed by infusion 15 mL/kg/hr. Adrenaline should be used in reduced doses (≤1 mcg/kg) — full doses worsen outcomes. Cardioversion may be needed but lipid rescue should not be delayed. Hyperventilation reduces CO₂ (worsens ionisation of LA).",
    },
    {
        "id": "clin004", "topic": "Clinical Anaesthesia",
        "question": "Which nerve block, if performed successfully, would provide analgesia for a total knee replacement without motor block of the quadriceps?",
        "options": {
            "A": "Femoral nerve block",
            "B": "Adductor canal block",
            "C": "Sciatic nerve block",
            "D": "Lateral femoral cutaneous nerve block",
            "E": "Obturator nerve block alone",
        },
        "answer": "B",
        "explanation": "The adductor canal block (ACB) targets the saphenous nerve (sensory) and associated branches within the adductor canal, sparing the motor branches of the femoral nerve to quadriceps. This preserves quadriceps strength, reducing falls risk and enabling early mobilisation — unlike the femoral nerve block which blocks motor supply. ACB is now standard for TKR analgesia.",
    },
    {
        "id": "clin005", "topic": "Clinical Anaesthesia",
        "question": "A patient in the post-anaesthesia care unit has a respiratory rate of 6/min, SpO₂ 91% on 15L O₂, and is difficult to rouse. The MOST likely cause and treatment is:",
        "options": {
            "A": "Residual volatile agent — supportive care and time",
            "B": "Opioid-induced respiratory depression — naloxone 400 mcg IV",
            "C": "Opioid-induced respiratory depression — naloxone 40 mcg IV titrated",
            "D": "Residual neuromuscular blockade — neostigmine 2.5 mg IV",
            "E": "Hypoglycaemia — IV dextrose 50 mL of 50%",
        },
        "answer": "C",
        "explanation": "Clinical picture is opioid-induced POCD/respiratory depression. Naloxone should be titrated in small doses (40–80 mcg IV every 2–3 min) to restore respiratory drive without precipitating acute pain, hypertension, pulmonary oedema, or opioid withdrawal. A full 400 mcg bolus risks abrupt reversal of analgesia and cardiovascular instability.",
    },
    {
        "id": "phy006", "topic": "Physiology",
        "question": "Which of the following correctly describes the Frank-Starling mechanism?",
        "options": {
            "A": "Increased heart rate leads to increased stroke volume",
            "B": "Increased ventricular end-diastolic volume leads to increased stroke volume",
            "C": "Increased afterload leads to increased stroke volume",
            "D": "Decreased preload leads to increased cardiac output",
            "E": "Increased sympathetic tone is required for the mechanism to operate",
        },
        "answer": "B",
        "explanation": "The Frank-Starling law states that stroke volume increases with increasing end-diastolic volume (preload), up to a point. This is due to increased overlap of actin and myosin filaments increasing the force of contraction. It operates intrinsically, independent of sympathetic innervation.",
    },
    {
        "id": "phy007", "topic": "Physiology",
        "question": "What is the normal value for pulmonary vascular resistance (PVR) in a healthy adult?",
        "options": {
            "A": "50\u2013100 dynes\u00b7s\u00b7cm\u207b\u2075",
            "B": "800\u20131200 dynes\u00b7s\u00b7cm\u207b\u2075",
            "C": "200\u2013400 dynes\u00b7s\u00b7cm\u207b\u2075",
            "D": "1500\u20132000 dynes\u00b7s\u00b7cm\u207b\u2075",
            "E": "10\u201330 dynes\u00b7s\u00b7cm\u207b\u2075",
        },
        "answer": "A",
        "explanation": "Normal PVR is approximately 50\u2013100 dynes\u00b7s\u00b7cm\u207b\u2075 (roughly 1\u20132 Wood units). This is about 10-fold lower than systemic vascular resistance (800\u20131200 dynes\u00b7s\u00b7cm\u207b\u2075), reflecting the low-resistance, high-compliance pulmonary circulation.",
    },
    {
        "id": "phy008", "topic": "Physiology",
        "question": "During exercise, which factor contributes MOST to the increase in oxygen delivery to skeletal muscle?",
        "options": {
            "A": "Increased haemoglobin concentration",
            "B": "Left shift of the oxyhaemoglobin dissociation curve",
            "C": "Increased cardiac output and local vasodilation",
            "D": "Increased respiratory rate alone",
            "E": "Decreased 2,3-DPG",
        },
        "answer": "C",
        "explanation": "The dominant mechanism for increased O\u2082 delivery during exercise is increased cardiac output (via increased HR and SV) combined with local metabolic vasodilation (CO\u2082, lactate, K\u207a, adenosine) redirecting blood to active muscle. The right-shift of the ODC (Bohr effect) facilitates unloading but delivery increase is primarily flow-driven.",
    },
    {
        "id": "phy009", "topic": "Physiology",
        "question": "Which buffer system provides the greatest buffering capacity in blood?",
        "options": {
            "A": "Phosphate buffer system",
            "B": "Protein buffer system",
            "C": "Bicarbonate buffer system",
            "D": "Haemoglobin buffer system",
            "E": "Bone mineral buffering",
        },
        "answer": "C",
        "explanation": "The bicarbonate/CO\u2082 system is the most important blood buffer in clinical terms due to its open system \u2014 CO\u2082 is continuously excreted by the lungs, allowing the buffer to operate far from equilibrium. Although haemoglobin has a higher intrinsic buffering capacity by concentration, the bicarbonate system's openness gives it greater effective capacity.",
    },
    {
        "id": "phy010", "topic": "Physiology",
        "question": "What is the anatomical dead space in a 70 kg adult approximately?",
        "options": {
            "A": "50 mL",
            "B": "150 mL",
            "C": "350 mL",
            "D": "500 mL",
            "E": "1000 mL",
        },
        "answer": "B",
        "explanation": "Anatomical dead space is approximately 2 mL/kg, giving ~150 mL in a 70 kg adult. A useful rule of thumb is 1 mL per pound (2.2 mL/kg) body weight. This represents conducting airways (trachea to terminal bronchioles) where no gas exchange occurs.",
    },
    {
        "id": "phy011", "topic": "Physiology",
        "question": "Which of the following BEST describes hypoxic pulmonary vasoconstriction (HPV)?",
        "options": {
            "A": "It is mediated by the sympathetic nervous system",
            "B": "It diverts blood from well-ventilated to poorly-ventilated areas",
            "C": "It is inhibited by inhalational anaesthetic agents",
            "D": "It is a reflex originating in the carotid bodies",
            "E": "It occurs only when PaO\u2082 falls below 8 kPa systemically",
        },
        "answer": "C",
        "explanation": "HPV is an intrinsic response of pulmonary vascular smooth muscle to low alveolar PO\u2082, diverting blood away from poorly-ventilated areas to optimise V/Q matching. Volatile anaesthetic agents (isoflurane, sevoflurane, desflurane) inhibit HPV in a dose-dependent manner, which is why they can worsen V/Q mismatch during one-lung ventilation.",
    },
    {
        "id": "phy012", "topic": "Physiology",
        "question": "The normal cerebral blood flow (CBF) in a conscious adult is approximately:",
        "options": {
            "A": "15 mL/100g/min",
            "B": "50 mL/100g/min",
            "C": "150 mL/100g/min",
            "D": "5 mL/100g/min",
            "E": "300 mL/100g/min",
        },
        "answer": "B",
        "explanation": "Normal CBF is approximately 50 mL/100g/min (global average), representing about 15% of cardiac output despite the brain comprising only 2% of body weight. Grey matter receives ~80 mL/100g/min and white matter ~20 mL/100g/min. Critical ischaemia occurs below ~20 mL/100g/min.",
    },
    {
        "id": "phy013", "topic": "Physiology",
        "question": "A patient has the following ABG: pH 7.28, PaCO\u2082 3.2 kPa, HCO\u2083\u207b 11 mmol/L, BE -14. What is the primary disturbance?",
        "options": {
            "A": "Respiratory acidosis with metabolic compensation",
            "B": "Metabolic acidosis with respiratory compensation",
            "C": "Metabolic alkalosis",
            "D": "Respiratory alkalosis with metabolic compensation",
            "E": "Mixed respiratory and metabolic acidosis",
        },
        "answer": "B",
        "explanation": "Low pH indicates acidosis. Low HCO\u2083\u207b and large negative BE indicate the primary process is metabolic acidosis. The low PaCO\u2082 (normal ~5.3 kPa) represents appropriate respiratory compensation (Kussmaul breathing). Using Winter's formula: expected PaCO\u2082 = (1.5 \u00d7 HCO\u2083\u207b) + 8 \u00b1 2 = 24.5 \u00b1 2 kPa \u2014 here 3.2 kPa is near the expected, confirming appropriate compensation.",
    },
    {
        "id": "phy014", "topic": "Physiology",
        "question": "Which of the following physiological changes occurs in normal pregnancy at term?",
        "options": {
            "A": "Functional residual capacity increases by 20%",
            "B": "Cardiac output increases by 40\u201350%",
            "C": "Systemic vascular resistance increases",
            "D": "Haematocrit increases above normal",
            "E": "Minimum alveolar concentration (MAC) decreases",
        },
        "answer": "B",
        "explanation": "Cardiac output increases 40\u201350% by term due to increased HR (~20%) and SV (~30%). FRC decreases by ~20% (diaphragm elevation). SVR decreases due to progesterone-mediated vasodilation and low-resistance placental circulation. A dilutional anaemia occurs (plasma volume increases more than red cell mass). MAC increases in pregnancy (progesterone effect).",
    },
    {
        "id": "phy015", "topic": "Physiology",
        "question": "What is the role of the juxtaglomerular apparatus (JGA) in renal autoregulation?",
        "options": {
            "A": "Detecting changes in plasma oncotic pressure",
            "B": "Detecting changes in tubular NaCl concentration and regulating renin release",
            "C": "Directly filtering plasma proteins",
            "D": "Producing erythropoietin in response to hypoxia",
            "E": "Regulating urinary concentration via aquaporin expression",
        },
        "answer": "B",
        "explanation": "The JGA consists of macula densa cells (sensing NaCl in the distal tubule) and granular cells (producing renin). When NaCl delivery is low (reduced perfusion), renin is released activating the RAAS, causing vasoconstriction and Na\u207a retention. This tubuloglomerular feedback is key to renal autoregulation.",
    },
    {
        "id": "phy016", "topic": "Physiology",
        "question": "Which of the following is a correct statement about functional residual capacity (FRC)?",
        "options": {
            "A": "FRC is the volume of gas after a maximal forced expiration",
            "B": "FRC equals ERV plus RV",
            "C": "FRC increases in the supine position",
            "D": "FRC can be measured by spirometry alone",
            "E": "FRC is unaffected by anaesthesia",
        },
        "answer": "B",
        "explanation": "FRC = expiratory reserve volume (ERV) + residual volume (RV). It represents the equilibrium point where inward elastic recoil of the lungs balances outward chest wall recoil. FRC decreases in the supine position (~25%), with obesity, pregnancy, and anaesthesia. It cannot be measured by spirometry alone (requires helium dilution, nitrogen washout, or body plethysmography).",
    },
    {
        "id": "phy017", "topic": "Physiology",
        "question": "Regarding action potentials in cardiac pacemaker cells, which statement is correct?",
        "options": {
            "A": "Phase 0 depolarisation is due to a fast sodium current",
            "B": "The resting membrane potential is stable at \u221290 mV",
            "C": "The funny current (If) contributes to spontaneous depolarisation",
            "D": "Phase 2 plateau is absent in pacemaker cells",
            "E": "Calcium plays no role in pacemaker depolarisation",
        },
        "answer": "C",
        "explanation": "Pacemaker cells (SA node) differ from ventricular myocytes: they have no true resting potential, instead showing spontaneous slow diastolic depolarisation (phase 4) driven by the 'funny' current (If) \u2014 an inward mixed Na\u207a/K\u207a current through HCN channels. Phase 0 is due to slow L-type Ca\u00b2\u207a channels (not fast Na\u207a channels). This is why verapamil/diltiazem slow the SA node.",
    },
    {
        "id": "phy018", "topic": "Physiology",
        "question": "Which correctly describes the oxygen-haemoglobin dissociation curve shift caused by carbon monoxide poisoning?",
        "options": {
            "A": "Right shift with decreased affinity",
            "B": "Left shift with decreased oxygen-carrying capacity",
            "C": "No shift \u2014 CO simply reduces available haemoglobin",
            "D": "Right shift with increased P50",
            "E": "Left shift with increased oxygen-carrying capacity",
        },
        "answer": "B",
        "explanation": "CO binds haemoglobin with 200\u00d7 the affinity of O\u2082, forming carboxyhaemoglobin (COHb). This reduces oxygen-carrying capacity AND causes a left shift of the remaining ODC (Haldane effect) \u2014 the remaining Hb binds O\u2082 more tightly, impairing tissue unloading. This double effect explains why CO poisoning is so dangerous even at relatively low COHb levels.",
    },
    {
        "id": "phy019", "topic": "Physiology",
        "question": "What is the primary mechanism of CO\u2082 transport in blood?",
        "options": {
            "A": "Dissolved CO\u2082 in plasma (70%)",
            "B": "Bound to haemoglobin as carbaminohaemoglobin (70%)",
            "C": "As bicarbonate ions in plasma (70%)",
            "D": "Bound to plasma proteins (50%)",
            "E": "As carbonic acid in plasma (60%)",
        },
        "answer": "C",
        "explanation": "CO\u2082 is transported as: bicarbonate ~70%, carbaminohaemoglobin ~23%, dissolved ~7%. CO\u2082 enters red cells, is hydrated by carbonic anhydrase to H\u2082CO\u2083, which dissociates to HCO\u2083\u207b (exported to plasma via chloride shift) and H\u207a (buffered by Hb). This is the dominant mechanism.",
    },
    {
        "id": "phy020", "topic": "Physiology",
        "question": "Which receptor mediates the Hering-Breuer inflation reflex?",
        "options": {
            "A": "Central chemoreceptors in the medulla",
            "B": "Slowly adapting pulmonary stretch receptors (SARs)",
            "C": "Rapidly adapting irritant receptors",
            "D": "Peripheral chemoreceptors in the carotid body",
            "E": "J-receptors in the alveolar walls",
        },
        "answer": "B",
        "explanation": "The Hering-Breuer reflex (inflation reflex) is mediated by slowly adapting pulmonary stretch receptors (SARs) in airway smooth muscle. Lung inflation activates these receptors, sending signals via the vagus nerve to inhibit inspiration. In adults this reflex is weak at normal tidal volumes but becomes important during large tidal volumes (>1L) and in neonates.",
    },
    {
        "id": "phy021", "topic": "Physiology",
        "question": "Regarding the glomerular filtration rate (GFR), which statement is correct?",
        "options": {
            "A": "Normal GFR is approximately 300 mL/min",
            "B": "GFR is directly proportional to afferent arteriolar resistance",
            "C": "GFR is maintained by autoregulation between MAP 80\u2013180 mmHg",
            "D": "Creatinine is freely filtered and actively secreted, making it an overestimate of GFR",
            "E": "Inulin clearance underestimates GFR as it is partially reabsorbed",
        },
        "answer": "C",
        "explanation": "Renal autoregulation maintains GFR and RBF relatively constant over a MAP range of approximately 70\u2013180 mmHg via myogenic response and tubuloglomerular feedback. Normal GFR ~125 mL/min. Creatinine is freely filtered and slightly secreted, so creatinine clearance slightly overestimates GFR. Inulin is the gold standard as it is freely filtered and neither secreted nor reabsorbed.",
    },
    {
        "id": "phy022", "topic": "Physiology",
        "question": "Which of the following best describes the central venous pressure (CVP) waveform component 'a wave'?",
        "options": {
            "A": "Ventricular systole causing tricuspid valve closure",
            "B": "Atrial contraction against a closed tricuspid valve",
            "C": "Atrial contraction during late diastole",
            "D": "Right ventricular filling during diastole",
            "E": "Venous return from the superior vena cava",
        },
        "answer": "C",
        "explanation": "The CVP 'a wave' represents atrial contraction during late diastole (just before ventricular systole). It is absent in atrial fibrillation. A 'cannon a wave' occurs when the atria contract against a closed tricuspid valve (complete heart block, junctional rhythms). The 'c wave' follows (tricuspid closure), then 'x descent' (atrial relaxation), 'v wave' (venous filling), and 'y descent' (tricuspid opening).",
    },
    {
        "id": "phy023", "topic": "Physiology",
        "question": "What is the approximate mixed venous oxygen saturation (SvO\u2082) in a healthy resting adult?",
        "options": {
            "A": "99%",
            "B": "90%",
            "C": "75%",
            "D": "60%",
            "E": "50%",
        },
        "answer": "C",
        "explanation": "Normal mixed venous O\u2082 saturation (measured in pulmonary artery) is approximately 70\u201375%. This reflects normal O\u2082 extraction (~25%) from a CaO\u2082 of ~20 mL/dL to a CvO\u2082 of ~15 mL/dL. A falling SvO\u2082 (<65%) indicates increased extraction due to reduced delivery (low CO, low Hb, low SaO\u2082) or increased consumption.",
    },
    {
        "id": "phy024", "topic": "Physiology",
        "question": "Which of the following correctly describes the law of Laplace as it applies to alveoli?",
        "options": {
            "A": "Larger alveoli have greater wall tension and are more likely to collapse",
            "B": "Surfactant increases surface tension to stabilise small alveoli",
            "C": "Smaller alveoli would have higher pressure and empty into larger ones if not for surfactant",
            "D": "Wall tension is directly proportional to radius at constant pressure",
            "E": "Pressure inside an alveolus is directly proportional to its radius",
        },
        "answer": "C",
        "explanation": "Laplace's law: P = 2T/r. Smaller alveoli (smaller r) would have higher internal pressure and collapse into larger ones (air embolism risk) if surface tension were constant. Surfactant (dipalmitoyl phosphatidylcholine) reduces surface tension more in smaller alveoli (where it is more concentrated), equalising pressure across alveoli of different sizes and preventing collapse.",
    },
    {
        "id": "phy025", "topic": "Physiology",
        "question": "Regarding pain pathways, which fibre type is responsible for the initial sharp 'first pain'?",
        "options": {
            "A": "C fibres",
            "B": "A\u03b2 fibres",
            "C": "A\u03b4 fibres",
            "D": "A\u03b1 fibres",
            "E": "B fibres",
        },
        "answer": "C",
        "explanation": "First (sharp, well-localised) pain is transmitted by thinly myelinated A\u03b4 fibres (5\u201330 m/s). Second (dull, diffuse, burning) pain is transmitted by unmyelinated C fibres (0.5\u20132 m/s). A\u03b2 fibres transmit touch/proprioception and are implicated in the gate control theory of pain (can modulate C fibre input at the dorsal horn).",
    },
    {
        "id": "phar006", "topic": "Pharmacology",
        "question": "Which of the following best describes the mechanism of action of propofol?",
        "options": {
            "A": "Agonist at NMDA receptors",
            "B": "Positive allosteric modulator of GABA-A receptors",
            "C": "Antagonist at nicotinic acetylcholine receptors",
            "D": "Agonist at mu-opioid receptors",
            "E": "Inhibitor of voltage-gated sodium channels",
        },
        "answer": "B",
        "explanation": "Propofol potentiates GABA-A receptor activity by binding to a specific site (distinct from benzodiazepines and barbiturates), increasing the duration of Cl\u207b channel opening. This produces CNS depression. At higher concentrations it may also have direct agonist activity. It does NOT act on NMDA receptors (unlike ketamine).",
    },
    {
        "id": "phar007", "topic": "Pharmacology",
        "question": "What is the context-sensitive half-time of remifentanil after a 4-hour infusion?",
        "options": {
            "A": "240 minutes",
            "B": "60 minutes",
            "C": "30 minutes",
            "D": "3\u20135 minutes",
            "E": "It increases linearly with infusion duration",
        },
        "answer": "D",
        "explanation": "Remifentanil has a context-sensitive half-time of approximately 3\u20135 minutes regardless of infusion duration, due to rapid metabolism by non-specific plasma and tissue esterases (not pseudo-cholinesterase). This makes it unique among opioids and ideal for TIVA/procedures requiring rapid offset, but requires a multimodal analgesic plan as there is no residual analgesia.",
    },
    {
        "id": "phar008", "topic": "Pharmacology",
        "question": "Regarding suxamethonium, which statement is correct?",
        "options": {
            "A": "It is a competitive antagonist at nicotinic receptors",
            "B": "It is metabolised by acetylcholinesterase at the neuromuscular junction",
            "C": "Dibucaine number of 20 indicates atypical pseudocholinesterase with prolonged block",
            "D": "It cannot cause hyperkalaemia in healthy patients",
            "E": "Neostigmine reverses its block effectively",
        },
        "answer": "C",
        "explanation": "Suxamethonium is a depolarising NMB hydrolysed by plasma pseudocholinesterase. Dibucaine inhibits normal pseudocholinesterase by ~80% (dibucaine number 80) but only ~20% of atypical enzyme \u2014 a dibucaine number of 20 indicates homozygous atypical enzyme, causing prolonged block of 2\u20133 hours. Neostigmine does NOT reverse Phase I block and may worsen it. Suxamethonium can cause dangerous hyperkalaemia (+0.5\u20131 mmol/L normally; dangerous in burns, denervation, UMN lesions).",
    },
    {
        "id": "phar009", "topic": "Pharmacology",
        "question": "Which of the following correctly describes the pharmacokinetics of thiopental?",
        "options": {
            "A": "Short duration of action due to rapid hepatic metabolism",
            "B": "Short duration of action due to redistribution from brain to muscle and fat",
            "C": "Elimination half-life of 5 minutes",
            "D": "It does not accumulate with repeated dosing",
            "E": "Highly ionised at physiological pH",
        },
        "answer": "B",
        "explanation": "Thiopental's short clinical duration (5\u201310 min after single dose) is due to rapid redistribution from the brain (high blood flow) to muscle then fat \u2014 not metabolism. Elimination half-life is 5\u201312 hours. It is highly lipid soluble and protein bound, and accumulates with repeated dosing (context-sensitive half-time increases markedly), making it unsuitable for infusions. It is highly unionised at physiological pH (~60% un-ionised), facilitating CNS penetration.",
    },
    {
        "id": "phar010", "topic": "Pharmacology",
        "question": "What is the primary mechanism of ketamine's analgesic action?",
        "options": {
            "A": "Mu-opioid receptor agonism",
            "B": "GABA-A receptor potentiation",
            "C": "NMDA receptor antagonism",
            "D": "Alpha-2 adrenoceptor agonism",
            "E": "Sodium channel blockade",
        },
        "answer": "C",
        "explanation": "Ketamine's primary mechanism is non-competitive antagonism of NMDA receptors (blocking the PCP site within the open channel). This produces dissociative anaesthesia, analgesia, and bronchodilation. It also has some opioid, muscarinic, monoaminergic, and Na\u207a channel effects. Its sympathomimetic properties (bronchodilation, \u2191HR, \u2191BP) are centrally mediated.",
    },
    {
        "id": "phar011", "topic": "Pharmacology",
        "question": "Regarding neostigmine, which statement is TRUE?",
        "options": {
            "A": "It crosses the blood-brain barrier readily",
            "B": "It reverses neuromuscular blockade by directly competing with NMBs at the receptor",
            "C": "Muscarinic side effects should be prevented with an anticholinergic agent",
            "D": "It should not be given with sugammadex",
            "E": "It is effective at reversing Phase I suxamethonium block",
        },
        "answer": "C",
        "explanation": "Neostigmine inhibits acetylcholinesterase, increasing ACh at all cholinergic synapses \u2014 nicotinic (NMJ) and muscarinic. Muscarinic effects (bradycardia, bronchospasm, increased secretions, gut motility) require glycopyrrolate (or atropine) co-administration. It does NOT cross the BBB (quaternary amine). It does not directly compete with NMBs \u2014 it raises ACh to outcompete them. It worsens Phase I suxamethonium block.",
    },
    {
        "id": "phar012", "topic": "Pharmacology",
        "question": "What is the minimum alveolar concentration (MAC) of sevoflurane in a 40-year-old adult?",
        "options": {
            "A": "0.75%",
            "B": "1.15%",
            "C": "2.05%",
            "D": "6.0%",
            "E": "1.8%",
        },
        "answer": "C",
        "explanation": "MAC of sevoflurane is approximately 2.05% in a 40-year-old adult in oxygen. MAC is the alveolar concentration at which 50% of patients do not move to a surgical skin incision. MAC decreases with age (~6% per decade after 40), increases with hyperthermia, chronic alcohol use, and hypernatraemia; decreases with hypothermia, opioids, pregnancy, and nitrous oxide (MAC is additive).",
    },
    {
        "id": "phar013", "topic": "Pharmacology",
        "question": "Which volatile agent is MOST associated with compound A production and potential nephrotoxicity?",
        "options": {
            "A": "Isoflurane",
            "B": "Desflurane",
            "C": "Sevoflurane",
            "D": "Halothane",
            "E": "Enflurane",
        },
        "answer": "C",
        "explanation": "Sevoflurane reacts with soda lime/Baralyme to produce compound A (fluoromethyl-2,2-difluoro-1-[trifluoromethyl]vinyl ether), which is nephrotoxic in rats. In humans, clinical nephrotoxicity has not been demonstrated in normal patients, though low-flow (<1 L/min) sevoflurane is avoided in patients with pre-existing renal disease as a precaution.",
    },
    {
        "id": "phar014", "topic": "Pharmacology",
        "question": "Morphine 6-glucuronide (M6G) is clinically significant because:",
        "options": {
            "A": "It is pharmacologically inactive and responsible for nausea",
            "B": "It is an active metabolite more potent than morphine and accumulates in renal failure",
            "C": "It is responsible for histamine release from mast cells",
            "D": "It is the primary analgesic moiety of morphine",
            "E": "It undergoes enterohepatic circulation causing prolonged action",
        },
        "answer": "B",
        "explanation": "M6G is an active metabolite of morphine with greater mu-receptor affinity and potency than morphine itself. It accumulates in renal failure (as it is renally excreted), causing prolonged and unpredictable respiratory depression, sedation, and analgesia. This is why morphine must be used with caution/avoided in renal impairment, and why alfentanil or fentanyl (inactive metabolites) are preferred.",
    },
    {
        "id": "phar015", "topic": "Pharmacology",
        "question": "Regarding local anaesthetic toxicity, which statement is MOST accurate?",
        "options": {
            "A": "CNS toxicity always precedes cardiovascular toxicity with all local anaesthetics",
            "B": "Bupivacaine is safer than lidocaine in cardiac toxicity as it has faster dissociation kinetics",
            "C": "20% intralipid is the first-line treatment for LA systemic toxicity",
            "D": "Cardiovascular collapse from bupivacaine may precede neurological symptoms",
            "E": "Maximum safe dose of bupivacaine with adrenaline is 4 mg/kg",
        },
        "answer": "D",
        "explanation": "With bupivacaine (and other highly protein-bound, high-pKa LAs), cardiovascular collapse can occur with little or no preceding CNS warning, due to high lipophilicity and slow dissociation from cardiac Na\u207a channels ('fast in, slow out'). Lidocaine dissociates faster. Intralipid 20% is indicated for severe LA toxicity (not first-line for mild CNS toxicity). Max bupivacaine with adrenaline is 2 mg/kg.",
    },
    {
        "id": "phar016", "topic": "Pharmacology",
        "question": "What is the mechanism by which sugammadex reverses rocuronium blockade?",
        "options": {
            "A": "Inhibition of acetylcholinesterase at the NMJ",
            "B": "Direct competition with rocuronium at nicotinic receptors",
            "C": "Encapsulation of rocuronium molecules in a cyclodextrin ring, removing them from the NMJ",
            "D": "Enhancement of acetylcholine release from motor nerve terminals",
            "E": "Activation of plasma cholinesterase to break down rocuronium",
        },
        "answer": "C",
        "explanation": "Sugammadex is a modified gamma-cyclodextrin that encapsulates steroidal NMBs (rocuronium > vecuronium) in a 1:1 ratio within its hydrophobic core, creating a concentration gradient that draws rocuronium away from the NMJ. The complex is renally excreted. It can reverse profound block (even immediately post-intubation at 16 mg/kg) and does not require anticholinergic co-administration.",
    },
    {
        "id": "phar017", "topic": "Pharmacology",
        "question": "Which opioid is most appropriate for a patient with renal failure requiring analgesia?",
        "options": {
            "A": "Morphine",
            "B": "Codeine",
            "C": "Tramadol",
            "D": "Alfentanil",
            "E": "Dihydrocodeine",
        },
        "answer": "D",
        "explanation": "Alfentanil (and fentanyl) are preferred in renal failure as they are metabolised to inactive metabolites that are not renally excreted. Morphine accumulates (active M6G), codeine can cause severe toxicity (accumulation of active metabolites), tramadol accumulates (active O-desmethyl tramadol), and dihydrocodeine has similar risks to codeine. Hydromorphone is another option.",
    },
    {
        "id": "phar018", "topic": "Pharmacology",
        "question": "Regarding the pharmacology of dexmedetomidine, which statement is correct?",
        "options": {
            "A": "It is a non-selective alpha-adrenoceptor agonist",
            "B": "It produces anaesthesia via GABA-A receptor potentiation",
            "C": "It provides sedation without respiratory depression at usual doses",
            "D": "Bradycardia is an uncommon side effect",
            "E": "It has no analgesic properties",
        },
        "answer": "C",
        "explanation": "Dexmedetomidine is a highly selective alpha-2 adrenoceptor agonist (alpha-2:alpha-1 ratio 1600:1, cf. clonidine 200:1). Its sedation is mediated via locus coeruleus alpha-2 receptors, producing a natural sleep-like state. Unlike other sedatives, it causes minimal respiratory depression at clinical doses. Bradycardia and hypotension are common (predictable pharmacological effects). It has significant analgesic and opioid-sparing properties.",
    },
    {
        "id": "phar019", "topic": "Pharmacology",
        "question": "Which of the following correctly describes the 'ceiling effect' relevant to anaesthetic practice?",
        "options": {
            "A": "Morphine has a ceiling effect for respiratory depression but not analgesia",
            "B": "Buprenorphine has a ceiling effect for analgesia but not respiratory depression",
            "C": "NSAIDs have no ceiling effect for analgesia",
            "D": "Paracetamol has no ceiling effect for analgesia",
            "E": "Buprenorphine has a ceiling effect for respiratory depression but not analgesia at low doses",
        },
        "answer": "E",
        "explanation": "Buprenorphine is a partial mu-opioid agonist with a ceiling effect for respiratory depression (but not for analgesia at analgesic doses). This makes it relatively safer than full agonists in overdose. NSAIDs and paracetamol both have ceiling effects for analgesia. Full opioids (morphine, fentanyl) have no ceiling for either analgesia or respiratory depression.",
    },
    {
        "id": "phar020", "topic": "Pharmacology",
        "question": "Which volatile agent has the LOWEST blood:gas partition coefficient?",
        "options": {
            "A": "Halothane (2.4)",
            "B": "Isoflurane (1.4)",
            "C": "Sevoflurane (0.65)",
            "D": "Desflurane (0.42)",
            "E": "Enflurane (1.8)",
        },
        "answer": "D",
        "explanation": "Desflurane has the lowest blood:gas partition coefficient of currently used agents (0.42), meaning it equilibrates rapidly between alveolar gas and blood \u2014 resulting in rapid onset and offset of anaesthesia. Sevoflurane (0.65) has similar properties. Halothane (2.4) has a high coefficient, meaning slow equilibration. Low coefficient = faster onset/offset = more controllable depth of anaesthesia.",
    },
    {
        "id": "phar021", "topic": "Pharmacology",
        "question": "Regarding aspirin, which statement is correct?",
        "options": {
            "A": "It reversibly inhibits COX-1 and COX-2",
            "B": "Its antiplatelet effect lasts 24 hours",
            "C": "It irreversibly acetylates COX, with antiplatelet effect lasting the platelet lifespan (~7\u201310 days)",
            "D": "It preferentially inhibits COX-2 at antiplatelet doses",
            "E": "It has no effect on thromboxane A2 production",
        },
        "answer": "C",
        "explanation": "Aspirin irreversibly acetylates and inhibits both COX-1 and COX-2. In platelets (which lack nuclei and cannot synthesise new enzyme), this permanently abolishes TXA2 production for the platelet's lifespan (7\u201310 days). At low doses (75 mg), it preferentially inhibits platelet COX-1 (TXA2 synthesis) over vascular endothelial COX-2 (PGI2 synthesis), providing a net antithrombotic effect.",
    },
    {
        "id": "phar022", "topic": "Pharmacology",
        "question": "What is the mechanism of ondansetron's antiemetic action?",
        "options": {
            "A": "Dopamine D2 antagonism in the chemoreceptor trigger zone",
            "B": "Histamine H1 antagonism in the vomiting centre",
            "C": "Serotonin 5-HT3 antagonism in the vagus nerve and CTZ",
            "D": "Muscarinic M1 antagonism in the vestibular nucleus",
            "E": "Neurokinin NK1 antagonism",
        },
        "answer": "C",
        "explanation": "Ondansetron is a selective 5-HT3 receptor antagonist. It acts peripherally (on vagal afferents in the GI tract and nucleus tractus solitarius) and centrally (in the chemoreceptor trigger zone). NK1 antagonists (aprepitant) and D2 antagonists (metoclopramide, droperidol) work by different mechanisms. Multi-modal antiemesis using different mechanisms is more effective than single-agent therapy.",
    },
    {
        "id": "phar023", "topic": "Pharmacology",
        "question": "Which of the following is a pharmacological effect of nitrous oxide?",
        "options": {
            "A": "Potent muscle relaxation",
            "B": "Inhibition of NMDA receptors and mild analgesia",
            "C": "Hepatotoxicity via trifluoroacetyl metabolites",
            "D": "Profound respiratory depression",
            "E": "Malignant hyperthermia trigger",
        },
        "answer": "B",
        "explanation": "N\u2082O is an NMDA receptor antagonist with analgesic (equivalent to ~10 mg morphine IM) and weak anaesthetic properties (MAC 105%, so cannot produce anaesthesia alone at atmospheric pressure). It causes minimal cardiovascular and respiratory depression. Hepatotoxicity via trifluoroacetyl metabolites is a feature of halothane. N\u2082O is not a MH trigger (only volatile agents and suxamethonium are).",
    },
    {
        "id": "phar024", "topic": "Pharmacology",
        "question": "Regarding metaraminol, which statement is correct?",
        "options": {
            "A": "It is a pure alpha-1 agonist with no beta activity",
            "B": "It acts by releasing noradrenaline from sympathetic nerve terminals and direct receptor agonism",
            "C": "It causes significant tachycardia via beta-1 stimulation",
            "D": "It reduces uteroplacental blood flow and is safe in obstetric hypotension",
            "E": "Phenylephrine has superior evidence to metaraminol in obstetric practice",
        },
        "answer": "B",
        "explanation": "Metaraminol acts via both direct alpha-1 (and weak beta) agonism and indirect release of stored noradrenaline from sympathetic terminals. It causes vasoconstriction with reflex bradycardia (not tachycardia). In obstetric spinal hypotension, phenylephrine (pure alpha-1) was historically preferred to preserve uteroplacental flow, but recent evidence shows metaraminol is equally safe and effective, and is now widely used in the UK.",
    },
    {
        "id": "phar025", "topic": "Pharmacology",
        "question": "Which of the following regarding magnesium sulphate is correct?",
        "options": {
            "A": "It acts as a calcium channel agonist",
            "B": "It potentiates non-depolarising neuromuscular blockade",
            "C": "Therapeutic levels are 0.5\u20131 mmol/L",
            "D": "Toxicity monitoring requires ECG only",
            "E": "It is contraindicated in eclampsia",
        },
        "answer": "B",
        "explanation": "Magnesium is a physiological calcium antagonist and NMDA antagonist. It potentiates both depolarising and non-depolarising NMBs \u2014 NMB doses should be reduced and TOF monitoring is essential. Therapeutic levels for eclampsia prophylaxis are 2\u20134 mmol/L. Toxicity signs: loss of patellar reflex (4\u20135 mmol/L), respiratory depression (5\u20136 mmol/L), cardiac arrest (>7.5 mmol/L). Calcium gluconate is the antidote. It is first-line treatment and prophylaxis for eclampsia.",
    },
    {
        "id": "phys006", "topic": "Physics & Clinical Measurement",
        "question": "Which of the following best describes the Doppler effect as applied to cardiac output measurement?",
        "options": {
            "A": "Sound waves are reflected off red blood cells; the frequency shift is proportional to velocity",
            "B": "Electrical impedance across the chest changes with cardiac output",
            "C": "Dye dilution measures the washout curve of injected dye",
            "D": "Oesophageal pressure changes reflect left ventricular filling",
            "E": "Pulse pressure variation during mechanical ventilation correlates with fluid responsiveness",
        },
        "answer": "A",
        "explanation": "The Doppler effect is used in oesophageal Doppler and echocardiography: ultrasound waves are reflected off moving red blood cells. The frequency shift (\u0394f) is proportional to blood velocity by the Doppler equation: \u0394f = 2f\u2080v\u00b7cos\u03b8/c. Measuring velocity in the descending aorta and knowing aortic cross-sectional area allows stroke volume and CO calculation.",
    },
    {
        "id": "phys007", "topic": "Physics & Clinical Measurement",
        "question": "What does a critically damped arterial line waveform indicate?",
        "options": {
            "A": "The transducer is positioned too high",
            "B": "Excessive damping causing underestimation of systolic and overestimation of diastolic pressure",
            "C": "The waveform is accurate and optimal for clinical use",
            "D": "Air bubbles are causing over-amplification of systolic pressure",
            "E": "The natural frequency of the system is too high",
        },
        "answer": "B",
        "explanation": "Critical damping (coefficient ~1.0) causes the system to return to baseline slowly without oscillation \u2014 losing the fine detail of the arterial waveform. This underestimates systolic and overestimates diastolic pressure (mean BP is relatively preserved). Causes include kinked tubing, soft tubing, blood clot, or compliant connections. Optimal damping coefficient is 0.64 (slightly underdamped). Air bubbles cause underdamping with systolic overshoot.",
    },
    {
        "id": "phys008", "topic": "Physics & Clinical Measurement",
        "question": "Regarding the Mapleson breathing systems, which correctly describes the Mapleson A system (Magill circuit)?",
        "options": {
            "A": "Most efficient system for controlled ventilation",
            "B": "Most efficient system for spontaneous ventilation, requiring FGF equal to minute ventilation",
            "C": "Most efficient system for spontaneous ventilation only in paediatric patients",
            "D": "Requires FGF of 2\u20133 \u00d7 minute ventilation for spontaneous breathing",
            "E": "The APL valve is at the patient end",
        },
        "answer": "B",
        "explanation": "The Mapleson A (Magill) is most efficient for spontaneous ventilation \u2014 FGF equal to alveolar minute ventilation (~70 mL/kg/min) prevents rebreathing. During expiration, fresh gas fills the reservoir bag while exhaled gas is vented via the APL valve (at the machine end). For controlled ventilation, Mapleson A is the least efficient (FGF of 3\u00d7 MV needed). Mapleson D/Bain is most efficient for controlled ventilation.",
    },
    {
        "id": "phys009", "topic": "Physics & Clinical Measurement",
        "question": "What is the relationship between flow and pressure in laminar flow, as described by the Hagen-Poiseuille equation?",
        "options": {
            "A": "Flow is proportional to the square of the pressure difference",
            "B": "Flow is proportional to the fourth power of the radius",
            "C": "Flow is proportional to the square root of the pressure difference",
            "D": "Flow is inversely proportional to the square of the radius",
            "E": "Flow is proportional to the square of the radius",
        },
        "answer": "B",
        "explanation": "Hagen-Poiseuille: Q = \u03c0\u0394Pr\u2074/8\u03b7l. Flow is proportional to r\u2074 \u2014 halving the radius reduces flow 16-fold. This has profound clinical implications: using the largest bore, shortest IV cannula maximises flow. Turbulent flow (Reynolds number >2000) follows different laws and is proportional to the square root of the pressure difference, with no r\u2074 relationship.",
    },
    {
        "id": "phys010", "topic": "Physics & Clinical Measurement",
        "question": "A patient's capnograph shows an elevated baseline that does not return to zero. What is the MOST likely cause?",
        "options": {
            "A": "Oesophageal intubation",
            "B": "Partial rebreathing of expired CO\u2082",
            "C": "Severe bronchospasm",
            "D": "Malignant hyperthermia",
            "E": "Disconnection of the breathing circuit",
        },
        "answer": "B",
        "explanation": "An elevated capnograph baseline (ETCO\u2082 does not return to zero) indicates CO\u2082 rebreathing, most commonly due to exhausted soda lime (channelling or colour change), a stuck expiratory valve, or insufficient fresh gas flow in a Mapleson circuit. Oesophageal intubation produces a flat trace or rapid fall to zero. Bronchospasm causes a 'shark fin' upslope. MH causes a rising ETCO\u2082 with normal baseline.",
    },
    {
        "id": "phys011", "topic": "Physics & Clinical Measurement",
        "question": "Which method of cardiac output measurement is considered the clinical gold standard?",
        "options": {
            "A": "Oesophageal Doppler",
            "B": "Thermodilution via pulmonary artery catheter",
            "C": "Lithium dilution (LiDCO)",
            "D": "Bioimpedance cardiography",
            "E": "Pulse pressure analysis (PiCCO)",
        },
        "answer": "B",
        "explanation": "Pulmonary artery catheter thermodilution remains the clinical reference standard for CO measurement. Cold saline is injected into the RA; the temperature change in the PA is measured over time. The area under the thermodilution curve (modified Stewart-Hamilton equation) gives CO. Limitations include its invasive nature, risk of complications (arrhythmias, PA rupture), and questions about outcome benefit.",
    },
    {
        "id": "phys012", "topic": "Physics & Clinical Measurement",
        "question": "What is the significance of the 'resonant frequency' of an arterial line measurement system?",
        "options": {
            "A": "It determines the safe working pressure of the pressure transducer",
            "B": "If the natural frequency is close to the harmonic content of the arterial waveform, resonance will amplify the signal",
            "C": "A higher resonant frequency worsens waveform accuracy",
            "D": "It only becomes relevant in paediatric patients",
            "E": "It determines the rate of IV fluid flow through the system",
        },
        "answer": "B",
        "explanation": "The arterial waveform contains harmonics up to ~30 Hz. If the system's natural frequency (fn) is close to these harmonics, resonance amplifies the signal \u2014 causing 'ringing' and systolic overshoot (underdamping). For accurate measurement, fn should be >40 Hz (achieved with short, stiff tubing and minimal connections) with a damping coefficient of ~0.64. This is assessed by the fast-flush test.",
    },
    {
        "id": "phys013", "topic": "Physics & Clinical Measurement",
        "question": "In the context of medical gas cylinders, what does the pressure in a full oxygen cylinder tell you about remaining contents?",
        "options": {
            "A": "Nothing \u2014 oxygen is stored as a liquid so pressure does not reflect volume",
            "B": "Pressure is directly proportional to remaining gas volume",
            "C": "Pressure is inversely proportional to remaining volume",
            "D": "Pressure only reflects temperature, not volume",
            "E": "Oxygen pressure remains constant until the cylinder is nearly empty",
        },
        "answer": "B",
        "explanation": "Oxygen is stored as a compressed gas (not liquid) in cylinders. By Boyle's law, at constant temperature, pressure is directly proportional to remaining volume \u2014 as gas is used, pressure falls proportionally. A full cylinder at 137 bar (pin index size E) contains 680 L; at half pressure, ~340 L remain. Contrast with nitrous oxide: stored as a liquid/gas mixture, pressure remains constant (~44 bar) until liquid is exhausted.",
    },
    {
        "id": "phys014", "topic": "Physics & Clinical Measurement",
        "question": "What is the definition of 'specific gravity' as used in urinalysis and spinal anaesthesia?",
        "options": {
            "A": "The weight of a substance per unit volume at 4\u00b0C",
            "B": "The ratio of the density of a substance to the density of water at the same temperature",
            "C": "The osmolality of a solution measured in mosmol/kg",
            "D": "The viscosity of a solution relative to water",
            "E": "The boiling point of a substance relative to water",
        },
        "answer": "B",
        "explanation": "Specific gravity (SG) is the ratio of a substance's density to water's density at the same temperature (dimensionless). CSF SG is approximately 1.003\u20131.006. Hyperbaric bupivacaine (SG ~1.026) is denser than CSF and sinks under gravity, allowing positioning to direct spread. Hypobaric solutions (SG <1.003) rise in CSF. This is clinically crucial for positioning in spinal anaesthesia.",
    },
    {
        "id": "phys015", "topic": "Physics & Clinical Measurement",
        "question": "Which of the following statements about pulse oximetry is correct?",
        "options": {
            "A": "It uses three wavelengths of light to distinguish oxyhaemoglobin from other species",
            "B": "It is accurate in methemoglobinaemia, reading the true SpO\u2082",
            "C": "It measures the pulsatile absorbance change at 660 nm and 940 nm",
            "D": "Nail polish has no effect on pulse oximetry readings",
            "E": "It accurately measures SpO\u2082 in severe peripheral vasoconstriction",
        },
        "answer": "C",
        "explanation": "Pulse oximetry uses two wavelengths: 660 nm (red \u2014 absorbed more by deoxyHb) and 940 nm (infrared \u2014 absorbed more by oxyHb). The ratio of pulsatile absorbance at these wavelengths is compared to a calibration curve. Methaemoglobin absorbs equally at both wavelengths, causing SpO\u2082 to read approximately 85% regardless of true saturation. Blue/black nail polish can affect readings; green/yellow generally does not. Severe vasoconstriction reduces signal quality.",
    },
    {
        "id": "phys016", "topic": "Physics & Clinical Measurement",
        "question": "What does the Fick principle state in the context of cardiac output measurement?",
        "options": {
            "A": "Cardiac output equals mean arterial pressure divided by systemic vascular resistance",
            "B": "Oxygen consumption equals cardiac output multiplied by the arteriovenous oxygen content difference",
            "C": "Cardiac output equals stroke volume divided by heart rate",
            "D": "Pulmonary blood flow equals alveolar ventilation divided by V/Q ratio",
            "E": "Oxygen delivery equals cardiac output multiplied by arterial oxygen content",
        },
        "answer": "B",
        "explanation": "Fick principle: VO\u2082 = CO \u00d7 (CaO\u2082 \u2212 CvO\u2082). Rearranged: CO = VO\u2082 / (CaO\u2082 \u2212 CvO\u2082). Requires measurement of O\u2082 consumption (Douglas bag or metabolic analyser) and arteriovenous O\u2082 content difference (arterial and mixed venous blood gases). This is the physiological gold standard (cf. thermodilution which is the clinical gold standard). Option E describes the oxygen delivery (DO\u2082) equation, which is related but distinct.",
    },
    {
        "id": "phys017", "topic": "Physics & Clinical Measurement",
        "question": "Regarding the pin index safety system on anaesthetic machines, which gas is identified by pins in positions 2 and 5?",
        "options": {
            "A": "Oxygen",
            "B": "Nitrous oxide",
            "C": "Air",
            "D": "Carbon dioxide",
            "E": "Entonox",
        },
        "answer": "A",
        "explanation": "The pin index system prevents incorrect gas cylinder connection. Oxygen: pins 2 and 5. Nitrous oxide: pins 3 and 5. Air: pins 1 and 5. CO\u2082: pins 1 and 6. Entonox (50:50 O\u2082/N\u2082O): pins 7 only. The yoke has holes corresponding to the pin positions on the specific gas cylinder, preventing cross-connection. Colour coding also applies: oxygen \u2014 black with white shoulders; nitrous oxide \u2014 blue; air \u2014 grey/black.",
    },
    {
        "id": "phys018", "topic": "Physics & Clinical Measurement",
        "question": "What is the clinical significance of the 'iso-electric point' of a volatile agent in a circle breathing system?",
        "options": {
            "A": "The temperature at which a volatile agent vaporises",
            "B": "The concentration at which equal amounts are absorbed and released from rubber components",
            "C": "There is no clinically relevant concept called the iso-electric point for volatiles",
            "D": "The blood:gas partition coefficient",
            "E": "The ratio of inspired to alveolar concentration at steady state",
        },
        "answer": "C",
        "explanation": "The concept referred to in rubber solubility is the equilibrium point where absorption equals release, but 'iso-electric point' is not the correct term for volatiles. The rubber:gas partition coefficient describes solubility in rubber. Desflurane has the lowest rubber solubility, sevoflurane higher. The relevant clinical concept for circle systems is the equilibrium between gas concentration and rubber/soda lime absorption \u2014 but the correct term for this context is the rubber partition coefficient or equilibration, not the iso-electric point.",
    },
    {
        "id": "phys019", "topic": "Physics & Clinical Measurement",
        "question": "What is the MOST important safety feature preventing barotrauma from a gas supply failure in an anaesthetic machine?",
        "options": {
            "A": "The flow control valves",
            "B": "The pressure-reducing valves (regulators) at pipeline and cylinder inlets",
            "C": "The vaporiser interlock system",
            "D": "The oxygen failure alarm",
            "E": "The adjustable pressure-limiting (APL) valve",
        },
        "answer": "B",
        "explanation": "Pipeline gas is supplied at ~400 kPa and cylinder gas at much higher pressures (O\u2082 cylinders at 137 bar = 13,700 kPa). Pressure-reducing valves at inlet reduce these to a working pressure of ~400 kPa (pipelines) or ~420 kPa (cylinders), protecting the machine and patient from high-pressure gas injury. The APL valve limits airway pressure during ventilation but doesn't protect against supply-side pressure surges.",
    },
    {
        "id": "phys020", "topic": "Physics & Clinical Measurement",
        "question": "In a normal spirometry trace, what does the FEV1/FVC ratio indicate?",
        "options": {
            "A": "Total lung capacity as a fraction of vital capacity",
            "B": "The proportion of vital capacity exhaled in the first second",
            "C": "Residual volume as a proportion of TLC",
            "D": "Peak flow as a proportion of FVC",
            "E": "The ratio of functional residual capacity to TLC",
        },
        "answer": "B",
        "explanation": "FEV1/FVC (Tiffeneau index) is the proportion of forced vital capacity exhaled in the first second. Normal is >70\u201375% (>0.7). In obstructive disease (asthma, COPD): FEV1 reduced disproportionately, ratio <0.7. In restrictive disease: both FEV1 and FVC reduced proportionally, ratio normal or elevated (>0.7\u20130.8). This distinction is fundamental to preoperative respiratory assessment.",
    },
    {
        "id": "phys021", "topic": "Physics & Clinical Measurement",
        "question": "What statistical test is most appropriate for comparing the means of two normally distributed continuous variables from independent groups?",
        "options": {
            "A": "Mann-Whitney U test",
            "B": "Chi-squared test",
            "C": "Unpaired t-test",
            "D": "Pearson's correlation coefficient",
            "E": "Fisher's exact test",
        },
        "answer": "C",
        "explanation": "The unpaired (independent samples) t-test compares means of two independent groups when data are normally distributed. Mann-Whitney U is the non-parametric equivalent for non-normally distributed data. Chi-squared and Fisher's exact test are for categorical data. Pearson's correlation measures the linear relationship between two continuous variables. Selecting the correct statistical test is examinable in the Primary FRCA.",
    },
    {
        "id": "phys022", "topic": "Physics & Clinical Measurement",
        "question": "What is the oxygen flush valve on an anaesthetic machine designed to deliver?",
        "options": {
            "A": "100% O\u2082 at 200\u2013700 mL/min",
            "B": "100% O\u2082 at 35\u201375 L/min bypassing the vaporiser",
            "C": "A mixture of O\u2082 and air at 15 L/min",
            "D": "100% O\u2082 at flowmeter-set rate only",
            "E": "100% O\u2082 through the vaporiser at full concentration",
        },
        "answer": "B",
        "explanation": "The oxygen flush valve delivers 100% O\u2082 at 35\u201375 L/min directly to the common gas outlet, bypassing the vaporisers and flowmeters. This rapidly flushes the breathing system with oxygen. Hazards include: barotrauma (high flow during inspiration can cause lung injury), dilution of volatile agent (awareness if used during maintenance), and delivery of undiluted O\u2082 to the patient. It should be used with care with spontaneously breathing patients.",
    },
    {
        "id": "phys023", "topic": "Physics & Clinical Measurement",
        "question": "Which type of error does a p-value of 0.05 threshold aim to control?",
        "options": {
            "A": "Type II error (beta error) \u2014 missing a true difference",
            "B": "Type I error (alpha error) \u2014 falsely concluding a difference exists",
            "C": "Systematic bias",
            "D": "Measurement error",
            "E": "Selection bias",
        },
        "answer": "B",
        "explanation": "A p-value threshold of 0.05 means we accept a 5% probability of committing a Type I error (alpha error) \u2014 incorrectly rejecting the null hypothesis when it is true (false positive). Type II error (beta error) \u2014 failing to detect a real difference (false negative) \u2014 is controlled by sample size/power calculations. Power = 1 \u2212 \u03b2; a study with 80% power has a 20% risk of a Type II error.",
    },
    {
        "id": "phys024", "topic": "Physics & Clinical Measurement",
        "question": "Which temperature measurement method is most accurate for reflecting core temperature?",
        "options": {
            "A": "Axillary temperature",
            "B": "Tympanic infrared measurement",
            "C": "Nasopharyngeal thermistor",
            "D": "Pulmonary artery temperature",
            "E": "Urinary bladder temperature",
        },
        "answer": "D",
        "explanation": "Pulmonary artery temperature (via PAC) is the true gold standard for core temperature as it measures mixed venous blood temperature at the heart. In routine anaesthetic practice, nasopharyngeal (close to carotid blood supply) and oesophageal temperatures best reflect core temperature. Tympanic probes show good correlation if correctly placed. Axillary underestimates; rectal lags behind changes.",
    },
    {
        "id": "phys025", "topic": "Physics & Clinical Measurement",
        "question": "What is the 'time constant' of an exponential process (e.g. lung emptying in a ventilated patient)?",
        "options": {
            "A": "The time for 100% of the process to complete",
            "B": "The time for 50% of the process to complete",
            "C": "The product of resistance and compliance, representing time for 63% of the process",
            "D": "The half-life of the process",
            "E": "The time to reach peak pressure",
        },
        "answer": "C",
        "explanation": "The time constant (\u03c4) = R \u00d7 C (resistance \u00d7 compliance). After one \u03c4, 63% of the process is complete; after 2\u03c4, 86%; after 3\u03c4, 95%; after 5\u03c4, ~99% (effectively complete). In respiratory mechanics, \u03c4 governs lung emptying: long \u03c4 means slow emptying (e.g. COPD with high resistance), risking gas trapping if expiratory time is insufficient. Normal \u03c4 ~0.2\u20130.5 s.",
    },
    {
        "id": "clin006", "topic": "Clinical Anaesthesia",
        "question": "A 35-year-old woman with known latex allergy presents for laparoscopic cholecystectomy. Which of the following measures is MOST important?",
        "options": {
            "A": "Premedication with chlorphenamine alone",
            "B": "Avoiding all latex-containing equipment and ensuring a latex-free environment",
            "C": "Informing the patient that their risk is low with modern latex-low gloves",
            "D": "Scheduling the case last on the list to minimise exposure",
            "E": "Administering prophylactic hydrocortisone intraoperatively",
        },
        "answer": "B",
        "explanation": "The most important measure is complete avoidance of all latex-containing equipment (gloves, catheters, IV ports, airway equipment). Latex-allergic patients should be scheduled first on the list (not last) to minimise ambient latex particles from previous cases. Premedication with antihistamines/steroids reduces reaction severity but does NOT prevent anaphylaxis and should not replace avoidance.",
    },
    {
        "id": "clin007", "topic": "Clinical Anaesthesia",
        "question": "During a rapid sequence induction, cricoid pressure (Sellick's manoeuvre) is applied. What force should be applied?",
        "options": {
            "A": "10 N (approximately 1 kg)",
            "B": "30 N (approximately 3 kg) before induction, 44 N after loss of consciousness",
            "C": "60 N throughout",
            "D": "10 N before induction, increasing to 30 N after",
            "E": "Pressure should be applied until the cuff is inflated, regardless of force",
        },
        "answer": "B",
        "explanation": "Current evidence supports: 10 N applied before induction (to warn the patient), increasing to 30 N after loss of consciousness (equivalent to ~3 kg \u2014 enough to occlude the oesophagus without distorting the airway), and releasing once the cuff is inflated and position confirmed. 44 N may be applied if regurgitation is actively occurring. Excessive force can obstruct the airway and impede intubation.",
    },
    {
        "id": "clin008", "topic": "Clinical Anaesthesia",
        "question": "What is the MOST appropriate initial management of suspected malignant hyperthermia intraoperatively?",
        "options": {
            "A": "Increase fresh gas flow and give IV paracetamol",
            "B": "Stop all triggering agents, call for help, give dantrolene 2.5 mg/kg IV, active cooling",
            "C": "Give dantrolene 1 mg/kg and await response before further action",
            "D": "Give sodium bicarbonate and surface cooling only",
            "E": "Change to a propofol TIVA and continue the case",
        },
        "answer": "B",
        "explanation": "MH is a rare but life-threatening pharmacogenetic disorder triggered by volatile anaesthetics and suxamethonium. Management: stop trigger agents immediately, call for help, hyperventilate with 100% O\u2082 at maximum fresh gas flow, give dantrolene 2.5 mg/kg IV (repeat every 5 min to max 10 mg/kg), active cooling, treat hyperkalaemia and acidosis, continue monitoring in ICU. Dantrolene inhibits SR Ca\u00b2\u207a release via RyR1 receptor.",
    },
    {
        "id": "clin009", "topic": "Clinical Anaesthesia",
        "question": "Which nerve is at greatest risk during a posterior triangle lymph node biopsy?",
        "options": {
            "A": "Phrenic nerve",
            "B": "Recurrent laryngeal nerve",
            "C": "Accessory nerve (CN XI)",
            "D": "Hypoglossal nerve",
            "E": "Vagus nerve",
        },
        "answer": "C",
        "explanation": "The accessory nerve (CN XI) crosses the posterior triangle of the neck superficially, passing from the anterior border of SCM to the anterior border of trapezius. It is at high risk during posterior triangle dissection, lymph node biopsy, or neck dissection. Injury causes weakness of trapezius (shoulder drop, inability to shrug, winging of scapula) and SCM. The phrenic nerve is at risk in anterior triangle surgery.",
    },
    {
        "id": "clin010", "topic": "Clinical Anaesthesia",
        "question": "A patient has a known grade 3 Cormack-Lehane view at direct laryngoscopy. Which is the MOST appropriate plan for a repeat anaesthetic?",
        "options": {
            "A": "Proceed with direct laryngoscopy using a standard Macintosh blade",
            "B": "Cancel the case until an ENT surgeon is available for awake tracheotomy",
            "C": "Plan awake fibreoptic intubation as the primary technique",
            "D": "Use a video laryngoscope as a primary technique with a plan B of awake FOI",
            "E": "Pre-oxygenate for 5 minutes and perform standard RSI",
        },
        "answer": "D",
        "explanation": "Cormack-Lehane grade 3 (only epiglottis visible) indicates a difficult airway. The 2015 DAS guidelines recommend videolaryngoscopy as the primary technique for anticipated difficult intubation in non-emergency cases (better glottic view in most cases). Awake fibreoptic intubation is preferred when there are additional concerns (obstructive pathology, cervical instability, high aspiration risk, predicted impossible mask ventilation). A plan B must always be formulated.",
    },
    {
        "id": "clin011", "topic": "Clinical Anaesthesia",
        "question": "What is the MOST common cause of perioperative anaphylaxis in the UK?",
        "options": {
            "A": "Latex",
            "B": "Antibiotics (penicillin)",
            "C": "Neuromuscular blocking agents",
            "D": "Colloids (gelatin)",
            "E": "Chlorhexidine",
        },
        "answer": "C",
        "explanation": "Neuromuscular blocking agents (NMBAs) account for approximately 50\u201360% of perioperative anaphylaxis cases in the UK (AAGBI/NAP6 data). Antibiotics are second (20\u201330%), followed by latex, chlorhexidine, and colloids. Cross-reactivity between NMBAs occurs due to the quaternary ammonium group. Skin testing and allergy investigation should be performed after any suspected reaction.",
    },
    {
        "id": "clin012", "topic": "Clinical Anaesthesia",
        "question": "In a patient developing anaphylaxis under anaesthesia, what is the first-line drug and dose?",
        "options": {
            "A": "Hydrocortisone 200 mg IV",
            "B": "Chlorphenamine 10 mg IV",
            "C": "Adrenaline 50\u2013100 mcg IV (titrated), or 500 mcg IM if no IV access",
            "D": "Adrenaline 1 mg IV bolus",
            "E": "Salbutamol 2.5 mg nebulised",
        },
        "answer": "C",
        "explanation": "Adrenaline is the first-line treatment for anaphylaxis. IV administration allows titration: 50 mcg (0.5 mL of 1:10,000) boluses repeated every 1\u20132 min, with an infusion if repeated boluses required. IM adrenaline 500 mcg (0.5 mL of 1:1000) into the lateral thigh is used if no IV access. 1 mg IV bolus is for cardiac arrest only \u2014 in a conscious or semi-conscious patient this dose causes severe hypertension and arrhythmias.",
    },
    {
        "id": "clin013", "topic": "Clinical Anaesthesia",
        "question": "Which of the following is an absolute contraindication to spinal anaesthesia?",
        "options": {
            "A": "Prior back surgery at a different level",
            "B": "Patient refusal",
            "C": "Age over 80",
            "D": "Mild aortic stenosis",
            "E": "Diabetes mellitus",
        },
        "answer": "B",
        "explanation": "Patient refusal is an absolute contraindication to any anaesthetic technique \u2014 valid informed consent is required. Other absolute contraindications include: patient refusal, infection at the injection site, true allergy to LA, raised intracranial pressure (risk of coning with CSF loss), severe coagulopathy. Relative contraindications include: anticoagulation, fixed cardiac output states (severe AS), pre-existing neurological disease, hypovolaemia.",
    },
    {
        "id": "clin014", "topic": "Clinical Anaesthesia",
        "question": "What is the maximum safe dose of intralipid 20% in LA toxicity treatment?",
        "options": {
            "A": "1.5 mL/kg bolus only, no infusion",
            "B": "Initial bolus 1.5 mL/kg over 1 min, then infusion 0.25 mL/kg/min, max cumulative dose 12 mL/kg",
            "C": "10 mL/kg over 30 minutes",
            "D": "5 mL/kg as a single bolus, repeatable once",
            "E": "0.5 mL/kg/hr continuous infusion until recovery",
        },
        "answer": "B",
        "explanation": "AAGBI guidelines for LA toxicity: initial bolus of 20% intralipid 1.5 mL/kg IV over 1 min, followed by an infusion at 0.25 mL/kg/min. If cardiovascular stability is not achieved, repeat the bolus up to twice more at 5 min intervals, then double the infusion rate to 0.5 mL/kg/min. Maximum cumulative dose: 12 mL/kg. Continue CPR throughout; propofol is NOT a substitute for intralipid.",
    },
    {
        "id": "clin015", "topic": "Clinical Anaesthesia",
        "question": "A 72-year-old man presents for elective right hemicolectomy. He takes warfarin for AF. His INR is 2.8. What is the MOST appropriate management?",
        "options": {
            "A": "Proceed with surgery and reverse with vitamin K only if excessive bleeding occurs",
            "B": "Give FFP 4 units preoperatively to reduce INR",
            "C": "Stop warfarin and bridge with low molecular weight heparin, targeting INR <1.5 on day of surgery",
            "D": "Cancel the case indefinitely",
            "E": "Give vitamin K 1 mg IV the night before and proceed next morning",
        },
        "answer": "C",
        "explanation": "For elective major surgery with significant bleeding risk, warfarin should be stopped 5 days pre-op. For high thromboembolic risk (AF with CHA\u2082DS\u2082-VASc \u22655, mechanical heart valves, recent VTE), bridging with LMWH is appropriate. Target INR <1.5 (some centres <2.0 for low-risk surgery). FFP is not appropriate for elective reversal. The decision to bridge should be individualised with haematology input.",
    },
    {
        "id": "clin016", "topic": "Clinical Anaesthesia",
        "question": "What volume of blood does a 4\u00d74 cm gauze swab hold when fully soaked?",
        "options": {
            "A": "5 mL",
            "B": "10 mL",
            "C": "15 mL",
            "D": "25 mL",
            "E": "50 mL",
        },
        "answer": "B",
        "explanation": "A standard 4\u00d74 cm gauze swab (surgical swab) holds approximately 10 mL of blood when fully soaked. Larger surgical swabs (10\u00d710 cm) hold approximately 100\u2013150 mL. Accurate intraoperative blood loss estimation requires counting swabs, weighing (1 g \u2248 1 mL blood), and measuring suction losses. Surgical swab counting is also a WHO safety checklist item to prevent retained surgical items.",
    },
    {
        "id": "clin017", "topic": "Clinical Anaesthesia",
        "question": "Which of the following best describes the obturator nerve and its clinical relevance to the anaesthetist?",
        "options": {
            "A": "It arises from L2-L4 and adducts the thigh; stimulation during TURBT causes obturator reflex",
            "B": "It arises from L4-S2 and supplies the gluteal region",
            "C": "It provides sensory supply to the knee joint only",
            "D": "It is the primary nerve blocked in femoral nerve block",
            "E": "It passes through the greater sciatic foramen",
        },
        "answer": "A",
        "explanation": "The obturator nerve (L2-L4) exits the pelvis through the obturator foramen, supplying the adductor compartment of the thigh. During TURBT of lateral bladder wall tumours, monopolar diathermy stimulates the obturator nerve causing sudden violent adductor contraction (obturator reflex), risking bladder perforation. Prevention: spinal anaesthesia, muscle relaxation under GA, or obturator nerve block. The nerve also supplies the hip and medial knee joint.",
    },
    {
        "id": "clin018", "topic": "Clinical Anaesthesia",
        "question": "Regarding the management of a 'can't intubate, can't oxygenate' (CICO) scenario, what is the correct sequence?",
        "options": {
            "A": "Continue attempting bag-mask ventilation indefinitely",
            "B": "Call for senior help, attempt supraglottic airway, then proceed to front-of-neck access (FONA)",
            "C": "Immediately proceed to percutaneous tracheostomy",
            "D": "Administer suxamethonium to facilitate spontaneous ventilation",
            "E": "Perform retrograde intubation as the first rescue technique",
        },
        "answer": "B",
        "explanation": "The 2015 DAS difficult airway guidelines for CICO: declare emergency (call for help), attempt supraglottic airway (LMA/ILMA) as a bridge, if unsuccessful proceed immediately to front-of-neck access (FONA) \u2014 scalpel cricothyroidotomy is the fastest, most reliable technique. Do not delay FONA with multiple failed airway attempts ('can't intubate' + 'can't oxygenate' = proceed to FONA). Time-critical: hypoxic cardiac arrest follows within minutes.",
    },
    {
        "id": "clin019", "topic": "Clinical Anaesthesia",
        "question": "A 28-year-old parturient requires emergency caesarean section for fetal bradycardia. She has no epidural in situ. The MOST appropriate anaesthetic technique is:",
        "options": {
            "A": "Spinal anaesthesia if possible, or general anaesthesia if spinal is not possible within an acceptable time frame",
            "B": "General anaesthesia in all cases as it is fastest",
            "C": "Epidural top-up as this is safest",
            "D": "Spinal anaesthesia in all cases as it is safest",
            "E": "Sedation with regional anaesthesia",
        },
        "answer": "A",
        "explanation": "Spinal anaesthesia is preferred for Category 1 LSCS if it can be performed without unacceptable delay \u2014 it avoids the risks of GA in the obstetric airway (Mendelson's, difficult intubation) and provides excellent analgesia. However, if time does not allow (genuine immediate threat to life), GA with RSI is the appropriate alternative. The decision requires communication between obstetrician and anaesthetist about urgency. RCOA guidelines support both depending on clinical urgency.",
    },
    {
        "id": "clin020", "topic": "Clinical Anaesthesia",
        "question": "What is the recommended approach to pre-oxygenation before RSI in an adult?",
        "options": {
            "A": "4 deep breaths of 100% O\u2082 over 30 seconds with a tight-fitting mask",
            "B": "3 minutes of tidal volume breathing of 100% O\u2082 via tight-fitting mask, or 8 vital capacity breaths",
            "C": "1 minute of normal breathing on the anaesthetic circuit",
            "D": "2 minutes of breathing on a non-rebreathing mask",
            "E": "High-flow nasal oxygen alone (15 L/min) for 3 minutes",
        },
        "answer": "B",
        "explanation": "Optimal pre-oxygenation: 3 minutes of normal tidal breathing of 100% O\u2082 via a tight-fitting facemask (FGF \u226510 L/min), or 8 vital capacity breaths in 60 seconds. Target ETO\u2082 >90%. This replaces nitrogen in the FRC with oxygen, extending the apnoea safe period from ~1 min to ~8 min in healthy adults. Obese, pregnant, and paediatric patients have reduced FRC and desaturate faster. High-flow nasal O\u2082 (apnoeic oxygenation) may be used as an adjunct but not a replacement.",
    },
    {
        "id": "clin021", "topic": "Clinical Anaesthesia",
        "question": "Which of the following is a recognised risk factor for postoperative nausea and vomiting (PONV) according to the Apfel score?",
        "options": {
            "A": "Male sex",
            "B": "Age over 50",
            "C": "History of motion sickness or previous PONV",
            "D": "Use of regional anaesthesia",
            "E": "Use of propofol TIVA",
        },
        "answer": "C",
        "explanation": "The simplified Apfel score has 4 risk factors: female sex, non-smoker, history of PONV or motion sickness, and postoperative opioid use. Each factor adds ~20% risk (0 factors ~10%, 4 factors ~80%). Age, type of surgery, and duration all affect risk but are not in the simplified Apfel score. Regional anaesthesia and propofol TIVA are PROTECTIVE against PONV.",
    },
    {
        "id": "clin022", "topic": "Clinical Anaesthesia",
        "question": "Which of the following correctly describes the mechanism of spinal cord injury from epidural haematoma?",
        "options": {
            "A": "Direct trauma from the epidural needle to the spinal cord",
            "B": "Infection spreading to the meninges",
            "C": "Venous bleeding into the epidural space causing compressive ischaemia",
            "D": "Arterial rupture causing subarachnoid haemorrhage",
            "E": "Intrathecal injection of the LA causing neurotoxicity",
        },
        "answer": "C",
        "explanation": "Epidural haematoma most commonly arises from venous (epidural venous plexus) bleeding into the epidural space, causing expanding haematoma and compressive ischaemia of the spinal cord. Risk factors include coagulopathy, anticoagulant therapy, difficult/traumatic insertion, and atraumatic patient positioning. Presentation: severe back pain and new neurological deficit after epidural. Emergency MRI and surgical decompression within 8 hours is required to prevent permanent paralysis.",
    },
    {
        "id": "clin023", "topic": "Clinical Anaesthesia",
        "question": "A patient develops a tachyarrhythmia with broad complexes at 180 bpm following induction. They are haemodynamically stable. What is the FIRST action?",
        "options": {
            "A": "Immediate synchronised DC cardioversion at 200 J",
            "B": "IV adenosine 6 mg rapid bolus",
            "C": "12-lead ECG, attach defibrillator, assess for adverse features",
            "D": "Amiodarone 300 mg IV over 20\u201360 minutes",
            "E": "Verapamil 5 mg IV",
        },
        "answer": "C",
        "explanation": "The first step in any perioperative arrhythmia is systematic assessment: 12-lead ECG and evaluate for adverse features (haemodynamic instability, chest pain, heart failure, syncope). If stable, determine if the broad complex tachycardia is regular (VT vs. SVT with aberrancy) or irregular (VF, AF with aberrancy). Adenosine can be used for regular broad complex tachycardia if SVT is suspected. Immediate cardioversion is for haemodynamically compromised patients. Verapamil is contraindicated if VT is possible.",
    },
    {
        "id": "clin024", "topic": "Clinical Anaesthesia",
        "question": "Regarding the Bier's block (intravenous regional anaesthesia), which statement is MOST correct?",
        "options": {
            "A": "Bupivacaine 0.5% is the preferred agent due to its long duration",
            "B": "The cuff can be deflated after 10 minutes as the LA is fully tissue-bound",
            "C": "Prilocaine 0.5% is the agent of choice; cuff should remain inflated for at least 20 minutes",
            "D": "The block provides excellent muscle relaxation",
            "E": "A single-cuff tourniquet is safer than a double-cuff system",
        },
        "answer": "C",
        "explanation": "IVRA (Bier's block): prilocaine 0.5% (3 mg/kg) is the agent of choice in the UK \u2014 lowest systemic toxicity. Bupivacaine 0.5% is ABSOLUTELY CONTRAINDICATED due to risk of fatal cardiac toxicity on cuff release. The cuff must remain inflated for at least 20 minutes (ideally 25\u201330 min) to allow tissue binding of LA and prevent toxic systemic levels on deflation. A double-cuff tourniquet allows transition to distal (less uncomfortable) cuff once the proximal LA takes effect.",
    },
    {
        "id": "clin025", "topic": "Clinical Anaesthesia",
        "question": "What is the MOST appropriate management of a total spinal following an epidural top-up for caesarean section?",
        "options": {
            "A": "Sit the patient upright to limit cephalad spread",
            "B": "Immediate intubation and ventilation, left lateral tilt, vasopressors, supportive care",
            "C": "Give intralipid 1.5 mg/kg IV",
            "D": "Administer neostigmine to reverse the block",
            "E": "Give IV dexamethasone 8 mg and observe",
        },
        "answer": "B",
        "explanation": "Total spinal (accidental subarachnoid injection of epidural dose) causes rapid ascending motor and sensory block to the brainstem, with hypotension, bradycardia, apnoea, and loss of consciousness. Management: ABC \u2014 immediate tracheal intubation and IPPV (apnoea), left lateral tilt (aortocaval decompression), aggressive vasopressor therapy (ephedrine/phenylephrine/adrenaline for refractory hypotension), atropine for bradycardia, supportive care until block wears off (~2\u20134 hours). Fetal delivery may need to proceed urgently.",
    },
]


# ── Supabase ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def load_stats() -> dict:
    try:
        sb = get_supabase()
        r = sb.table("mcq_stats").select("data").eq("id", 1).execute()
        if r.data and r.data[0]["data"]:
            d = r.data[0]["data"]
            return d if isinstance(d, dict) else json.loads(d)
    except Exception:
        pass
    return default_stats()


def save_stats(stats: dict):
    try:
        sb = get_supabase()
        sb.table("mcq_stats").upsert({"id": 1, "data": stats}).execute()
    except Exception as e:
        st.error(f"Could not save stats: {e}")


def default_stats() -> dict:
    return {
        "sessions": [],
        "topic_totals": {t: {"correct": 0, "total": 0} for t in TOPICS},
        "answered_ids": [],
    }


# ── AI question generation ────────────────────────────────────────────────────
def generate_question(topic: str, used_ids: list) -> dict | None:
    """Generate a novel MCQ using Claude, with optional inline SVG diagram."""
    client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    prompt = f"""Generate a single, high-quality Primary FRCA standard SBA (single best answer) MCQ on the topic: {topic}.

Requirements:
- Five options labelled A-E
- Only ONE correct answer
- Plausible distractors based on common exam misconceptions
- A clear, detailed explanation of why the answer is correct and why distractors are wrong
- Difficulty level: appropriate for Primary FRCA written paper

DIAGRAM DECISION:
Decide whether a diagram, graph, or infographic would meaningfully help the student understand or answer this question.
A diagram IS appropriate for questions involving:
- Waveforms or traces (ECG, capnograph, CVP, arterial line, spirometry, action potentials)
- Curves with shifts (ODC, dose-response, Frank-Starling, compliance)
- Anatomical relationships or nerve distributions relevant to the question
- Flow diagrams for physiological processes (cardiac cycle, renal handling, clotting cascade)
- Graphs where the shape/pattern IS the concept being tested

A diagram is NOT needed for:
- Pure definition/mechanism questions with no visual component
- Drug dosing or classification questions
- Questions where text options fully convey all necessary information

If a diagram IS appropriate, generate clean SVG code following these STRICT rules:
- viewBox="0 0 420 220" (or 420x180 for simpler traces), style with background #161b27, border-radius:8px
- Dark theme ONLY: background #161b27, grid lines #252e42, axes #6b7a99, main text #e8edf5, muted labels #6b7a99
- Curve/trace colours: use topic-appropriate accent colours (#2dd4bf teal, #a78bfa purple, #38bdf8 blue, #fb923c orange, #4ade80 green, #f87171 red, #fbbf24 yellow, #60a5fa light-blue)
- Font: font-family="IBM Plex Mono,monospace" for all labels, font-size 9-11px
- Include: axis lines, light grid, axis labels with units, a short descriptive title, legend if multiple traces
- Use <polyline> for traces, <line> for axes/grid, <text> for labels, <rect> for backgrounds
- SVG must be self-contained - no external references, no <script>, no CSS classes
- Keep SVG compact but readable — aim for under 4000 characters
- The SVG will be rendered inside a dark card, so NO white backgrounds anywhere

Respond ONLY with a JSON object in this exact format (no markdown, no preamble, no code fences):
{{
  "id": "ai_placeholder",
  "topic": "{topic}",
  "question": "...",
  "options": {{
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "...",
    "E": "..."
  }},
  "answer": "A",
  "explanation": "...",
  "svg": "<svg ...>...</svg> or null if no diagram needed",
  "svg_caption": "Short label shown below diagram, or null"
}}

If svg is null, set svg_caption to null too. Do not include the string "null" inside svg quotes — use JSON null."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Strip any accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        q = json.loads(raw)
        q["id"] = f"ai_{uuid.uuid4().hex[:8]}"
        # Validate svg field — must be string starting with <svg or None
        svg = q.get("svg")
        if svg and isinstance(svg, str) and svg.strip().startswith("<svg"):
            # Inject consistent sizing style if missing
            if "style=" not in svg[:80]:
                svg = svg.replace("<svg ", '<svg style="width:100%;max-width:420px;display:block;margin:0 auto 16px;" ', 1)
            else:
                svg = svg.replace("<svg ", '<svg style="', 1)  # leave as-is
            q["svg"] = svg
        else:
            q["svg"] = None
            q["svg_caption"] = None
        return q
    except Exception as e:
        st.error(f"AI generation failed: {e}")
        return None


# ── Session state ─────────────────────────────────────────────────────────────
if "stats" not in st.session_state:
    st.session_state.stats = load_stats()
if "page" not in st.session_state:
    st.session_state.page = "home"
if "session" not in st.session_state:
    st.session_state.session = None   # active quiz session
if "current_q" not in st.session_state:
    st.session_state.current_q = None
if "selected_answer" not in st.session_state:
    st.session_state.selected_answer = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "generating" not in st.session_state:
    st.session_state.generating = False
if "textbook_docs" not in st.session_state:
    st.session_state.textbook_docs = None
if "fc_data" not in st.session_state:
    st.session_state.fc_data = None  # loaded lazily
if "fc_study_queue" not in st.session_state:
    st.session_state.fc_study_queue = []
if "fc_study_idx" not in st.session_state:
    st.session_state.fc_study_idx = 0
if "fc_flipped" not in st.session_state:
    st.session_state.fc_flipped = False
if "fc_session_stats" not in st.session_state:
    st.session_state.fc_session_stats = {"again": 0, "hard": 0, "good": 0, "easy": 0}
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []  # per-question chat history
if "chat_q_id" not in st.session_state:
    st.session_state.chat_q_id = None  # which question the chat is about
if "fc_editor_open" not in st.session_state:
    st.session_state.fc_editor_open = False  # whether flashcard editor is showing
if "fc_editor_q_id" not in st.session_state:
    st.session_state.fc_editor_q_id = None
if "quiz_review_idx" not in st.session_state:
    st.session_state.quiz_review_idx = None  # None = not in review mode; int = reviewing result at that index
if "mid_session_review" not in st.session_state:
    st.session_state.mid_session_review = False

stats = st.session_state.stats


def nav(page):
    st.session_state.page = page


# ── Textbook storage ──────────────────────────────────────────────────────────
def load_textbook_docs() -> list:
    try:
        sb = get_supabase()
        r = sb.table("textbook_store").select("*").execute()
        if r.data:
            return r.data
    except Exception:
        pass
    return []


def save_textbook_doc(name: str, topic: str, b64_data: str) -> bool:
    try:
        sb = get_supabase()
        sb.table("textbook_store").insert({
            "id": str(uuid.uuid4()),
            "name": name,
            "topic": topic,
            "data": b64_data,
            "uploaded": datetime.now().isoformat(),
        }).execute()
        return True
    except Exception as e:
        st.error(f"Could not save document: {e}")
        return False


def delete_textbook_doc(doc_id: str) -> bool:
    try:
        sb = get_supabase()
        sb.table("textbook_store").delete().eq("id", doc_id).execute()
        return True
    except Exception as e:
        st.error(f"Could not delete: {e}")
        return False

# ── SM-2 Spaced Repetition ────────────────────────────────────────────────────
def sm2(card: dict, grade: int) -> dict:
    """grade: 0=Again, 1=Hard, 2=Good, 3=Easy"""
    interval    = card.get("interval", 1)
    repetitions = card.get("repetitions", 0)
    ease_factor = card.get("ease_factor", 2.5)
    if grade == 0:
        interval = 1; repetitions = 0
    else:
        if repetitions == 0:   interval = 1
        elif repetitions == 1: interval = 6
        else:                  interval = math.ceil(interval * ease_factor)
        repetitions += 1
    ef = ease_factor + (0.1 - (3 - grade) * (0.08 + (3 - grade) * 0.02))
    ease_factor = max(1.3, round(ef, 3))
    next_review = (datetime.now() + timedelta(days=interval)).isoformat()
    return {**card, "interval": interval, "repetitions": repetitions,
            "ease_factor": ease_factor, "next_review": next_review, "last_grade": grade}

def fc_is_due(card: dict) -> bool:
    if not card.get("next_review"): return True
    return datetime.fromisoformat(card["next_review"]) <= datetime.now()

def fc_days_until(card: dict) -> str:
    if not card.get("next_review"): return "Now"
    delta = datetime.fromisoformat(card["next_review"]) - datetime.now()
    d = delta.days
    return "Now" if d <= 0 else ("Tomorrow" if d == 1 else f"{d}d")

# ── Flashcard Supabase ────────────────────────────────────────────────────────
def load_flashcard_data() -> dict:
    try:
        sb = get_supabase()
        r = sb.table("frca_flashcards").select("data").eq("id", 1).execute()
        if r.data and r.data[0]["data"]:
            d = r.data[0]["data"]
            data = d if isinstance(d, dict) else json.loads(d)
            # Merge in any new canonical decks not yet in stored data
            existing_ids = {deck["id"] for deck in data.get("decks", [])}
            for canonical in CANONICAL_DECKS:
                if canonical["id"] not in existing_ids:
                    data.setdefault("decks", []).append(dict(canonical))
            return data
    except Exception:
        pass
    return {"decks": [dict(d) for d in CANONICAL_DECKS]}

def save_flashcard_data(fc_data: dict):
    try:
        sb = get_supabase()
        sb.table("frca_flashcards").upsert({"id": 1, "data": fc_data}).execute()
    except Exception as e:
        st.error(f"Could not save flashcards: {e}")

# ── Session Resume Supabase ───────────────────────────────────────────────────
def save_session_state(session: dict):
    try:
        sb = get_supabase()
        payload = {
            "id": 1,
            "session": json.dumps(session),
            "saved_at": datetime.now().isoformat(),
        }
        sb.table("session_resume").upsert(payload).execute()
    except Exception:
        pass

def load_saved_session() -> dict | None:
    try:
        sb = get_supabase()
        r = sb.table("session_resume").select("*").eq("id", 1).execute()
        if r.data and r.data[0].get("session"):
            s = r.data[0]["session"]
            parsed = json.loads(s) if isinstance(s, str) else s
            # Only resume if incomplete
            if parsed and len(parsed.get("results", [])) < parsed.get("n_target", 0):
                return parsed
    except Exception:
        pass
    return None

def clear_saved_session():
    try:
        sb = get_supabase()
        sb.table("session_resume").upsert({"id": 1, "session": None, "saved_at": None}).execute()
    except Exception:
        pass



# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Close button at very top of sidebar — always visible on mobile
    close_col, title_col = st.columns([1, 3])
    with close_col:
        if st.button("✕", key="sidebar_close", use_container_width=True):
            st.session_state.sidebar_visible = False
            st.rerun()
    with title_col:
        st.markdown("""
        <div style="padding:6px 0 0;">
            <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 2px;">Primary FRCA</p>
            <p style="font-family:Fraunces,serif;color:#e8edf5;font-size:18px;font-weight:300;margin:0;">MCQ Drill</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="border-bottom:1px solid #252e42;margin:12px 0 8px;"></div>', unsafe_allow_html=True)

    if st.button("Home", use_container_width=True):
        nav("home")
    if st.button("Performance", use_container_width=True):
        nav("stats")
    if st.button("Textbook", use_container_width=True):
        nav("textbook")
    if st.button("Flashcards", use_container_width=True):
        nav("flashcards")

    # Quick topic stats in sidebar
    st.markdown("""
    <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;
              text-transform:uppercase;letter-spacing:0.08em;margin:24px 16px 10px;padding:0;">Topic Scores</p>
    """, unsafe_allow_html=True)

    for topic, meta in TOPICS.items():
        t = stats["topic_totals"].get(topic, {"correct": 0, "total": 0})
        pct = int(t["correct"] / t["total"] * 100) if t["total"] else 0
        bar_colour = meta["colour"]
        st.markdown(f"""
        <div style="margin:0 16px 10px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                <span style="color:#e8edf5;font-size:12px;">{topic.split(' &')[0].split(' ')[0]}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:11px;color:{bar_colour};">{pct}%</span>
            </div>
            <div style="background:#252e42;border-radius:1px;height:2px;">
                <div style="width:{pct}%;height:2px;background:{bar_colour};border-radius:1px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: HOME
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.page == "home":
    st.markdown("""
    <div style="padding-bottom:32px;border-bottom:1px solid #252e42;margin-bottom:32px;">
        <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 10px;">Primary FRCA</p>
        <h1 style="font-family:Fraunces,serif;font-size:42px;font-weight:300;letter-spacing:-0.03em;margin:0 0 10px;color:#e8edf5;">MCQ Drill</h1>
        <p style="color:#6b7a99;font-size:14px;margin:0;font-weight:300;">Timed SBA practice &middot; Fixed bank + AI-generated questions &middot; Per-topic tracking</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Resume banner ──────────────────────────────────────────────────────────
    if "resume_checked" not in st.session_state:
        st.session_state.resume_checked = False
    if not st.session_state.resume_checked:
        saved = load_saved_session()
        st.session_state.resume_checked = True
        if saved:
            st.session_state._saved_session = saved
    if hasattr(st.session_state, "_saved_session") and st.session_state._saved_session:
        saved = st.session_state._saved_session
        done_n = len(saved.get("results", []))
        total_n = saved.get("n_target", 0)
        topic_label = saved.get("topic_filter") or "All Topics"
        st.markdown(f"""
        <div style="background:#161b27;border:1px solid #2e3a52;border-left:3px solid #4f9cf9;
                    border-radius:6px;padding:16px 20px;margin-bottom:24px;display:flex;
                    align-items:center;justify-content:space-between;">
            <div>
                <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;
                          text-transform:uppercase;letter-spacing:0.08em;margin:0 0 4px;">Incomplete session</p>
                <p style="font-size:14px;color:#e8edf5;margin:0;">{topic_label} &mdash; {done_n}/{total_n} completed</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("Resume session →", use_container_width=True, key="resume_btn"):
                st.session_state.session = saved
                st.session_state.current_q = None
                st.session_state.selected_answer = None
                st.session_state.submitted = False
                st.session_state.chat_messages = []
                st.session_state._saved_session = None
                nav("quiz")
                st.rerun()
        with rc2:
            if st.button("Discard", use_container_width=True, key="discard_btn"):
                clear_saved_session()
                st.session_state._saved_session = None
                st.rerun()
        st.markdown("---")

    st.markdown("""
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px 28px 20px;margin-bottom:24px;">
        <p style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;margin:0 0 16px;">New Session</p>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        topic_choice = st.selectbox(
            "Topic", ["All Topics"] + list(TOPICS.keys()), key="cfg_topic"
        )
    with col2:
        mode_choice = st.selectbox(
            "Source",
            ["Mixed (Fixed + AI)", "Fixed bank only", "AI-generated only"],
            key="cfg_mode",
        )
    with col3:
        timing_choice = st.selectbox(
            "Timing",
            ["Timed — 90s", "Untimed"],
            key="cfg_timing",
        )

    n_questions = st.slider("Questions", 5, 30, 10, key="cfg_n")

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Start Session →", use_container_width=True):
        # Build question queue
        topic_filter = None if topic_choice == "All Topics" else topic_choice

        # Split bank into unseen-first, then seen — avoids repeats across sessions
        answered_ids = st.session_state.stats.get("answered_ids", [])
        full_bank = [q for q in FIXED_BANK if (not topic_filter or q["topic"] == topic_filter)]
        unseen = [q for q in full_bank if q["id"] not in answered_ids]
        seen   = [q for q in full_bank if q["id"] in answered_ids]

        def interleave_topics(pool):
            """Shuffle within each topic then interleave so consecutive Qs are always different topics."""
            from collections import defaultdict
            by_topic = defaultdict(list)
            for q in pool:
                by_topic[q["topic"]].append(q)
            for t in by_topic:
                random.shuffle(by_topic[t])
            # Round-robin across topics
            result = []
            topic_queues = list(by_topic.values())
            random.shuffle(topic_queues)  # randomise which topic goes first
            while any(topic_queues):
                topic_queues = [tq for tq in topic_queues if tq]
                for tq in topic_queues:
                    if tq:
                        result.append(tq.pop(0))
            return result

        bank = interleave_topics(unseen) + interleave_topics(seen)

        def shuffle_answers(q):
            """Return a copy of q with options shuffled so correct answer lands randomly across A-E."""
            import copy
            q = copy.deepcopy(q)
            keys = list("ABCDE")
            correct_text = q["options"][q["answer"]]
            vals = list(q["options"].values())
            random.shuffle(vals)
            q["options"] = dict(zip(keys, vals))
            # Update answer key to wherever the correct text landed
            q["answer"] = next(k for k, v in q["options"].items() if v == correct_text)
            return q

        use_fixed = mode_choice != "AI-generated only"
        use_ai    = mode_choice != "Fixed bank only"

        if use_fixed:
            fixed_qs = [shuffle_answers(q) for q in bank[:n_questions]]
        else:
            fixed_qs = []

        ai_needed = max(0, n_questions - len(fixed_qs)) if use_ai else 0

        st.session_state.session = {
            "topic_filter": topic_filter,
            "use_ai": use_ai,
            "ai_needed": ai_needed,
            "timed": "Timed" in timing_choice,
            "queue": fixed_qs,
            "idx": 0,
            "results": [],
            "n_target": n_questions,
            "shown_ids": [q["id"] for q in fixed_qs],
        }
        st.session_state.current_q = None
        st.session_state.selected_answer = None
        st.session_state.submitted = False
        st.session_state.quiz_review_idx = None
        st.session_state.mid_session_review = False
        nav("quiz")
        st.rerun()

    # Recent sessions
    if stats["sessions"]:
        st.markdown("""
        <p style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--muted);
                  text-transform:uppercase;letter-spacing:0.08em;margin:28px 0 12px;">Recent Sessions</p>
        """, unsafe_allow_html=True)
        recent = stats["sessions"][-5:][::-1]
        for s in recent:
            pct = int(s["correct"] / s["total"] * 100) if s["total"] else 0
            bar_c = "#4ade80" if pct >= 60 else "#f87171"
            topic_label = s.get("topic", "All")
            date_str = datetime.fromisoformat(s["ts"]).strftime("%d %b %H:%M")
            st.markdown(f"""
            <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;
                        padding:14px 18px;margin-bottom:6px;display:flex;align-items:center;gap:16px;">
                <div style="flex:1;">
                    <p style="font-size:14px;color:var(--text);margin:0 0 2px;">{topic_label}</p>
                    <p style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--muted);margin:0;">{date_str}</p>
                </div>
                <div style="text-align:right;">
                    <p style="font-family:'Fraunces',serif;font-size:22px;font-weight:300;color:{bar_c};margin:0;line-height:1;">{pct}%</p>
                    <p style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--muted);margin:0;">{s["correct"]}/{s["total"]}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: QUIZ
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.page == "quiz":
    session = st.session_state.session
    if not session:
        nav("home")
        st.rerun()

    idx  = session["idx"]
    done = len(session["results"])
    total_target = session["n_target"]

    # Session complete
    if done >= total_target:
        correct = sum(1 for r in session["results"] if r["correct"])
        pct = int(correct / done * 100)

        result_colour = "#166534" if pct >= 60 else "#991b1b"
        result_bg = "#f0fdf4" if pct >= 60 else "#fef2f2"
        result_label = "Pass territory" if pct >= 60 else "Below pass mark"
        st.markdown(f"""
        <div style="text-align:center;padding:48px 0 32px;border-bottom:1px solid #252e42;margin-bottom:32px;">
            <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 16px;">Session complete</p>
            <h2 style="font-family:Fraunces,serif;font-size:72px;font-weight:300;letter-spacing:-0.04em;margin:0 0 12px;color:#e8edf5;line-height:1;">
                {correct}<span style="font-size:32px;color:#6b7a99;">/{done}</span>
            </h2>
            <span style="display:inline-block;background:{result_bg};color:{result_colour};border-radius:4px;padding:4px 14px;font-size:13px;font-family:IBM Plex Mono,monospace;letter-spacing:0.04em;">
                {result_label} &mdash; {pct}%
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Record session
        s_record = {
            "ts": datetime.now().isoformat(),
            "topic": session.get("topic_filter") or "All",
            "correct": correct,
            "total": done,
        }
        stats["sessions"].append(s_record)

        # Update topic totals
        for r in session["results"]:
            t = r["topic"]
            if t not in stats["topic_totals"]:
                stats["topic_totals"][t] = {"correct": 0, "total": 0}
            stats["topic_totals"][t]["total"] += 1
            if r["correct"]:
                stats["topic_totals"][t]["correct"] += 1

        save_stats(stats)
        clear_saved_session()

        # Per-question review — card navigator
        results = session["results"]
        n_results = len(results)
        if st.session_state.quiz_review_idx is None:
            st.session_state.quiz_review_idx = 0
        ri = max(0, min(st.session_state.quiz_review_idx, n_results - 1))

        # Mini progress dots
        dots_html = ""
        for di in range(n_results):
            r_dot = results[di]
            dot_col = "#4ade80" if r_dot["correct"] else "#f87171"
            dot_size = "10px" if di == ri else "7px"
            dots_html += f'<span style="display:inline-block;width:{dot_size};height:{dot_size};border-radius:50%;background:{dot_col};margin:0 3px;transition:all 0.15s;"></span>'

        st.markdown(f'''
        <div style="text-align:center;margin:0 0 20px;">
            <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 10px;">Answer Review</p>
            <div>{dots_html}</div>
        </div>
        ''', unsafe_allow_html=True)

        r = results[ri]
        q_colour = TOPICS.get(r["topic"], {}).get("colour", "#4f9cf9")
        icon = "✓" if r["correct"] else "✗"
        icon_col = "#4ade80" if r["correct"] else "#f87171"
        icon_bg  = "#0a1f14" if r["correct"] else "#1c0a0a"

        # Result card
        options_html = ""
        for opt, text in r["options"].items():
            if opt == r["answer"]:
                bg, col, marker = "#0a1f14", "#4ade80", "✓"
            elif opt == r["selected"] and not r["correct"]:
                bg, col, marker = "#1c0a0a", "#f87171", "✗"
            else:
                bg, col, marker = "transparent", "#6b7a99", "·"
            options_html += (
                f'<div style="background:{bg};border:1px solid {col}33;border-radius:6px;' +
                f'padding:10px 14px;margin:6px 0;display:flex;gap:10px;align-items:flex-start;">' +
                f'<span style="color:{col};font-family:IBM Plex Mono,monospace;font-size:12px;' +
                f'min-width:14px;margin-top:1px;">{marker}</span>' +
                f'<span style="color:{col};font-size:14px;line-height:1.5;"><strong>{opt}.</strong> {text}</span>' +
                f'</div>'
            )

        _eos_sub = Q_SUBTOPICS.get(r.get('id', ''), (None, ''))
        _eos_deck_id, _eos_sub_name = _eos_sub
        _eos_badge = (
            f'<span style="display:inline-block;background:{q_colour}15;border:1px solid {q_colour}44;'
            f'border-radius:4px;padding:1px 8px;font-family:IBM Plex Mono,monospace;font-size:10px;'
            f'color:{q_colour};margin-left:8px;">{_eos_sub_name}</span>'
        ) if _eos_sub_name else ''

        st.markdown(
            f'<div style="border:1px solid #252e42;border-top:3px solid {q_colour};border-radius:8px;padding:24px;margin-bottom:12px;">' +
            f'<div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:16px;">' +
            f'<span style="display:inline-flex;align-items:center;justify-content:center;' +
            f'width:28px;height:28px;border-radius:50%;background:{icon_bg};' +
            f'color:{icon_col};font-size:14px;font-weight:700;">{icon}</span>' +
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{q_colour};' +
            f'text-transform:uppercase;letter-spacing:0.08em;">Q{ri+1} of {n_results} · {r["topic"]}</span>' +
            _eos_badge +
            f'</div>' +
            + (f'<div style="margin-bottom:14px;">{Q_IMAGES[r["id"]]}</div>' if r.get('id') in Q_IMAGES
               else (f'<div style="margin-bottom:14px;">{r["svg"]}</div>' if r.get('svg') else '')) +
            f'<p style="font-size:16px;color:#e8edf5;line-height:1.6;margin:0 0 18px;font-weight:500;">{r["question"]}</p>' +
            f'{options_html}' +
            f'<div style="border-left:3px solid {q_colour};padding:12px 16px;margin-top:16px;' +
            f'background:#161b27;border-radius:0 6px 6px 0;font-size:14px;line-height:1.7;color:#c8d3e8;">' +
            f'<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{q_colour};' +
            f'text-transform:uppercase;letter-spacing:0.08em;margin:0 0 8px;">Explanation</p>' +
            f'{r["explanation"]}' +
            f'</div>' +
            f'</div>',
            unsafe_allow_html=True
        )

        # Prev / Next + Go to deck
        prev_col, counter_col, next_col = st.columns([1, 2, 1])
        with prev_col:
            if st.button("← Prev", use_container_width=True, disabled=(ri == 0)):
                st.session_state.quiz_review_idx = ri - 1
                st.rerun()
        with counter_col:
            st.markdown(
                f'<p style="text-align:center;font-family:IBM Plex Mono,monospace;font-size:12px;' +
                f'color:#6b7a99;margin:10px 0;">{ri+1} / {n_results}</p>',
                unsafe_allow_html=True
            )
        with next_col:
            if st.button("Next →", use_container_width=True, disabled=(ri == n_results - 1)):
                st.session_state.quiz_review_idx = ri + 1
                st.rerun()
        if _eos_deck_id and _eos_sub_name:
            if st.button(f"→ Go to {_eos_sub_name}", use_container_width=True, key=f"eos_deck_{ri}"):
                st.session_state.fc_view = 'browse'
                st.session_state.fc_active_deck_id = _eos_deck_id
                nav('flashcards')
                st.rerun()

        st.markdown("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Home", use_container_width=True):
                nav("home")
                st.rerun()
        with c2:
            if st.button("View Stats", use_container_width=True):
                nav("stats")
                st.rerun()

    else:
        # Load next question
        if st.session_state.current_q is None:
            queue = session["queue"]
            shown_ids = session.get("shown_ids", [])

            if idx < len(queue):
                # Serve pre-built queue
                st.session_state.current_q = queue[idx]
                st.session_state.selected_answer = None
                st.session_state.submitted = False
                st.session_state.start_time = time.time()

            elif session["use_ai"] and session["ai_needed"] > 0:
                # Generate AI question
                with st.spinner("Generating question…"):
                    topic = session["topic_filter"] or random.choice(list(TOPICS.keys()))
                    q = generate_question(topic, shown_ids)
                    if q:
                        import copy as _copy
                        q = _copy.deepcopy(q)
                        _keys = list("ABCDE")
                        _correct_text = q["options"][q["answer"]]
                        _vals = list(q["options"].values())
                        random.shuffle(_vals)
                        q["options"] = dict(zip(_keys, _vals))
                        q["answer"] = next(k for k, v in q["options"].items() if v == _correct_text)
                        shown_ids.append(q["id"])
                        session["shown_ids"] = shown_ids
                        st.session_state.current_q = q
                        st.session_state.selected_answer = None
                        st.session_state.submitted = False
                        st.session_state.start_time = time.time()
                        session["ai_needed"] -= 1
                    else:
                        st.error("Could not generate question. Check ANTHROPIC_API_KEY.")
                        st.stop()
                st.rerun()

            else:
                # Fixed bank fallback — never repeat a seen question if avoidable
                topic_filter = session.get("topic_filter")
                candidate_pool = [
                    q for q in FIXED_BANK
                    if (not topic_filter or q["topic"] == topic_filter)
                    and q["id"] not in shown_ids
                ]
                # If all fixed questions exhausted, reset and allow repeats
                if not candidate_pool:
                    candidate_pool = [
                        q for q in FIXED_BANK
                        if (not topic_filter or q["topic"] == topic_filter)
                    ]
                    if not candidate_pool:
                        candidate_pool = list(FIXED_BANK)

                next_q = random.choice(candidate_pool)
                shown_ids.append(next_q["id"])
                session["shown_ids"] = shown_ids
                st.session_state.current_q = next_q
                st.session_state.selected_answer = None
                st.session_state.submitted = False
                st.session_state.start_time = time.time()

        q = st.session_state.current_q
        if not q:
            st.rerun()

        # Header
        colour = TOPICS.get(q["topic"], {}).get("colour", "#4f9cf9")
        progress_pct = int(done / total_target * 100)

        # Build timer string separately — no nested f-strings
        if session["timed"] and not st.session_state.submitted:
            elapsed = time.time() - (st.session_state.start_time or time.time())
            remaining = max(0, 90 - elapsed)
            time_colour = "#f87171" if remaining < 20 else "#fbbf24" if remaining < 45 else "#4ade80"
            timer_secs = int(remaining)
            timer_block = (
                '<div style="text-align:center;min-width:56px;">'
                '<p style="font-family:IBM Plex Mono,monospace;font-size:28px;font-weight:500;'
                'margin:0;line-height:1;color:' + time_colour + ';">' + str(timer_secs) + '</p>'
                '<p style="font-family:IBM Plex Mono,monospace;font-size:9px;color:#6b7a99;'
                'text-transform:uppercase;letter-spacing:0.06em;margin:2px 0 0;">sec</p>'
                '</div>'
            )
        else:
            timer_block = ""

        # Review-previous state — show review panel if active
        reviewing = st.session_state.get("mid_session_review", False)

        if reviewing and done > 0:
            results = session["results"]
            n_res = len(results)
            if st.session_state.quiz_review_idx is None:
                st.session_state.quiz_review_idx = n_res - 1
            ri = max(0, min(st.session_state.quiz_review_idx, n_res - 1))
            r = results[ri]
            r_colour = TOPICS.get(r["topic"], {}).get("colour", "#4f9cf9")
            icon = "✓" if r["correct"] else "✗"
            icon_col = "#4ade80" if r["correct"] else "#f87171"
            icon_bg  = "#0a1f14" if r["correct"] else "#1c0a0a"
            options_html = ""
            for opt, text in r["options"].items():
                if opt == r["answer"]:
                    bg2, col2, marker2 = "#0a1f14", "#4ade80", "✓"
                elif opt == r["selected"] and not r["correct"]:
                    bg2, col2, marker2 = "#1c0a0a", "#f87171", "✗"
                else:
                    bg2, col2, marker2 = "transparent", "#6b7a99", "·"
                options_html += (
                    f'<div style="background:{bg2};border:1px solid {col2}33;border-radius:6px;'
                    f'padding:10px 14px;margin:6px 0;display:flex;gap:10px;align-items:flex-start;">'
                    f'<span style="color:{col2};font-family:IBM Plex Mono,monospace;font-size:12px;min-width:14px;">{marker2}</span>'
                    f'<span style="color:{col2};font-size:14px;line-height:1.5;"><strong>{opt}.</strong> {text}</span>'
                    f'</div>'
                )
            st.markdown(
                f'<div style="border:1px solid #252e42;border-top:3px solid {r_colour};border-radius:8px;padding:20px 24px;margin-bottom:16px;">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">'
                f'<span style="display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;'
                f'border-radius:50%;background:{icon_bg};color:{icon_col};font-size:13px;font-weight:700;">{icon}</span>'
                f'<span style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{r_colour};'
                f'text-transform:uppercase;letter-spacing:0.08em;">Q{ri+1} · {r["topic"]}</span>'
                + (f'<span style="display:inline-block;background:{r_colour}15;border:1px solid {r_colour}44;'
                f'border-radius:4px;padding:1px 8px;font-family:IBM Plex Mono,monospace;font-size:10px;'
                f'color:{r_colour};margin-left:8px;">{Q_SUBTOPICS.get(r.get("id",""), (None,""))[1]}</span>'
                if Q_SUBTOPICS.get(r.get("id","")) else "")
                + f'</div>'
                + (f'<div style="margin-bottom:14px;">{Q_IMAGES[r["id"]]}</div>' if r.get('id') in Q_IMAGES
                   else (f'<div style="margin-bottom:14px;">{r["svg"]}</div>' if r.get('svg') else ''))
                + f'<p style="font-size:16px;color:#e8edf5;line-height:1.6;margin:0 0 16px;font-weight:500;">{r["question"]}</p>'
                + f'{options_html}'
                + f'<div style="border-left:3px solid {r_colour};padding:12px 16px;margin-top:14px;'
                f'background:#161b27;border-radius:0 6px 6px 0;font-size:14px;line-height:1.7;color:#c8d3e8;">'
                f'<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{r_colour};'
                f'text-transform:uppercase;letter-spacing:0.08em;margin:0 0 8px;">Explanation</p>'
                f'{r["explanation"]}</div></div>',
                unsafe_allow_html=True
            )
            prev_c, ctr_c, next_c, close_c = st.columns([1, 1, 1, 1])
            with prev_c:
                if st.button("← Prev", key="rev_prev", use_container_width=True, disabled=(ri == 0)):
                    st.session_state.quiz_review_idx = ri - 1
                    st.rerun()
            with ctr_c:
                st.markdown(f'<p style="text-align:center;font-family:IBM Plex Mono,monospace;font-size:12px;color:#6b7a99;margin:10px 0;">{ri+1} / {n_res}</p>', unsafe_allow_html=True)
            with next_c:
                if st.button("Next →", key="rev_next", use_container_width=True, disabled=(ri == n_res - 1)):
                    st.session_state.quiz_review_idx = ri + 1
                    st.rerun()
            with close_c:
                if st.button("✕ Resume", key="rev_close", use_container_width=True):
                    st.session_state.mid_session_review = False
                    st.rerun()
            st.markdown('<hr style="border-color:#252e42;margin:20px 0;">', unsafe_allow_html=True)

        # Look up subtopic for this question
        q_id_for_sub = q.get('id', '')
        subtopic_info = Q_SUBTOPICS.get(q_id_for_sub)
        subtopic_deck_id, subtopic_name = subtopic_info if subtopic_info else (None, None)
        broad_topic_short = q['topic'].replace('Physics & Clinical Measurement','Physics').replace('Clinical Anaesthesia','Clinical')
        subtopic_badge = (
            f'<span style="display:inline-block;background:#252e42;border:1px solid #2e3a52;'
            f'border-radius:4px;padding:2px 8px;font-family:IBM Plex Mono,monospace;'
            f'font-size:9px;color:#6b7a99;letter-spacing:0.04em;margin-left:4px;">{broad_topic_short}</span>'
        ) if subtopic_name else ''

        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">'
            '<div>'
            '<p style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#6b7a99;'
            'margin:0 0 5px;text-transform:uppercase;letter-spacing:0.06em;">'
            'Question ' + str(done+1) + ' of ' + str(total_target) + '</p>'
            '<div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;">'
            '<div style="display:flex;align-items:center;gap:8px;">'
            '<div style="width:3px;height:16px;background:' + colour + ';border-radius:2px;"></div>'
            '<span style="font-family:IBM Plex Mono,monospace;font-size:12px;color:' + colour + ';">' + (Q_SUBTOPICS.get(q.get('id',''), (None, q['topic']))[1]) + '</span>'
            '</div>'
            + subtopic_badge +
            '</div>'
            '</div>'
            + timer_block +
            '</div>'
            '<div style="background:#252e42;border-radius:2px;height:3px;margin-bottom:24px;">'
            '<div style="width:' + str(progress_pct) + '%;height:3px;background:' + colour + ';border-radius:2px;"></div>'
            '</div>',
            unsafe_allow_html=True
        )

        # Question box — with optional diagram (fixed bank lookup or AI-generated SVG)
        q_diagram = Q_IMAGES.get(q.get("id", ""), "") or q.get("svg", "") or ""
        q_svg_caption = q.get("svg_caption") or ""
        caption_html = (
            f'<p style="font-family:IBM Plex Mono,monospace;font-size:9px;color:#6b7a99;'
            f'text-align:center;margin:-8px 0 14px;letter-spacing:0.06em;">{q_svg_caption}</p>'
        ) if q_svg_caption else ""
        diagram_html = f'<div style="margin-bottom:4px;">{q_diagram}{caption_html}</div>' if q_diagram else ""
        st.markdown(
            '<div style="background:#161b27;border:1px solid #252e42;border-radius:12px;'
            'padding:28px 32px;margin-bottom:24px;border-top:3px solid ' + colour + ';">'
            + diagram_html +
            '<p style="font-family:IBM Plex Sans,sans-serif;font-size:18px;font-weight:400;'
            'line-height:1.7;margin:0;color:#e8edf5;">' + q["question"] + '</p>'
            '</div>',
            unsafe_allow_html=True
        )

        if not st.session_state.submitted:
            # "Review previous" link if we have answered questions
            if done > 0:
                rev_label = "📖 Review previous" if not st.session_state.get("mid_session_review") else "▲ Hide review"
                if st.button(rev_label, key="toggle_review"):
                    st.session_state.mid_session_review = not st.session_state.get("mid_session_review", False)
                    if st.session_state.mid_session_review:
                        st.session_state.quiz_review_idx = len(session["results"]) - 1
                    st.rerun()

            # Radio styled as cards via CSS
            selected = st.radio(
                "Select your answer:",
                options=list(q["options"].keys()),
                format_func=lambda k: f"{k}.   {q['options'][k]}",
                key=f"radio_{done}",
                label_visibility="collapsed",
            )
            st.markdown("")
            if st.button("Submit →", use_container_width=True):
                st.session_state.selected_answer = selected
                st.session_state.submitted = True
                st.rerun()

            # Auto-submit on timer
            if session["timed"] and st.session_state.start_time:
                if (time.time() - st.session_state.start_time) >= 90 and not st.session_state.submitted:
                    st.session_state.selected_answer = list(q["options"].keys())[0]
                    st.session_state.submitted = True
                    st.rerun()
                    st.session_state.submitted = True
                    st.rerun()

        else:
            # Show result
            sel = st.session_state.selected_answer
            correct = sel == q["answer"]

            for opt, text in q["options"].items():
                if opt == q["answer"]:
                    bg, border_c, text_c = "#0a1f14", "#14532d", "#4ade80"
                    icon = "✓"
                elif opt == sel and not correct:
                    bg, border_c, text_c = "#1c0a0a", "#7f1d1d", "#f87171"
                    icon = "✗"
                else:
                    bg, border_c, text_c = "#161b27", "#252e42", "#6b7a99"
                    icon = ""
                label_weight = "600" if opt in [q["answer"], sel] else "400"
                st.markdown(f"""
                <div style="background:{bg};border:1.5px solid {border_c};border-radius:10px;
                            padding:16px 20px;margin:6px 0;">
                    <div style="display:flex;gap:12px;align-items:flex-start;">
                        <span style="font-family:IBM Plex Mono,monospace;font-size:13px;
                                     color:{text_c};flex-shrink:0;width:20px;margin-top:1px;">{icon or opt}</span>
                        <p style="font-family:IBM Plex Sans,sans-serif;font-size:15px;
                                  color:{text_c};margin:0;line-height:1.5;font-weight:{label_weight};">{text}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            result_icon = "✓" if correct else "✗"
            result_c = "#4ade80" if correct else "#f87171"
            result_word = "Correct" if correct else "Incorrect"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;margin:20px 0 4px;">
                <span style="font-size:20px;color:{result_c};">{result_icon}</span>
                <span style="font-family:IBM Plex Mono,monospace;font-size:13px;color:{result_c};
                             text-transform:uppercase;letter-spacing:0.06em;">{result_word}</span>
            </div>
            <div style="background:#161b27;border:1px solid #252e42;border-left:3px solid {colour};
                        border-radius:0 8px 8px 0;padding:20px 24px;margin:8px 0 20px;line-height:1.8;color:#e8edf5;">
                <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;
                          text-transform:uppercase;letter-spacing:0.08em;margin:0 0 10px;">Explanation</p>
                <p style="font-family:IBM Plex Sans,sans-serif;font-size:15px;margin:0;line-height:1.8;">{q["explanation"]}</p>
            </div>
            """, unsafe_allow_html=True)

            # ── Post-answer chat ────────────────────────────────────────────
            st.markdown("""
            <div style="margin:24px 0 8px;padding-top:20px;border-top:1px solid #252e42;">
                <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;
                          text-transform:uppercase;letter-spacing:0.08em;margin:0 0 4px;">Ask a follow-up</p>
                <p style="font-size:12px;color:#6b7a99;margin:0 0 12px;">Ask Claude anything about this question or topic.</p>
            </div>
            """, unsafe_allow_html=True)

            # Reset chat if on a new question
            q_id = q.get("id", q["question"][:30])
            if st.session_state.chat_q_id != q_id:
                st.session_state.chat_messages = []
                st.session_state.chat_q_id = q_id

            # Show chat history
            for msg in st.session_state.chat_messages:
                role_label = "You" if msg["role"] == "user" else "Claude"
                role_colour = "#e8edf5" if msg["role"] == "user" else "#4f9cf9"
                bg_colour = "#1e2535" if msg["role"] == "user" else "#161b27"
                st.markdown(f"""
                <div style="background:{bg_colour};border:1px solid #252e42;border-radius:6px;
                            padding:12px 16px;margin:6px 0;">
                    <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{role_colour};
                              margin:0 0 6px;text-transform:uppercase;letter-spacing:0.06em;">{role_label}</p>
                    <p style="font-size:14px;color:#e8edf5;margin:0;line-height:1.6;">{msg["content"]}</p>
                </div>
                """, unsafe_allow_html=True)

            chat_input = st.text_input(
                "Your question",
                placeholder="e.g. Why does alkalosis shift the curve leftward?",
                key=f"chat_input_{q_id}",
                label_visibility="collapsed"
            )
            chat_col1, chat_col2 = st.columns([3, 1])
            with chat_col1:
                if st.button("Ask Claude", key=f"ask_{q_id}", use_container_width=True):
                    if chat_input.strip():
                        st.session_state.chat_messages.append({"role": "user", "content": chat_input.strip()})
                        # Build context for Claude
                        ctx = f"""You are a Primary FRCA exam tutor. The student just answered this MCQ:

Question: {q["question"]}
Options: {json.dumps(q["options"])}
Correct answer: {q["answer"]}
Student's answer: {sel} ({"correct" if correct else "incorrect"})
Explanation: {q["explanation"]}

Answer the student's follow-up question concisely and clearly. Focus on exam-relevant detail. Be direct."""
                        msgs = [{"role": "system", "content": ctx}] if False else []
                        history = [{"role": m["role"], "content": m["content"]}
                                   for m in st.session_state.chat_messages]
                        try:
                            client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                            resp = client.messages.create(
                                model="claude-sonnet-4-20250514",
                                max_tokens=400,
                                system=ctx,
                                messages=history,
                            )
                            reply = resp.content[0].text.strip()
                            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                        except Exception as e:
                            st.session_state.chat_messages.append({"role": "assistant", "content": f"Error: {e}"})
                        st.rerun()

            # ── Save as flashcard + Go to deck ──────────────────────────────
            with chat_col2:
                # Subtopic deck jump button (uses q_id_for_sub from header block above)
                _sub_deck_id = Q_SUBTOPICS.get(q.get("id", ""), (None, None))[0]
                _sub_name    = Q_SUBTOPICS.get(q.get("id", ""), (None, None))[1]
                if _sub_deck_id and _sub_name:
                    btn_label = f"→ {_sub_name.split('&')[0].strip()}"
                    if st.button(btn_label, key=f"go_deck_{q_id}", use_container_width=True,
                                 help=f"Go to {_sub_name} flashcard deck"):
                        st.session_state.fc_view = "browse"
                        st.session_state.fc_active_deck_id = _sub_deck_id
                        nav("flashcards")
                        st.rerun()
                if st.button("+ Flashcard", key=f"fc_{q_id}", use_container_width=True):
                    if st.session_state.fc_data is None:
                        st.session_state.fc_data = load_flashcard_data()
                    # Toggle editor open, reset if switching question
                    if st.session_state.fc_editor_q_id != q_id:
                        st.session_state.fc_editor_open = True
                        st.session_state.fc_editor_q_id = q_id
                    else:
                        st.session_state.fc_editor_open = not st.session_state.fc_editor_open
                    st.rerun()

            # ── Flashcard editor panel ──────────────────────────────────────
            if st.session_state.fc_editor_open and st.session_state.fc_editor_q_id == q_id:
                if st.session_state.fc_data is None:
                    st.session_state.fc_data = load_flashcard_data()
                fc_data = st.session_state.fc_data
                decks = fc_data.get("decks", [])

                default_back = q["answer"] + ". " + q["options"][q["answer"]] + "\n\n" + q["explanation"]

                # Work out suggested decks for this topic
                q_topic = q.get("topic", "")
                q_colour = TOPICS.get(q_topic, {}).get("colour", "#4f9cf9")
                suggestions = TOPIC_DECK_SUGGESTIONS.get(q_topic, [])
                suggested_names = [name for _, name in suggestions]

                # Build suggested deck chips HTML
                chips_html = "".join(
                    f'<span style="display:inline-block;background:{q_colour}18;border:1px solid {q_colour}55;' +
                    f'border-radius:4px;padding:3px 10px;font-family:IBM Plex Mono,monospace;' +
                    f'font-size:10px;color:{q_colour};margin:0 4px 4px 0;letter-spacing:0.04em;">{name}</span>'
                    for _, name in suggestions
                )

                st.markdown(
                    f'<div style="background:#161b27;border:1px solid #252e42;border-left:3px solid {q_colour};' +
                    f'border-radius:8px;padding:16px 20px;margin:12px 0 4px;">' +
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">' +
                    f'<div style="width:3px;height:14px;background:{q_colour};border-radius:2px;"></div>' +
                    f'<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{q_colour};' +
                    f'text-transform:uppercase;letter-spacing:0.08em;margin:0;">Suggested decks — {q_topic}</p>' +
                    f'</div>' +
                    f'<div style="flex-wrap:wrap;display:flex;">{chips_html}</div>' +
                    f'</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div style="background:#161b27;border:1px solid #252e42;border-radius:8px;padding:20px 24px;margin:4px 0;">',
                    unsafe_allow_html=True
                )

                # Deck selector — pre-select first suggested deck if available
                if decks:
                    deck_names = [d["name"] for d in decks]
                    # Find index of first suggested deck
                    default_idx = 0
                    for sname in suggested_names:
                        if sname in deck_names:
                            default_idx = deck_names.index(sname)
                            break
                    chosen_deck_name = st.selectbox(
                        "Deck", deck_names,
                        index=default_idx,
                        key=f"fc_deck_sel_{q_id}",
                        label_visibility="collapsed"
                    )
                    chosen_deck = next((d for d in decks if d["name"] == chosen_deck_name), decks[0])
                    dc = chosen_deck.get("colour", "#4f9cf9")
                    st.markdown(f'<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{dc};margin:0 0 14px;">{len(chosen_deck["cards"])} cards in deck</p>', unsafe_allow_html=True)
                else:
                    st.warning("No decks found — create one in the Flashcards section first.")
                    chosen_deck = None

                st.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 6px;">Front</p>', unsafe_allow_html=True)
                edited_front = st.text_area(
                    "Front", value=q["question"], height=100,
                    key=f"fc_front_{q_id}", label_visibility="collapsed"
                )

                st.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin:6px 0;">Back</p>', unsafe_allow_html=True)
                edited_back = st.text_area(
                    "Back", value=default_back, height=160,
                    key=f"fc_back_{q_id}", label_visibility="collapsed"
                )

                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                save_col, cancel_col = st.columns(2)
                with save_col:
                    if st.button("Save Card", key=f"fc_save_{q_id}", use_container_width=True,
                                 disabled=(chosen_deck is None)):
                        new_card = {
                            "id": f"mcq_{uuid.uuid4().hex[:8]}",
                            "front": edited_front.strip(),
                            "back": edited_back.strip(),
                            "topic": q["topic"],
                            "interval": 1, "repetitions": 0, "ease_factor": 2.5,
                            "next_review": None, "last_grade": None,
                        }
                        chosen_deck["cards"].append(new_card)
                        save_flashcard_data(fc_data)
                        st.session_state.fc_data = fc_data
                        st.session_state.fc_editor_open = False
                        st.toast(f"Saved to {chosen_deck['name']}!")
                        st.rerun()
                with cancel_col:
                    if st.button("Cancel", key=f"fc_cancel_{q_id}", use_container_width=True):
                        st.session_state.fc_editor_open = False
                        st.rerun()

            st.markdown("")

            # ── Navigation ─────────────────────────────────────────────────
            if st.button("Next Question →", use_container_width=True):
                # Record result
                result_entry = {
                    "question": q["question"],
                    "options": q["options"],
                    "answer": q["answer"],
                    "selected": sel,
                    "correct": correct,
                    "topic": q["topic"],
                    "explanation": q["explanation"],
                    "id": q.get("id", ""),
                    "svg": q.get("svg"),
                    "svg_caption": q.get("svg_caption"),
                }
                session["results"].append(result_entry)
                session["idx"] += 1
                # Persist this question ID so it won't be prioritised in future sessions
                q_id = q.get("id", "")
                if q_id and not q_id.startswith("ai_"):
                    answered = st.session_state.stats.get("answered_ids", [])
                    if q_id not in answered:
                        answered.append(q_id)
                        st.session_state.stats["answered_ids"] = answered
                        save_stats(st.session_state.stats)
                # Save for resume
                save_session_state(session)
                st.session_state.current_q = None
                st.session_state.selected_answer = None
                st.session_state.submitted = False
                st.session_state.start_time = None
                st.session_state.chat_messages = []
                st.session_state.chat_q_id = None
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: STATS
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.page == "stats":
    st.markdown("""
    <div style="padding-bottom:28px;border-bottom:1px solid #252e42;margin-bottom:28px;">
        <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 8px;">Analytics</p>
        <h2 style="font-family:Fraunces,serif;font-size:36px;font-weight:300;letter-spacing:-0.03em;margin:0;color:#e8edf5;">Performance</h2>
    </div>
    """, unsafe_allow_html=True)

    total_q    = sum(v["total"] for v in stats["topic_totals"].values())
    total_c    = sum(v["correct"] for v in stats["topic_totals"].values())
    overall    = int(total_c / total_q * 100) if total_q else 0
    n_sessions = len(stats["sessions"])

    # ── Top metrics ──────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("Questions", total_q)
    c2.metric("Overall", f"{overall}%")
    c3.metric("Sessions", n_sessions)

    # ── Weakest topic callout ─────────────────────────────────────────────────
    topic_pcts = {
        t: int(v["correct"] / v["total"] * 100) if v["total"] else None
        for t, v in stats["topic_totals"].items()
    }
    scored = {t: p for t, p in topic_pcts.items() if p is not None}
    if scored:
        weakest = min(scored, key=scored.get)
        strongest = max(scored, key=scored.get)
        w_colour = TOPICS[weakest]["colour"] if weakest in TOPICS else "#f87171"
        s_colour = TOPICS[strongest]["colour"] if strongest in TOPICS else "#4ade80"
        wc1, wc2 = st.columns(2)
        with wc1:
            st.markdown(f"""
            <div style="background:#1c0a0a;border:1px solid #7f1d1d;border-radius:10px;padding:18px 22px;margin-top:12px;">
                <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#f87171;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 6px;">Focus here</p>
                <p style="font-size:15px;color:#e8edf5;margin:0 0 2px;font-weight:500;">{weakest}</p>
                <p style="font-family:Fraunces,serif;font-size:28px;font-weight:300;color:#f87171;margin:0;">{scored[weakest]}%</p>
            </div>
            """, unsafe_allow_html=True)
        with wc2:
            st.markdown(f"""
            <div style="background:#0a1f14;border:1px solid #14532d;border-radius:10px;padding:18px 22px;margin-top:12px;">
                <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#4ade80;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 6px;">Strongest</p>
                <p style="font-size:15px;color:#e8edf5;margin:0 0 2px;font-weight:500;">{strongest}</p>
                <p style="font-family:Fraunces,serif;font-size:28px;font-weight:300;color:#4ade80;margin:0;">{scored[strongest]}%</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Sparkline — last 10 sessions ─────────────────────────────────────────
    if len(stats["sessions"]) >= 2:
        recent_10 = stats["sessions"][-10:]
        pts = [int(s["correct"] / s["total"] * 100) if s["total"] else 0 for s in recent_10]
        n = len(pts)
        W, H = 600, 80
        x_step = W / max(n - 1, 1)
        coords = [(i * x_step, H - (p / 100 * H)) for i, p in enumerate(pts)]
        polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
        # fill path
        fill_path = f"M {coords[0][0]:.1f},{H} " + " ".join(f"L {x:.1f},{y:.1f}" for x, y in coords) + f" L {coords[-1][0]:.1f},{H} Z"
        trend = pts[-1] - pts[0]
        trend_c = "#4ade80" if trend >= 0 else "#f87171"
        trend_str = f"+{trend}%" if trend >= 0 else f"{trend}%"
        st.markdown(f"""
        <div style="background:#161b27;border:1px solid #252e42;border-radius:10px;padding:20px 24px;margin:20px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin:0;">Score trend — last {n} sessions</p>
                <span style="font-family:IBM Plex Mono,monospace;font-size:12px;color:{trend_c};">{trend_str}</span>
            </div>
            <svg viewBox="0 0 {W} {H}" width="100%" height="80" preserveAspectRatio="none">
                <defs>
                    <linearGradient id="spark_fill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#4f9cf9" stop-opacity="0.25"/>
                        <stop offset="100%" stop-color="#4f9cf9" stop-opacity="0"/>
                    </linearGradient>
                </defs>
                <path d="{fill_path}" fill="url(#spark_fill)"/>
                <polyline points="{polyline}" fill="none" stroke="#4f9cf9" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
                {"".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#4f9cf9"/>' for x, y in [coords[-1]])}
                <line x1="0" y1="{H - 60/100*H:.1f}" x2="{W}" y2="{H - 60/100*H:.1f}"
                      stroke="#252e42" stroke-width="1" stroke-dasharray="4,4"/>
            </svg>
            <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;margin:4px 0 0;text-align:right;">60% pass mark shown</p>
        </div>
        """, unsafe_allow_html=True)

    # ── By topic ─────────────────────────────────────────────────────────────
    st.markdown("""
    <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;
              text-transform:uppercase;letter-spacing:0.08em;margin:8px 0 14px;">By Topic</p>
    """, unsafe_allow_html=True)

    for topic, meta in TOPICS.items():
        t = stats["topic_totals"].get(topic, {"correct": 0, "total": 0})
        pct = int(t["correct"] / t["total"] * 100) if t["total"] else 0
        c = meta["colour"]
        st.markdown(f"""
        <div style="background:#161b27;border:1px solid #252e42;border-radius:10px;
                    padding:18px 22px;margin-bottom:8px;border-left:3px solid {c};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                <span style="font-family:IBM Plex Sans,sans-serif;font-size:15px;font-weight:400;color:#e8edf5;">{topic}</span>
                <div style="text-align:right;">
                    <span style="font-family:Fraunces,serif;font-size:22px;font-weight:300;color:{c};">{pct}%</span>
                    <span style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#6b7a99;margin-left:8px;">{t["correct"]}/{t["total"]}</span>
                </div>
            </div>
            <div style="background:#252e42;border-radius:2px;height:4px;">
                <div style="width:{pct}%;height:4px;background:{c};border-radius:2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
    if st.button("Reset All Stats", key="reset_stats"):
        st.session_state.stats = default_stats()
        save_stats(st.session_state.stats)
        st.success("Stats reset.")
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: TEXTBOOK
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.page == "textbook":
    import base64

    st.markdown("""
    <div style="padding-bottom:28px;border-bottom:1px solid #252e42;margin-bottom:28px;">
        <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 8px;">Reference</p>
        <h2 style="font-family:Fraunces,serif;font-size:36px;font-weight:300;letter-spacing:-0.03em;margin:0;color:#e8edf5;">Textbook Library</h2>
    </div>
    """, unsafe_allow_html=True)

    # Load docs if not yet loaded
    if st.session_state.textbook_docs is None:
        with st.spinner("Loading library…"):
            st.session_state.textbook_docs = load_textbook_docs()

    docs = st.session_state.textbook_docs

    # ── Upload section ────────────────────────────────────────────────────────
    with st.expander("➕ Upload New Document"):
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            upload_name = st.text_input("Document title", placeholder="e.g. CV Physiology — Primary FRCA", key="tb_name")
        with col_u2:
            upload_topic = st.selectbox(
                "Topic",
                ["Physiology", "Pharmacology", "Physics & Clinical Measurement", "Clinical Anaesthesia", "Other"],
                key="tb_topic"
            )
        uploaded_file = st.file_uploader("PDF file", type=["pdf"], key="tb_file")

        if uploaded_file and upload_name.strip():
            if st.button("Upload to Library", key="tb_upload_btn"):
                with st.spinner("Uploading…"):
                    raw = uploaded_file.read()
                    b64 = base64.b64encode(raw).decode("utf-8")
                    ok = save_textbook_doc(upload_name.strip(), upload_topic, b64)
                    if ok:
                        st.success(f"\'{upload_name}\' uploaded!")
                        st.session_state.textbook_docs = None  # force reload
                        st.rerun()

    st.markdown("")

    if not docs:
        st.markdown("""
        <div style="text-align:center;padding:60px 0;color:#6b7280;">
            <p style="font-size:40px;margin-bottom:12px;">📄</p>
            <p style="font-size:15px;">No documents yet — upload your first PDF above.</p>
            <p style="font-size:13px;margin-top:8px;">Tip: Start with your CV Physiology, Pharmacology, and Physics guides.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Group by topic
        from collections import defaultdict
        by_topic = defaultdict(list)
        for doc in docs:
            by_topic[doc.get("topic", "Other")].append(doc)

        # Check if a doc is open
        if "open_doc_id" not in st.session_state:
            st.session_state.open_doc_id = None

        open_id = st.session_state.open_doc_id
        open_doc = next((d for d in docs if d["id"] == open_id), None)

        if open_doc:
            # ── Split-screen: PDF + Flashcard panel ───────────────────────────
            topic_colour = TOPICS.get(open_doc.get("topic", ""), {}).get("colour", "#4f9cf9")

            # Header bar
            hc1, hc2, hc3 = st.columns([1, 4, 2])
            with hc1:
                if st.button("← Back", key="tb_back"):
                    st.session_state.open_doc_id = None
                    st.rerun()
            with hc2:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:4px 0;">
                    <div style="width:3px;height:20px;background:{topic_colour};border-radius:2px;flex-shrink:0;"></div>
                    <span style="font-family:Fraunces,serif;font-size:20px;font-weight:300;color:#e8edf5;letter-spacing:-0.02em;">{open_doc["name"]}</span>
                    <span style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{topic_colour};border:1px solid {topic_colour}55;border-radius:3px;padding:2px 8px;flex-shrink:0;">{open_doc.get("topic","Other")}</span>
                </div>
                """, unsafe_allow_html=True)
            with hc3:
                b64 = open_doc["data"]
                raw_bytes = base64.b64decode(b64)
                st.download_button("Download PDF", data=raw_bytes,
                    file_name=f"{open_doc['name'].replace(' ','_')}.pdf",
                    mime="application/pdf", key="tb_dl", use_container_width=True)

            st.markdown('<div style="border-bottom:1px solid #252e42;margin:12px 0 20px;"></div>', unsafe_allow_html=True)

            # Load flashcard data
            if st.session_state.fc_data is None:
                st.session_state.fc_data = load_flashcard_data()
            fc_data = st.session_state.fc_data
            decks = fc_data.get("decks", [])

            # Split layout: PDF left (60%), flashcard panel right (40%)
            pdf_col, fc_col = st.columns([3, 2], gap="large")

            with pdf_col:
                try:
                    from streamlit_pdf_viewer import pdf_viewer
                    pdf_viewer(input=raw_bytes, width=700, height=860, key=f"pdf_{open_doc['id']}")
                except ImportError:
                    st.warning("PDF viewer not installed.")

            with fc_col:
                st.markdown("""
                <div style="padding-bottom:12px;border-bottom:1px solid #252e42;margin-bottom:16px;">
                    <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 4px;">Quick Add</p>
                    <p style="font-family:Fraunces,serif;font-size:18px;font-weight:300;color:#e8edf5;margin:0;">Flashcard Panel</p>
                </div>
                """, unsafe_allow_html=True)

                if decks:
                    deck_names = [d["name"] for d in decks]
                    selected_deck_name = st.selectbox("Deck", deck_names, key="tb_fc_deck", label_visibility="collapsed")
                    active_deck = next((d for d in decks if d["name"] == selected_deck_name), decks[0])
                    deck_colour = active_deck.get("colour", "#4f9cf9")
                    st.markdown(f"""<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{deck_colour};margin:0 0 16px;">{len(active_deck["cards"])} cards &middot; {sum(1 for c in active_deck["cards"] if fc_is_due(c))} due today</p>""", unsafe_allow_html=True)
                else:
                    st.info("No decks yet — create one in Flashcards first.")
                    active_deck = None

                st.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 6px;">Front</p>', unsafe_allow_html=True)
                tb_front = st.text_area("Front", height=100,
                    placeholder="Concept or question from what you just read...",
                    key="tb_fc_front", label_visibility="collapsed")

                st.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin:6px 0;">Back</p>', unsafe_allow_html=True)
                tb_back = st.text_area("Back", height=120,
                    placeholder="Answer, mechanism, or key values...",
                    key="tb_fc_back", label_visibility="collapsed")

                if st.button("Save Card", key="tb_fc_save", use_container_width=True,
                             disabled=(not (tb_front.strip() and tb_back.strip()) or active_deck is None)):
                    new_card = {
                        "id": str(uuid.uuid4()),
                        "front": tb_front.strip(),
                        "back": tb_back.strip(),
                        "topic": open_doc.get("topic", ""),
                        "interval": 1, "repetitions": 0, "ease_factor": 2.5,
                        "next_review": None, "last_grade": None,
                    }
                    active_deck["cards"].append(new_card)
                    save_flashcard_data(fc_data)
                    st.session_state.fc_data = fc_data
                    st.toast("Card saved!")
                    st.rerun()

                st.markdown('<div style="border-top:1px solid #252e42;margin:20px 0 14px;"></div>', unsafe_allow_html=True)
                st.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 10px;">Cards in this deck</p>', unsafe_allow_html=True)

                if active_deck and active_deck["cards"]:
                    recent_cards = list(reversed(active_deck["cards"]))[:6]
                    for rc in recent_cards:
                        due_colour = "#4ade80" if fc_is_due(rc) else "#6b7a99"
                        due_label  = "Due" if fc_is_due(rc) else fc_days_until(rc)
                        front_preview = rc["front"][:55] + ("..." if len(rc["front"]) > 55 else "")
                        st.markdown(f"""
                        <div style="background:#161b27;border:1px solid #252e42;border-radius:6px;padding:10px 14px;margin-bottom:6px;">
                            <p style="font-size:13px;color:#e8edf5;margin:0 0 4px;line-height:1.4;">{front_preview}</p>
                            <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{due_colour};margin:0;">{due_label}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown('<p style="font-size:13px;color:#6b7a99;text-align:center;padding:20px 0;">No cards yet in this deck.</p>', unsafe_allow_html=True)
        else:
            # ── Library grid ─────────────────────────────────────────────────
            topic_order = list(TOPICS.keys()) + ["Other"]
            for topic in topic_order:
                topic_docs = by_topic.get(topic, [])
                if not topic_docs:
                    continue

                colour = TOPICS.get(topic, {}).get("colour", "#6b7280")
                emoji  = TOPICS.get(topic, {}).get("emoji", "📄")
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:12px;margin:28px 0 12px;padding-bottom:10px;border-bottom:1px solid #252e42;">
                    <div style="width:2px;height:20px;background:{colour};border-radius:1px;"></div>
                    <h3 style="font-size:13px;font-weight:500;margin:0;letter-spacing:0.01em;color:#e8edf5;">{topic}</h3>
                    <span style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;">
                        {len(topic_docs)} doc{"s" if len(topic_docs) != 1 else ""}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                for doc in topic_docs:
                    uploaded_str = ""
                    try:
                        uploaded_str = datetime.fromisoformat(doc.get("uploaded","")).strftime("%d %b %Y")
                    except Exception:
                        pass

                    col_info, col_open, col_del = st.columns([5, 1, 1])
                    with col_info:
                        st.markdown(f"""
                        <div style="background:#161b27;border:1px solid #252e42;border-radius:6px;
                                    padding:14px 18px;border-left:3px solid {colour};">
                            <p style="font-size:14px;font-weight:500;margin:0 0 4px;color:#e8edf5;">{doc["name"]}</p>
                            <p style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#6b7a99;margin:0;">
                                Uploaded {uploaded_str}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_open:
                        st.markdown("<div style=\"margin-top:8px;\">", unsafe_allow_html=True)
                        if st.button("Open", key=f"open_{doc['id']}", use_container_width=True):
                            st.session_state.open_doc_id = doc["id"]
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    with col_del:
                        st.markdown("<div style=\"margin-top:8px;\">", unsafe_allow_html=True)
                        if st.button("🗑", key=f"del_tb_{doc['id']}", use_container_width=True):
                            if delete_textbook_doc(doc["id"]):
                                st.session_state.textbook_docs = None
                                st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: FLASHCARDS
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.page == "flashcards":

    # ── Load data ─────────────────────────────────────────────────────────────
    if st.session_state.fc_data is None:
        st.session_state.fc_data = load_flashcard_data()
    fc_data = st.session_state.fc_data
    decks = fc_data.get("decks", [])
    if not decks:
        decks = [
        # ── Physiology ──────────────────────────────────────────────────────
        {"id": "phy_resp",   "name": "Respiratory Physiology",         "colour": "#2dd4bf", "cards": []},
        {"id": "phy_cvs",    "name": "Cardiovascular Physiology",      "colour": "#2dd4bf", "cards": []},
        {"id": "phy_neuro",  "name": "Neurophysiology & Pain",         "colour": "#2dd4bf", "cards": []},
        {"id": "phy_renal",  "name": "Renal & Acid-Base",              "colour": "#2dd4bf", "cards": []},
        {"id": "phy_gi",     "name": "Hepatic, GI & Metabolic",        "colour": "#2dd4bf", "cards": []},
        {"id": "phy_haem",   "name": "Haematology & Immunology",       "colour": "#2dd4bf", "cards": []},
        {"id": "phy_endo",   "name": "Endocrine & Obstetric Physiology","colour": "#2dd4bf", "cards": []},
        # ── Pharmacology ────────────────────────────────────────────────────
        {"id": "ph_inh",     "name": "Inhalational Agents",            "colour": "#a78bfa", "cards": []},
        {"id": "ph_iv",      "name": "IV Induction Agents & Sedatives","colour": "#a78bfa", "cards": []},
        {"id": "ph_opioid",  "name": "Opioids & Analgesics",           "colour": "#a78bfa", "cards": []},
        {"id": "ph_nmb",     "name": "NMBs & Reversal",                "colour": "#a78bfa", "cards": []},
        {"id": "ph_la",      "name": "Local Anaesthetics",             "colour": "#a78bfa", "cards": []},
        {"id": "ph_cvd",     "name": "Cardiovascular Drugs",           "colour": "#a78bfa", "cards": []},
        {"id": "ph_other",   "name": "Antiemetics, Antacids & Other",  "colour": "#a78bfa", "cards": []},
        # ── Physics & Clinical Measurement ──────────────────────────────────
        {"id": "phx_elec",   "name": "Electricity, Safety & Equipment","colour": "#38bdf8", "cards": []},
        {"id": "phx_gas",    "name": "Gas Laws & Vaporisers",          "colour": "#38bdf8", "cards": []},
        {"id": "phx_mon",    "name": "Monitoring (CO, Neuro, Temp)",   "colour": "#38bdf8", "cards": []},
        {"id": "phx_resp",   "name": "Respiratory Mechanics & Spirometry","colour": "#38bdf8","cards": []},
        {"id": "phx_stats",  "name": "Statistics & Clinical Trials",   "colour": "#38bdf8", "cards": []},
        # ── Clinical Anaesthesia ─────────────────────────────────────────────
        {"id": "ca_airway",  "name": "Airway Anatomy & Management",    "colour": "#fb923c", "cards": []},
        {"id": "ca_regional","name": "Regional Anatomy & Blocks",      "colour": "#fb923c", "cards": []},
        {"id": "ca_preop",   "name": "Preoperative Assessment",        "colour": "#fb923c", "cards": []},
        {"id": "ca_emerg",   "name": "Perioperative Emergencies",      "colour": "#fb923c", "cards": []},
        {"id": "ca_obs",     "name": "Obstetric Anaesthesia",          "colour": "#fb923c", "cards": []},
        {"id": "ca_paeds",   "name": "Paediatric Anaesthesia",         "colour": "#fb923c", "cards": []},
    ]
        fc_data["decks"] = decks

    # ── Streak calculation ────────────────────────────────────────────────────
    streak_data = fc_data.get("streak", {"last_study_date": None, "count": 0})
    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_date = streak_data.get("last_study_date")
    streak_count = streak_data.get("count", 0)
    if last_date == today_str:
        pass  # already studied today
    elif last_date == yesterday_str:
        pass  # streak intact, not yet studied today
    elif last_date is None:
        streak_count = 0
    else:
        streak_count = 0  # streak broken

    fc_view = st.session_state.get("fc_view", "decks")

    # ── DECK LIST VIEW ────────────────────────────────────────────────────────
    if fc_view == "decks":

        # Header
        st.markdown("""
        <div style="padding-bottom:24px;border-bottom:1px solid #252e42;margin-bottom:28px;">
            <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;
                      letter-spacing:0.1em;text-transform:uppercase;margin:0 0 8px;">Spaced Repetition</p>
            <h2 style="font-family:Fraunces,serif;font-size:36px;font-weight:300;
                       letter-spacing:-0.03em;margin:0;color:#e8edf5;">Flashcards</h2>
        </div>
        """, unsafe_allow_html=True)

        # ── Streak + Study All row ────────────────────────────────────────────
        all_due = [c for deck in decks for c in deck["cards"] if fc_is_due(c)]
        all_due_count = len(all_due)
        total_cards = sum(len(d["cards"]) for d in decks)

        streak_icon = "🔥" if streak_count >= 1 else "○"
        streak_label = f"{streak_count} day streak" if streak_count > 1 else ("1 day streak" if streak_count == 1 else "No streak yet")

        col_streak, col_studyall = st.columns([1, 2])
        with col_streak:
            st.markdown(f"""
            <div style="background:#161b27;border:1px solid #252e42;border-radius:10px;
                        padding:18px 20px;text-align:center;">
                <p style="font-size:28px;margin:0 0 4px;">{streak_icon}</p>
                <p style="font-family:Fraunces,serif;font-size:24px;font-weight:300;
                          color:#e8edf5;margin:0 0 2px;">{streak_count}</p>
                <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;
                          text-transform:uppercase;letter-spacing:0.06em;margin:0;">day streak</p>
            </div>
            """, unsafe_allow_html=True)
        with col_studyall:
            if all_due_count > 0:
                st.markdown(f"""
                <div style="background:#0a1f14;border:1.5px solid #14532d;border-radius:10px;
                            padding:18px 20px;">
                    <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#4ade80;
                              text-transform:uppercase;letter-spacing:0.06em;margin:0 0 4px;">Reviews waiting</p>
                    <p style="font-family:Fraunces,serif;font-size:32px;font-weight:300;
                              color:#4ade80;margin:0 0 12px;line-height:1;">{all_due_count}
                        <span style="font-size:14px;color:#6b7a99;font-family:IBM Plex Mono,monospace;">
                            / {total_cards} cards
                        </span>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Study All Due ({all_due_count}) →", use_container_width=True, key="fc_study_all"):
                    # Build cross-deck queue: store (deck_id, card_id) pairs
                    import random as _random
                    cross_queue = []
                    for dk in decks:
                        for c in dk["cards"]:
                            if fc_is_due(c):
                                cross_queue.append({"deck_id": dk["id"], "card_id": c["id"]})
                    _random.shuffle(cross_queue)
                    st.session_state.fc_study_queue = cross_queue
                    st.session_state.fc_study_idx = 0
                    st.session_state.fc_flipped = False
                    st.session_state.fc_session_stats = {"again": 0, "hard": 0, "good": 0, "easy": 0}
                    st.session_state.fc_active_deck_id = None  # cross-deck mode
                    st.session_state.fc_view = "study"
                    st.rerun()
            else:
                st.markdown("""
                <div style="background:#161b27;border:1px solid #252e42;border-radius:10px;
                            padding:18px 20px;">
                    <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#4ade80;
                              text-transform:uppercase;letter-spacing:0.06em;margin:0 0 4px;">All caught up</p>
                    <p style="font-size:15px;color:#e8edf5;margin:0;">✓ No reviews due</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        # ── New Deck ──────────────────────────────────────────────────────────
        with st.expander("+ New Deck"):
            nd_name   = st.text_input("Deck name", placeholder="e.g. Drug Mechanisms", key="nd_name")
            nd_colours = {"Teal": "#2dd4bf", "Purple": "#a78bfa", "Blue": "#38bdf8",
                          "Amber": "#fb923c", "Green": "#4ade80", "Red": "#f87171"}
            nd_colour = st.selectbox("Colour", list(nd_colours.keys()), key="nd_colour")
            if st.button("Create Deck", key="nd_create"):
                if nd_name.strip():
                    new_deck = {"id": str(uuid.uuid4()), "name": nd_name.strip(),
                                "colour": nd_colours[nd_colour], "cards": []}
                    fc_data["decks"].append(new_deck)
                    save_flashcard_data(fc_data)
                    st.session_state.fc_data = fc_data
                    st.success(f"Deck '{nd_name}' created!")
                    st.rerun()

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── Deck cards ────────────────────────────────────────────────────────
        for deck in decks:
            total  = len(deck["cards"])
            due    = sum(1 for c in deck["cards"] if fc_is_due(c))
            colour = deck.get("colour", "#4f9cf9")
            learned = sum(1 for c in deck["cards"] if c.get("interval", 1) > 1)
            mastery_pct = int(learned / total * 100) if total > 0 else 0

            # Next review time when nothing due
            if due == 0 and total > 0:
                future_cards = [c for c in deck["cards"] if c.get("next_review")]
                if future_cards:
                    next_dt = min(datetime.fromisoformat(c["next_review"]) for c in future_cards)
                    delta = next_dt - datetime.now()
                    hrs = int(delta.total_seconds() / 3600)
                    if hrs < 1:
                        next_str = "< 1 hour"
                    elif hrs < 24:
                        next_str = f"{hrs}h"
                    else:
                        next_str = f"{delta.days}d"
                    due_display = f"Next in {next_str}"
                else:
                    due_display = "No reviews scheduled"
            else:
                due_display = None

            # Progress ring SVG
            r = 18
            circ = 2 * 3.14159 * r
            filled = circ * mastery_pct / 100
            ring_svg = (
                f'<svg width="44" height="44" viewBox="0 0 44 44">'
                f'<circle cx="22" cy="22" r="{r}" fill="none" stroke="#252e42" stroke-width="3"/>'
                f'<circle cx="22" cy="22" r="{r}" fill="none" stroke="{colour}" stroke-width="3"'
                f' stroke-dasharray="{filled:.1f} {circ:.1f}" stroke-linecap="round"'
                f' transform="rotate(-90 22 22)"/>'
                f'<text x="22" y="27" text-anchor="middle" font-family="IBM Plex Mono" font-size="9"'
                f' fill="{colour}">{mastery_pct}%</text>'
                f'</svg>'
            )

            # Deck card HTML
            if due > 0:
                due_html = (
                    f'<p style="font-family:Fraunces,serif;font-size:36px;font-weight:300;'
                    f'color:{colour};margin:0 0 2px;line-height:1;">{due}</p>'
                    f'<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;'
                    f'text-transform:uppercase;letter-spacing:0.06em;margin:0;">due</p>'
                )
            else:
                due_html = (
                    f'<p style="font-size:22px;margin:0 0 2px;">✓</p>'
                    f'<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#4ade80;margin:0;">'
                    + (due_display or "all done") + '</p>'
                )

            st.markdown(
                f'<div style="background:#161b27;border:1px solid {"#" + colour.lstrip("#") if due > 0 else "252e42"};'
                f'border-radius:12px;padding:20px 24px;margin-bottom:6px;border-left:3px solid {colour};">'
                f'<div style="display:flex;align-items:center;justify-content:space-between;">'
                f'<div style="flex:1;">'
                f'<p style="font-size:16px;font-weight:500;color:#e8edf5;margin:0 0 3px;">{deck["name"]}</p>'
                f'<p style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#6b7a99;margin:0;">'
                f'{total} cards</p>'
                f'</div>'
                f'<div style="display:flex;align-items:center;gap:20px;">'
                f'{ring_svg}'
                f'<div style="text-align:center;min-width:52px;">{due_html}</div>'
                f'</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Action row — Study CTA dominant, rest in a slim row
            if due > 0:
                btn_study, btn_browse, btn_add, btn_del = st.columns([3, 1, 1, 1])
            else:
                btn_study, btn_browse, btn_add, btn_del = st.columns([3, 1, 1, 1])

            with btn_study:
                study_label = f"Study {due} due →" if due > 0 else "Browse cards"
                if st.button(study_label, key=f"fc_study_{deck['id']}", use_container_width=True):
                    if due > 0:
                        due_cards = [c for c in deck["cards"] if fc_is_due(c)]
                        st.session_state.fc_study_queue = [{"deck_id": deck["id"], "card_id": c["id"]} for c in due_cards]
                        st.session_state.fc_study_idx = 0
                        st.session_state.fc_flipped = False
                        st.session_state.fc_session_stats = {"again": 0, "hard": 0, "good": 0, "easy": 0}
                        st.session_state.fc_active_deck_id = deck["id"]
                        st.session_state.fc_view = "study"
                        st.rerun()
                    else:
                        st.session_state.fc_active_deck_id = deck["id"]
                        st.session_state.fc_view = "browse"
                        st.rerun()
            with btn_browse:
                if st.button("Browse", key=f"fc_browse_{deck['id']}", use_container_width=True):
                    st.session_state.fc_active_deck_id = deck["id"]
                    st.session_state.fc_view = "browse"
                    st.rerun()
            with btn_add:
                if st.button("+ Card", key=f"fc_add_{deck['id']}", use_container_width=True):
                    st.session_state.fc_active_deck_id = deck["id"]
                    st.session_state.fc_view = "add"
                    st.rerun()
            with btn_del:
                if st.button("🗑", key=f"fc_del_{deck['id']}", use_container_width=True):
                    fc_data["decks"] = [d for d in fc_data["decks"] if d["id"] != deck["id"]]
                    save_flashcard_data(fc_data)
                    st.session_state.fc_data = fc_data
                    st.rerun()

            st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    # ── ADD CARD VIEW ─────────────────────────────────────────────────────────
    elif fc_view == "add":
        deck = next((d for d in decks if d["id"] == st.session_state.get("fc_active_deck_id")), decks[0])
        colour = deck.get("colour", "#4f9cf9")
        if st.button("← Decks", key="fc_back_add"):
            st.session_state.fc_view = "decks"
            st.rerun()
        st.markdown(
            f'<div style="margin:16px 0 24px;">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<div style="width:3px;height:20px;background:{colour};border-radius:2px;"></div>'
            f'<p style="font-family:Fraunces,serif;font-size:22px;font-weight:300;color:#e8edf5;margin:0;">Add Card — {deck["name"]}</p>'
            f'</div></div>',
            unsafe_allow_html=True
        )
        fc1, fc2 = st.columns(2)
        with fc1:
            st.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Front</p>', unsafe_allow_html=True)
            new_front = st.text_area("Front", height=160, placeholder="Question or concept...", key="fc_new_front", label_visibility="collapsed")
        with fc2:
            st.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Back</p>', unsafe_allow_html=True)
            new_back  = st.text_area("Back",  height=160, placeholder="Answer or explanation...", key="fc_new_back",  label_visibility="collapsed")
        st.markdown("")
        if st.button("Save Card", use_container_width=True, key="fc_save_card",
                     disabled=not (new_front.strip() and new_back.strip())):
            card = {"id": str(uuid.uuid4()), "front": new_front.strip(), "back": new_back.strip(),
                    "topic": deck["name"], "interval": 1, "repetitions": 0,
                    "ease_factor": 2.5, "next_review": None, "last_grade": None}
            deck["cards"].append(card)
            save_flashcard_data(fc_data)
            st.session_state.fc_data = fc_data
            st.toast("Card saved!")
            st.rerun()

    # ── BROWSE VIEW ───────────────────────────────────────────────────────────
    elif fc_view == "browse":
        deck = next((d for d in decks if d["id"] == st.session_state.get("fc_active_deck_id")), decks[0])
        colour = deck.get("colour", "#4f9cf9")
        b_col1, b_col2 = st.columns([1, 4])
        with b_col1:
            if st.button("← Decks", key="fc_back_browse"):
                st.session_state.fc_view = "decks"
                st.rerun()
        with b_col2:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;padding:4px 0;">'
                f'<div style="width:3px;height:18px;background:{colour};border-radius:2px;"></div>'
                f'<p style="font-family:Fraunces,serif;font-size:20px;font-weight:300;color:#e8edf5;margin:0;">{deck["name"]}</p>'
                f'<span style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#6b7a99;">'
                f'{len(deck["cards"])} cards &middot; {sum(1 for c in deck["cards"] if fc_is_due(c))} due</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        if not deck["cards"]:
            st.markdown('<p style="color:#6b7a99;text-align:center;padding:60px 0;">No cards yet — add your first one.</p>', unsafe_allow_html=True)
            if st.button("+ Add Card", use_container_width=True, key="browse_add_cta"):
                st.session_state.fc_view = "add"
                st.rerun()
        else:
            for card in deck["cards"]:
                is_due = fc_is_due(card)
                due_label = "Due now" if is_due else fc_days_until(card)
                badge_c = "#4ade80" if is_due else "#6b7a99"
                with st.expander(card["front"][:80] + ("…" if len(card["front"]) > 80 else "")):
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        st.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Front</p>', unsafe_allow_html=True)
                        st.markdown(f'<div style="background:#1e2535;border:1px solid #252e42;border-radius:8px;padding:14px;font-size:14px;color:#e8edf5;line-height:1.6;white-space:pre-wrap;">{card["front"]}</div>', unsafe_allow_html=True)
                    with bc2:
                        st.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Back</p>', unsafe_allow_html=True)
                        st.markdown(f'<div style="background:#1e2535;border:1px solid #252e42;border-radius:8px;padding:14px;font-size:14px;color:#e8edf5;line-height:1.6;white-space:pre-wrap;">{card["back"]}</div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{badge_c};margin-top:10px;">'
                        f'{due_label} &middot; interval {card.get("interval",1)}d &middot; EF {card.get("ease_factor",2.5):.2f}</p>',
                        unsafe_allow_html=True
                    )
                    if st.button("Delete card", key=f"fc_del_card_{card['id']}"):
                        deck["cards"] = [c for c in deck["cards"] if c["id"] != card["id"]]
                        save_flashcard_data(fc_data)
                        st.session_state.fc_data = fc_data
                        st.rerun()

    # ── STUDY VIEW ────────────────────────────────────────────────────────────
    elif fc_view == "study":
        queue   = st.session_state.fc_study_queue   # list of {deck_id, card_id}
        idx     = st.session_state.fc_study_idx
        ss      = st.session_state.fc_session_stats

        # Support old format (list of strings) gracefully
        if queue and isinstance(queue[0], str):
            active_deck_id = st.session_state.get("fc_active_deck_id")
            queue = [{"deck_id": active_deck_id, "card_id": cid} for cid in queue]
            st.session_state.fc_study_queue = queue

        # ── Session complete ──────────────────────────────────────────────────
        if not queue or idx >= len(queue):
            total_reviewed = idx

            # Update streak
            streak_data2 = fc_data.get("streak", {"last_study_date": None, "count": 0})
            today_s = datetime.now().strftime("%Y-%m-%d")
            yest_s  = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            last_s  = streak_data2.get("last_study_date")
            cnt     = streak_data2.get("count", 0)
            if last_s == today_s:
                pass
            elif last_s == yest_s:
                cnt += 1
            elif last_s is None:
                cnt = 1
            else:
                cnt = 1
            streak_data2 = {"last_study_date": today_s, "count": cnt}
            fc_data["streak"] = streak_data2
            save_flashcard_data(fc_data)
            st.session_state.fc_data = fc_data

            total_correct = ss["good"] + ss["easy"]
            pct = int(total_correct / total_reviewed * 100) if total_reviewed else 0

            st.markdown(f"""
            <div style="text-align:center;padding:48px 0 36px;">
                <p style="font-size:40px;margin:0 0 8px;">{"🔥" if cnt >= 2 else "✓"}</p>
                <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;
                          letter-spacing:0.1em;text-transform:uppercase;margin:0 0 12px;">Session complete</p>
                <h2 style="font-family:Fraunces,serif;font-size:64px;font-weight:300;
                           letter-spacing:-0.04em;margin:0 0 4px;color:#4ade80;line-height:1;">{total_reviewed}</h2>
                <p style="font-size:14px;color:#6b7a99;margin:0 0 6px;">cards reviewed</p>
                <p style="font-family:IBM Plex Mono,monospace;font-size:12px;color:#e8edf5;">
                    {cnt} day streak 🔥</p>
            </div>
            """, unsafe_allow_html=True)

            sc1, sc2, sc3, sc4 = st.columns(4)
            for col, (label, key, col_c) in zip(
                [sc1, sc2, sc3, sc4],
                [("Again", "again", "#f87171"), ("Hard", "hard", "#fb923c"),
                 ("Good",  "good",  "#fbbf24"), ("Easy", "easy",  "#4ade80")]
            ):
                with col:
                    st.markdown(f"""
                    <div style="background:#161b27;border:1px solid #252e42;border-radius:10px;
                                padding:16px;text-align:center;">
                        <p style="font-family:Fraunces,serif;font-size:32px;font-weight:300;
                                  color:{col_c};margin:0 0 4px;">{ss[key]}</p>
                        <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;
                                  text-transform:uppercase;letter-spacing:0.06em;margin:0;">{label}</p>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
            if st.button("Back to Decks →", use_container_width=True, key="fc_back_done"):
                st.session_state.fc_view = "decks"
                st.session_state.fc_study_queue = []
                st.session_state.fc_study_idx = 0
                st.session_state.fc_session_stats = {"again": 0, "hard": 0, "good": 0, "easy": 0}
                st.rerun()

        else:
            # ── Active card ───────────────────────────────────────────────────
            item     = queue[idx]
            deck_id  = item["deck_id"]
            card_id  = item["card_id"]
            deck     = next((d for d in decks if d["id"] == deck_id), decks[0])
            card     = next((c for c in deck["cards"] if c["id"] == card_id), None)

            if not card:
                st.session_state.fc_study_idx += 1
                st.rerun()

            colour = TOPICS.get(card.get("topic", ""), {}).get("colour", deck.get("colour", "#4f9cf9"))

            # Progress bar + counter
            prog_pct = int(idx / len(queue) * 100)
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
                f'<span style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#6b7a99;">'
                f'{idx + 1} / {len(queue)}</span>'
                f'<span style="font-family:IBM Plex Mono,monospace;font-size:11px;color:{colour};">'
                f'{deck["name"]}</span>'
                f'</div>'
                f'<div style="background:#252e42;border-radius:2px;height:3px;margin-bottom:28px;">'
                f'<div style="width:{prog_pct}%;height:3px;background:{colour};border-radius:2px;"></div>'
                f'</div>',
                unsafe_allow_html=True
            )

            if not st.session_state.fc_flipped:
                # ── Front ─────────────────────────────────────────────────────
                st.markdown(
                    f'<div style="background:#161b27;border:1px solid #252e42;border-radius:12px;'
                    f'padding:48px 40px;text-align:center;min-height:240px;border-top:3px solid {colour};">'
                    f'<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;'
                    f'text-transform:uppercase;letter-spacing:0.08em;margin:0 0 24px;">Question</p>'
                    f'<p style="font-family:Fraunces,serif;font-size:22px;font-weight:300;'
                    f'line-height:1.6;color:#e8edf5;margin:0;white-space:pre-wrap;">{card["front"]}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
                if st.button("Reveal Answer →", use_container_width=True, key="fc_reveal"):
                    st.session_state.fc_flipped = True
                    st.rerun()

            else:
                # ── Back ──────────────────────────────────────────────────────
                st.markdown(
                    f'<div style="background:#161b27;border:1.5px solid {colour};border-radius:12px;'
                    f'padding:48px 40px;min-height:240px;">'
                    f'<p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;'
                    f'text-transform:uppercase;letter-spacing:0.08em;margin:0 0 20px;">Answer</p>'
                    f'<p style="font-family:IBM Plex Sans,sans-serif;font-size:16px;'
                    f'line-height:1.8;color:#e8edf5;margin:0;white-space:pre-wrap;">{card["back"]}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
                st.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#6b7a99;text-align:center;margin-bottom:14px;">How well did you know this?</p>', unsafe_allow_html=True)

                ef   = card.get("ease_factor", 2.5)
                intv = card.get("interval", 1)
                previews = ["< 1d", "tomorrow", f"{max(1,round(intv*ef))}d", f"{max(1,round(intv*ef*1.3))}d"]
                grades   = [("Again", "again", 0, "#f87171"),
                            ("Hard",  "hard",  1, "#fb923c"),
                            ("Good",  "good",  2, "#fbbf24"),
                            ("Easy",  "easy",  3, "#4ade80")]

                # Style each grade button by its key using Streamlit's element id
                # Inject CSS that targets buttons inside each column slot
                st.markdown(f"""<style>
                /* Grade button shared */
                [data-testid="stHorizontalBlock"] .stButton > button {{
                    padding: 14px 8px !important;
                    min-height: 68px !important;
                    white-space: pre-line !important;
                    line-height: 1.5 !important;
                    font-size: 13px !important;
                    text-align: center !important;
                }}
                /* Again — col 1 */
                [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button {{
                    border-color: #f87171 !important; color: #f87171 !important;
                }}
                [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button:hover {{
                    background: #f8717122 !important;
                }}
                /* Hard — col 2 */
                [data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton > button {{
                    border-color: #fb923c !important; color: #fb923c !important;
                }}
                [data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton > button:hover {{
                    background: #fb923c22 !important;
                }}
                /* Good — col 3 */
                [data-testid="stHorizontalBlock"] > div:nth-child(3) .stButton > button {{
                    border-color: #fbbf24 !important; color: #fbbf24 !important;
                }}
                [data-testid="stHorizontalBlock"] > div:nth-child(3) .stButton > button:hover {{
                    background: #fbbf2422 !important;
                }}
                /* Easy — col 4 */
                [data-testid="stHorizontalBlock"] > div:nth-child(4) .stButton > button {{
                    border-color: #4ade80 !important; color: #4ade80 !important;
                }}
                [data-testid="stHorizontalBlock"] > div:nth-child(4) .stButton > button:hover {{
                    background: #4ade8022 !important;
                }}
                </style>""", unsafe_allow_html=True)

                g_cols = st.columns(4)
                for col, (label, key, grade, col_c) in zip(g_cols, grades):
                    with col:
                        if st.button(f"{previews[grade]}\n{label}", key=f"fc_grade_{grade}", use_container_width=True):
                            updated = sm2(card, grade)
                            card_idx = next((i for i, c in enumerate(deck["cards"]) if c["id"] == card["id"]), None)
                            if card_idx is not None:
                                deck["cards"][card_idx] = updated
                            save_flashcard_data(fc_data)
                            st.session_state.fc_data = fc_data
                            st.session_state.fc_session_stats[key] += 1
                            st.session_state.fc_study_idx += 1
                            st.session_state.fc_flipped = False
                            st.rerun()

    # Persist fc_view in session state
    if "fc_view" not in st.session_state:
        st.session_state.fc_view = "decks"
