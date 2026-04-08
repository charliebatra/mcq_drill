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
    "phy_gi001": ("phy_gi", "Hepatic, GI & Metabolic"),
    "phy_gi002": ("phy_gi", "Hepatic, GI & Metabolic"),
    "phy_gi003": ("phy_gi", "Hepatic, GI & Metabolic"),
    "phy_gi004": ("phy_gi", "Hepatic, GI & Metabolic"),
    "phy_gi005": ("phy_gi", "Hepatic, GI & Metabolic"),
    "phy_gi006": ("phy_gi", "Hepatic, GI & Metabolic"),
    "phy_gi007": ("phy_gi", "Hepatic, GI & Metabolic"),
    "phy_gi008": ("phy_gi", "Hepatic, GI & Metabolic"),
    "ca_paeds001": ("ca_paeds", "Paediatric Anaesthesia"),
    "ca_paeds002": ("ca_paeds", "Paediatric Anaesthesia"),
    "ca_paeds003": ("ca_paeds", "Paediatric Anaesthesia"),
    "ca_paeds004": ("ca_paeds", "Paediatric Anaesthesia"),
    "ca_paeds005": ("ca_paeds", "Paediatric Anaesthesia"),
    "ca_paeds006": ("ca_paeds", "Paediatric Anaesthesia"),
    "ca_paeds007": ("ca_paeds", "Paediatric Anaesthesia"),
    "ca_paeds008": ("ca_paeds", "Paediatric Anaesthesia"),
    "ph_la002": ("ph_la", "Local Anaesthetics"),
    "ph_la003": ("ph_la", "Local Anaesthetics"),
    "ph_la004": ("ph_la", "Local Anaesthetics"),
    "ph_la005": ("ph_la", "Local Anaesthetics"),
    "ph_la006": ("ph_la", "Local Anaesthetics"),
    "ph_la007": ("ph_la", "Local Anaesthetics"),
    "ph_cvd002": ("ph_cvd", "Cardiovascular Drugs"),
    "ph_cvd003": ("ph_cvd", "Cardiovascular Drugs"),
    "ph_cvd004": ("ph_cvd", "Cardiovascular Drugs"),
    "ph_cvd005": ("ph_cvd", "Cardiovascular Drugs"),
    "ph_cvd006": ("ph_cvd", "Cardiovascular Drugs"),
    "ph_cvd007": ("ph_cvd", "Cardiovascular Drugs"),
    "phy_endo002": ("phy_endo", "Endocrine & Obstetric Physiology"),
    "phy_endo003": ("phy_endo", "Endocrine & Obstetric Physiology"),
    "phy_endo004": ("phy_endo", "Endocrine & Obstetric Physiology"),
    "phy_endo005": ("phy_endo", "Endocrine & Obstetric Physiology"),
    "phy_endo006": ("phy_endo", "Endocrine & Obstetric Physiology"),
    "phy_endo007": ("phy_endo", "Endocrine & Obstetric Physiology"),
    "phy_haem002": ("phy_haem", "Haematology & Immunology"),
    "phy_haem003": ("phy_haem", "Haematology & Immunology"),
    "phy_haem004": ("phy_haem", "Haematology & Immunology"),
    "phy_haem005": ("phy_haem", "Haematology & Immunology"),
    "phy_haem006": ("phy_haem", "Haematology & Immunology"),
    "phy_neuro003": ("phy_neuro", "Neurophysiology & Pain"),
    "phy_neuro004": ("phy_neuro", "Neurophysiology & Pain"),
    "phy_neuro005": ("phy_neuro", "Neurophysiology & Pain"),
    "phy_neuro006": ("phy_neuro", "Neurophysiology & Pain"),
    "phy_neuro007": ("phy_neuro", "Neurophysiology & Pain"),
    "phx_resp003": ("phx_resp", "Respiratory Mechanics & Spirometry"),
    "phx_resp004": ("phx_resp", "Respiratory Mechanics & Spirometry"),
    "phx_resp005": ("phx_resp", "Respiratory Mechanics & Spirometry"),
    "phx_resp006": ("phx_resp", "Respiratory Mechanics & Spirometry"),
    "phx_resp007": ("phx_resp", "Respiratory Mechanics & Spirometry"),
    "phx_stats003": ("phx_stats", "Statistics & Clinical Trials"),
    "phx_stats004": ("phx_stats", "Statistics & Clinical Trials"),
    "phx_stats005": ("phx_stats", "Statistics & Clinical Trials"),
    "phx_stats006": ("phx_stats", "Statistics & Clinical Trials"),
    "phx_stats007": ("phx_stats", "Statistics & Clinical Trials"),
    "phx_elec005": ("phx_elec", "Electricity, Safety & Equipment"),
    "phx_elec006": ("phx_elec", "Electricity, Safety & Equipment"),
    "phx_elec007": ("phx_elec", "Electricity, Safety & Equipment"),
    "phx_elec008": ("phx_elec", "Electricity, Safety & Equipment"),
    "phx_elec009": ("phx_elec", "Electricity, Safety & Equipment"),
    "ca_obs004": ("ca_obs", "Obstetric Anaesthesia"),
    "ca_obs005": ("ca_obs", "Obstetric Anaesthesia"),
    "ca_obs006": ("ca_obs", "Obstetric Anaesthesia"),
    "ca_obs007": ("ca_obs", "Obstetric Anaesthesia"),
    "ca_obs008": ("ca_obs", "Obstetric Anaesthesia"),
    "ca_obs009": ("ca_obs", "Obstetric Anaesthesia"),
    "ca_preop005": ("ca_preop", "Preoperative Assessment"),
    "ca_preop006": ("ca_preop", "Preoperative Assessment"),
    "ca_preop007": ("ca_preop", "Preoperative Assessment"),
    "ca_preop008": ("ca_preop", "Preoperative Assessment"),
    "ph_other004": ("ph_other", "Antiemetics, Antacids & Other"),
    "ph_other005": ("ph_other", "Antiemetics, Antacids & Other"),
    "ph_other006": ("ph_other", "Antiemetics, Antacids & Other"),
    "ph_other007": ("ph_other", "Antiemetics, Antacids & Other"),
    "ph_other008": ("ph_other", "Antiemetics, Antacids & Other"),
    "ph_nmb005": ("ph_nmb", "NMBs & Reversal"),
    "ph_nmb006": ("ph_nmb", "NMBs & Reversal"),
    "ph_nmb007": ("ph_nmb", "NMBs & Reversal"),
    "ph_nmb008": ("ph_nmb", "NMBs & Reversal"),
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
    {
        "id": "phy026", "topic": "Physiology",
        "question": "In a normal upright lung, which zone of West's model has the highest V/Q ratio?",
        "options": {
            "A": "Zone 1 (apex)",
            "B": "Zone 2 (middle)",
            "C": "Zone 3 (base)",
            "D": "Zone 4 (extreme base)",
            "E": "V/Q is uniform throughout the upright lung",
        },
        "answer": "A",
        "explanation": "In the upright lung, ventilation and perfusion both increase from apex to base, but perfusion increases more steeply due to gravity. At the apex (Zone 1), Pa>PA>Pv may occur; alveoli are over-ventilated relative to perfusion \u2014 high V/Q (~3). At the base (Zone 3), perfusion dominates \u2014 low V/Q (~0.6). Global average V/Q is approximately 0.8.",
    },
    {
        "id": "phy027", "topic": "Physiology",
        "question": "Compliance of the respiratory system is defined as:",
        "options": {
            "A": "The pressure required to generate a given flow rate",
            "B": "The change in volume per unit change in pressure",
            "C": "The resistance to airflow in the bronchioles",
            "D": "The work done per breath",
            "E": "The ratio of tidal volume to functional residual capacity",
        },
        "answer": "B",
        "explanation": "Compliance = dV/dP (L/cmH2O). Normal total respiratory system compliance approximately 100 mL/cmH2O. Lung compliance alone approximately 200 mL/cmH2O; chest wall approximately 200 mL/cmH2O. Decreased compliance: fibrosis, ARDS, pulmonary oedema. Increased compliance: emphysema (destruction of elastic tissue).",
    },
    {
        "id": "phy028", "topic": "Physiology",
        "question": "Which of the following shifts the oxyhaemoglobin dissociation curve to the RIGHT?",
        "options": {
            "A": "Decreased temperature",
            "B": "Alkalosis (increased pH)",
            "C": "Increased 2,3-DPG",
            "D": "Foetal haemoglobin (HbF)",
            "E": "Carbon monoxide poisoning",
        },
        "answer": "C",
        "explanation": "Right shift (increased P50, reduced O2 affinity, enhanced tissue unloading): increased 2,3-DPG (altitude, anaemia, chronic hypoxia), increased CO2 (Bohr effect), acidosis (decreased pH), increased temperature. Left shift: decreased 2,3-DPG, alkalosis, hypothermia, HbF, CO poisoning (which also reduces carrying capacity).",
    },
    {
        "id": "phy029", "topic": "Physiology",
        "question": "What is the approximate alveolar partial pressure of oxygen (PAO2) at sea level in a healthy person breathing room air?",
        "options": {
            "A": "21 kPa",
            "B": "13.3 kPa",
            "C": "19.8 kPa",
            "D": "8.0 kPa",
            "E": "5.3 kPa",
        },
        "answer": "B",
        "explanation": "Alveolar gas equation: PAO2 = FiO2(PB - PH2O) - PaCO2/RQ = 0.21(101.3-6.3) - 5.3/0.8 = 19.95 - 6.6 = approximately 13.4 kPa. Normal A-a gradient approximately 1-2 kPa, so PaO2 approximately 11-12 kPa on room air at sea level.",
    },
    {
        "id": "phy030", "topic": "Physiology",
        "question": "Hypoxic pulmonary vasoconstriction (HPV) is MOST beneficial during:",
        "options": {
            "A": "High-altitude acclimatisation to improve systemic oxygenation",
            "B": "One-lung ventilation to divert blood from the non-ventilated lung",
            "C": "Exercise to increase pulmonary blood flow",
            "D": "General anaesthesia to maintain cardiac output",
            "E": "Sepsis to reduce pulmonary vascular resistance",
        },
        "answer": "B",
        "explanation": "HPV is most clinically useful during one-lung ventilation (OLV), where the non-ventilated collapsed lung would otherwise receive approximately 50% of cardiac output causing massive shunt. HPV diverts blood to the ventilated lung improving V/Q matching. Volatile anaesthetics inhibit HPV dose-dependently \u2014 hence preference for TIVA in thoracic anaesthesia.",
    },
    {
        "id": "phy031", "topic": "Physiology",
        "question": "The work of breathing is increased by all of the following EXCEPT:",
        "options": {
            "A": "Increased airway resistance",
            "B": "Decreased lung compliance",
            "C": "Increased respiratory rate with constant minute ventilation",
            "D": "Increased tidal volume",
            "E": "Administration of helium-oxygen mixture (heliox)",
        },
        "answer": "E",
        "explanation": "Work of breathing = pressure times volume change. Resistance work increases with airway resistance and turbulent flow. Elastic work increases when compliance falls. Increasing RR (air trapping) or increasing TV both increase WOB. Heliox (low density gas) reduces turbulent flow and airway resistance \u2014 it REDUCES WOB, hence its use in upper airway obstruction and status asthmaticus.",
    },
    {
        "id": "phy032", "topic": "Physiology",
        "question": "During controlled mechanical ventilation, which change will INCREASE PaCO2?",
        "options": {
            "A": "Increasing respiratory rate",
            "B": "Increasing tidal volume",
            "C": "Increasing dead space (e.g. longer circuit tubing)",
            "D": "Hyperventilating the patient",
            "E": "Increasing FiO2",
        },
        "answer": "C",
        "explanation": "PaCO2 = VCO2 x 0.863 / VA. Alveolar ventilation = (TV - VD) x RR. Increasing dead space (VD) reduces alveolar ventilation without changing total minute ventilation, raising PaCO2. Increasing RR or TV increases VA and lowers PaCO2. FiO2 has no direct effect on CO2 clearance.",
    },
    {
        "id": "phy033", "topic": "Physiology",
        "question": "Which chemoreceptors respond to hypoxia, hypercapnia, AND acidosis?",
        "options": {
            "A": "Central chemoreceptors in the medulla",
            "B": "Carotid bodies",
            "C": "Aortic bodies",
            "D": "Juxtacapillary (J) receptors",
            "E": "Pulmonary stretch receptors",
        },
        "answer": "B",
        "explanation": "Carotid bodies contain glomus cells sensitive to decreased PaO2 (primary stimulus, very sensitive below 8 kPa), increased PaCO2, and decreased pH. They account for the entire ventilatory response to hypoxia. Central chemoreceptors respond to PCO2/pH in CSF \u2014 dominant CO2 sensors but insensitive to hypoxia.",
    },
    {
        "id": "phy034", "topic": "Physiology",
        "question": "Which of the following correctly describes the Starling forces governing fluid movement across a capillary wall?",
        "options": {
            "A": "Capillary hydrostatic pressure and interstitial oncotic pressure favour filtration",
            "B": "Plasma oncotic pressure and interstitial hydrostatic pressure favour filtration",
            "C": "Capillary hydrostatic pressure and interstitial oncotic pressure favour absorption",
            "D": "Plasma oncotic pressure and capillary hydrostatic pressure both favour filtration",
            "E": "Lymphatic drainage is not part of Starling equilibrium",
        },
        "answer": "A",
        "explanation": "Forces favouring FILTRATION: capillary hydrostatic pressure (pushes fluid out), interstitial oncotic pressure (pulls fluid out). Forces favouring ABSORPTION: plasma oncotic pressure (pulls fluid in), interstitial hydrostatic pressure (pushes fluid in). Lymphatics drain excess filtrate. Slight net filtration at the arterial end; absorption at the venous end.",
    },
    {
        "id": "phy035", "topic": "Physiology",
        "question": "In a pressure-volume loop of the left ventricle, where does the aortic valve OPEN?",
        "options": {
            "A": "At the end of diastole when LV pressure equals LVEDP",
            "B": "When LV pressure exceeds aortic diastolic pressure during isovolumetric contraction",
            "C": "At the start of the T wave on ECG",
            "D": "When the mitral valve closes",
            "E": "When pulmonary capillary wedge pressure is exceeded",
        },
        "answer": "B",
        "explanation": "LV P-V loop: 1) Mitral closes (isovolumetric contraction begins \u2014 volume constant, pressure rises steeply), 2) Aortic opens (when LV pressure exceeds aortic diastolic pressure \u2014 ejection begins), 3) Aortic closes (isovolumetric relaxation), 4) Mitral opens (filling). The area enclosed by the loop equals stroke work.",
    },
    {
        "id": "phy036", "topic": "Physiology",
        "question": "What is the primary determinant of myocardial oxygen consumption (MVO2)?",
        "options": {
            "A": "Preload (end-diastolic volume)",
            "B": "Heart rate",
            "C": "Coronary perfusion pressure",
            "D": "Arterial oxygen content",
            "E": "Pulmonary artery pressure",
        },
        "answer": "B",
        "explanation": "MVO2 is primarily determined by: heart rate (most important \u2014 doubles MVO2 when HR doubles), wall tension (afterload x preload), and contractility. Tachycardia is doubly harmful in ischaemia: increases MVO2 and reduces diastolic coronary filling time. Hence beta-blockers are valuable in IHD.",
    },
    {
        "id": "phy037", "topic": "Physiology",
        "question": "The blood-brain barrier (BBB) is formed primarily by:",
        "options": {
            "A": "Myelin sheaths surrounding cerebral vessels",
            "B": "Tight junctions between cerebral capillary endothelial cells, supported by astrocyte end-feet",
            "C": "Ependymal cells lining the choroid plexus",
            "D": "Pericytes surrounding cerebral arterioles",
            "E": "The meningeal layers surrounding the brain",
        },
        "answer": "B",
        "explanation": "BBB consists of tight junctions (claudins, occludins) between cerebral endothelial cells (the primary barrier), basement membrane, and astrocyte end-feet (induce and maintain barrier properties). Restricts polar/ionised molecules, large proteins, and many drugs. Lipid-soluble, un-ionised, low-molecular-weight drugs cross freely. The BBB is disrupted by inflammation, trauma, and ischaemia.",
    },
    {
        "id": "phy038", "topic": "Physiology",
        "question": "Cerebral autoregulation maintains CBF constant between which values of mean arterial pressure?",
        "options": {
            "A": "40-100 mmHg",
            "B": "50-150 mmHg",
            "C": "70-180 mmHg",
            "D": "80-200 mmHg",
            "E": "60-120 mmHg",
        },
        "answer": "B",
        "explanation": "Cerebral autoregulation maintains CBF approximately 50 mL/100g/min constant over a MAP range of approximately 50-150 mmHg via myogenic response and metabolic coupling. In chronic hypertension, the curve shifts rightward. CO2 is a potent cerebral vasodilator \u2014 each 1 kPa rise in PaCO2 increases CBF approximately 25-30%.",
    },
    {
        "id": "phy039", "topic": "Physiology",
        "question": "At the dorsal horn, which neurotransmitters are released from C-fibre primary afferents during sustained nociceptive input contributing to central sensitisation?",
        "options": {
            "A": "GABA",
            "B": "Substance P and glutamate",
            "C": "Serotonin",
            "D": "Noradrenaline",
            "E": "Acetylcholine",
        },
        "answer": "B",
        "explanation": "C-fibre primary afferents release substance P (neurokinin A) and glutamate at the dorsal horn. Glutamate activates AMPA receptors (fast transmission); substance P acts on NK1 receptors. With sustained input, NMDA receptors become activated causing wind-up and central sensitisation \u2014 the basis of chronic pain and hyperalgesia. NMDA antagonists (ketamine, magnesium) have anti-hyperalgesic properties.",
    },
    {
        "id": "phy040", "topic": "Physiology",
        "question": "Which of the following is a feature of the Bainbridge reflex?",
        "options": {
            "A": "Decreased heart rate in response to rising venous pressure",
            "B": "Increased heart rate caused by atrial stretch receptors responding to increased venous return",
            "C": "Bradycardia caused by stimulation of ventricular mechanoreceptors",
            "D": "Peripheral vasoconstriction in response to hypotension",
            "E": "Increased heart rate in response to pain via sympathetic activation",
        },
        "answer": "B",
        "explanation": "The Bainbridge reflex: stretch receptors in the right atrium respond to increased venous pressure/volume by causing reflex tachycardia. It counteracts the baroreceptor reflex during volume loading and helps increase CO to match venous return. Explains why HR can rise with IV fluid boluses despite rising BP.",
    },
    {
        "id": "phy041", "topic": "Physiology",
        "question": "What is the normal value for pulmonary artery wedge pressure (PAWP) and what does it estimate?",
        "options": {
            "A": "15-25 mmHg; right atrial pressure",
            "B": "2-12 mmHg; left atrial pressure and left ventricular end-diastolic pressure",
            "C": "2-12 mmHg; right ventricular end-diastolic pressure",
            "D": "25-35 mmHg; left ventricular systolic pressure",
            "E": "0-5 mmHg; pulmonary arterial pressure",
        },
        "answer": "B",
        "explanation": "Normal PAWP (pulmonary artery wedge/occlusion pressure) is 2-12 mmHg. When the PAC balloon is inflated and wedged, it measures static pressure transmitted back through the pulmonary veins from the left atrium \u2014 an estimate of LAP and LVEDP (preload). PAWP > 18 mmHg suggests left heart failure/pulmonary oedema. Limitations: mitral stenosis, raised PEEP, and non-zone-3 catheter position affect accuracy.",
    },
    {
        "id": "phy042", "topic": "Physiology",
        "question": "Regarding the glomerular filtration rate (GFR), which statement is correct?",
        "options": {
            "A": "Normal GFR is approximately 300 mL/min",
            "B": "GFR is directly proportional to afferent arteriolar resistance",
            "C": "GFR is maintained by autoregulation between MAP 70-180 mmHg",
            "D": "Creatinine clearance underestimates true GFR",
            "E": "Inulin clearance overestimates GFR as it is partially secreted",
        },
        "answer": "C",
        "explanation": "Renal autoregulation maintains GFR and RBF relatively constant over a MAP range of approximately 70-180 mmHg via myogenic response and tubuloglomerular feedback. Normal GFR approximately 125 mL/min. Creatinine is freely filtered and slightly secreted, so creatinine clearance slightly OVERESTIMATES GFR. Inulin is the gold standard as it is freely filtered and neither secreted nor reabsorbed.",
    },
    {
        "id": "phy043", "topic": "Physiology",
        "question": "Which of the following physiological changes occurs in normal pregnancy at term?",
        "options": {
            "A": "Functional residual capacity increases by 20%",
            "B": "Cardiac output increases by 40-50%",
            "C": "Systemic vascular resistance increases",
            "D": "Haematocrit increases above normal",
            "E": "Minimum alveolar concentration (MAC) increases",
        },
        "answer": "B",
        "explanation": "Cardiac output increases 40-50% by term (increased HR ~20% and SV ~30%). FRC decreases by approximately 20% (diaphragm elevation). SVR decreases due to progesterone-mediated vasodilation and low-resistance placental circulation. A dilutional anaemia occurs (plasma volume increases more than red cell mass). MAC decreases in pregnancy (progesterone-mediated CNS sensitisation).",
    },
    {
        "id": "phy044", "topic": "Physiology",
        "question": "The normal cerebrospinal fluid (CSF) glucose concentration is what fraction of the plasma glucose?",
        "options": {
            "A": "Equal to plasma glucose",
            "B": "50-60% of plasma glucose",
            "C": "80-90% of plasma glucose",
            "D": "30-40% of plasma glucose",
            "E": "10% of plasma glucose",
        },
        "answer": "B",
        "explanation": "Normal CSF glucose is approximately 60-80% of simultaneous plasma glucose (approximately 2.2-3.9 mmol/L when plasma glucose is normal). CSF glucose below 50% of plasma glucose suggests bacterial or fungal meningitis (bacteria and white cells consume glucose). Normal CSF protein is 0.15-0.45 g/L; raised in meningitis, Guillain-Barre, subarachnoid haemorrhage. Opening pressure: 5-18 cmH2O (lateral recumbent).",
    },
    {
        "id": "phy045", "topic": "Physiology",
        "question": "Regarding the renin-angiotensin-aldosterone system (RAAS), which statement is correct?",
        "options": {
            "A": "Renin is released from the macula densa in response to high NaCl concentration",
            "B": "Angiotensin II causes vasodilation and increases GFR",
            "C": "Aldosterone acts on the collecting duct to increase sodium reabsorption and potassium excretion",
            "D": "ACE inhibitors prevent aldosterone synthesis by blocking aldosterone synthase",
            "E": "Angiotensin II is produced in the liver",
        },
        "answer": "C",
        "explanation": "RAAS: juxtaglomerular cells release renin (in response to low NaCl at macula densa, reduced renal perfusion pressure, sympathetic activation) \u2192 angiotensinogen (liver) \u2192 angiotensin I \u2192 ACE (lung endothelium) \u2192 angiotensin II \u2192 vasoconstriction (AT1 receptor), aldosterone release from adrenal cortex, ADH release, thirst. Aldosterone acts on principal cells of collecting duct: ENaC Na+ reabsorption in exchange for K+ and H+ excretion. ACE inhibitors block ACE (not aldosterone synthase).",
    },
    {
        "id": "phar026", "topic": "Pharmacology",
        "question": "What is the oil:gas partition coefficient and why is it clinically relevant?",
        "options": {
            "A": "It determines the rate of induction \u2014 higher coefficient means faster onset",
            "B": "It correlates with anaesthetic potency \u2014 higher coefficient correlates with lower MAC",
            "C": "It determines solubility in blood \u2014 higher coefficient means greater blood solubility",
            "D": "It predicts the risk of hepatotoxicity from the agent",
            "E": "It determines the minimum inspired concentration needed to maintain anaesthesia",
        },
        "answer": "B",
        "explanation": "Oil:gas partition coefficient correlates with lipid solubility and anaesthetic potency (Meyer-Overton correlation: MAC x oil:gas coefficient is approximately constant). Higher oil:gas = more potent (lower MAC). Desflurane: oil:gas 19, MAC 6%; sevoflurane: 47, MAC 2.05%; isoflurane: 91, MAC 1.15%; halothane: 224, MAC 0.75%. Blood:gas coefficient determines rate of equilibration. These are distinct properties.",
    },
    {
        "id": "phar027", "topic": "Pharmacology",
        "question": "Which volatile anaesthetic is most associated with cardiac sensitisation to catecholamines and hepatotoxicity?",
        "options": {
            "A": "Isoflurane",
            "B": "Sevoflurane",
            "C": "Desflurane",
            "D": "Halothane",
            "E": "Nitrous oxide",
        },
        "answer": "D",
        "explanation": "Halothane: (1) Cardiac sensitisation to catecholamines causing arrhythmias. (2) Halothane hepatitis: Type 1 (mild, self-limiting, ~20% patients). Type 2 (fulminant hepatic necrosis ~1:35,000) \u2014 immune-mediated via trifluoroacetyl hapten from CYP2E1 oxidative metabolism. Contraindicated after prior halothane hepatitis. Modern agents (sevoflurane, isoflurane, desflurane) are much safer.",
    },
    {
        "id": "phar028", "topic": "Pharmacology",
        "question": "Desflurane is notable for which property compared to other modern volatile agents?",
        "options": {
            "A": "Highest blood:gas partition coefficient of modern agents",
            "B": "Lowest MAC value of modern agents",
            "C": "Pungency limiting its use for inhalational induction",
            "D": "Absence of greenhouse gas effect",
            "E": "Metabolism to compound A in soda lime",
        },
        "answer": "C",
        "explanation": "Desflurane properties: lowest blood:gas coefficient (0.42 \u2014 fastest offset), highest MAC (6.0%), pungent/irritant to airways causing breath-holding, coughing, laryngospasm \u2014 NOT suitable for inhalational induction. Requires a heated vaporiser (boiling point 23.5 degrees C). Significant global warming potential (GWP ~2540 x CO2). Compound A is produced from sevoflurane, not desflurane.",
    },
    {
        "id": "phar029", "topic": "Pharmacology",
        "question": "The second gas effect with nitrous oxide refers to:",
        "options": {
            "A": "N2O reducing the MAC of co-administered volatile agents",
            "B": "Rapid uptake of N2O concentrating the remaining volatile agent in the alveolus, accelerating its uptake",
            "C": "N2O diffusing into closed gas spaces and expanding them",
            "D": "N2O inhibiting vitamin B12 causing megaloblastic anaemia",
            "E": "The increase in FRC caused by N2O administration",
        },
        "answer": "B",
        "explanation": "Second gas effect: rapid uptake of high-concentration N2O from alveoli concentrates the remaining gases (O2 and co-administered volatile) in alveolar gas, increasing their alveolar partial pressures and accelerating uptake. Also, as N2O is absorbed, extra gas is pulled in from the airways. This contributes to faster induction when N2O is used. Diffusion hypoxia (Fink effect) occurs on N2O discontinuation \u2014 supplement O2 for at least 5 minutes.",
    },
    {
        "id": "phar030", "topic": "Pharmacology",
        "question": "Etomidate is preferred over propofol for induction in haemodynamically unstable patients because:",
        "options": {
            "A": "It provides superior analgesia",
            "B": "It has minimal cardiovascular depression, maintaining SVR, HR and cardiac output",
            "C": "It causes vasoconstriction via alpha-1 agonism",
            "D": "It reduces myocardial oxygen demand via beta-blockade",
            "E": "It has a faster onset and shorter duration than propofol",
        },
        "answer": "B",
        "explanation": "Etomidate (imidazole, GABA-A potentiator) is notable for cardiovascular stability \u2014 minimal effect on SVR, HR, and CO compared to propofol or thiopental. However, a single induction dose suppresses adrenocortical function for 6-12 hours (inhibits 11-beta-hydroxylase). This is controversial in critically ill patients where it is often used for RSI.",
    },
    {
        "id": "phar031", "topic": "Pharmacology",
        "question": "What is the clinical relevance of ketamine's dissociative state?",
        "options": {
            "A": "Patients are unconscious and unresponsive during ketamine anaesthesia",
            "B": "Patients may appear awake (eyes open, nystagmus) but are analgesic and amnesic due to functional dissociation of thalamocortical and limbic systems",
            "C": "Dissociation refers to ketamine's ability to separate analgesia from anaesthesia at sub-anaesthetic doses",
            "D": "The dissociative state makes ketamine safe in raised ICP",
            "E": "Emergence phenomena are prevented by co-administration of opioids",
        },
        "answer": "B",
        "explanation": "Ketamine produces a dissociative state \u2014 functional separation of thalamocortical and limbic systems. Patients appear awake (nystagmus, eyes open) but are analgesic and amnesic. Sympathomimetic (increased HR, BP, bronchodilation) \u2014 useful in asthma and shock. Laryngeal reflexes relatively preserved. Emergence delirium reduced by benzodiazepine pre-medication. Increases ICP (raised CBF, CMRO2) \u2014 classically avoided in neuroanaesthesia, though this is increasingly re-examined.",
    },
    {
        "id": "phar032", "topic": "Pharmacology",
        "question": "Which opioid receptor subtype primarily mediates spinal analgesia, respiratory depression, and euphoria?",
        "options": {
            "A": "Kappa (K) receptor",
            "B": "Delta (D) receptor",
            "C": "Mu (M) receptor",
            "D": "Nociceptin/ORL1 receptor",
            "E": "Sigma receptor",
        },
        "answer": "C",
        "explanation": "Mu opioid receptors (MOR) mediate: supraspinal analgesia (PAG, thalamus), spinal analgesia (dorsal horn), respiratory depression (pre-Botzinger complex), euphoria, miosis, bradycardia, reduced GI motility, nausea/vomiting (area postrema). All are Gi-coupled (decreased cAMP, increased K+ conductance, decreased Ca2+ conductance) reducing neuronal excitability.",
    },
    {
        "id": "phar033", "topic": "Pharmacology",
        "question": "What is opioid-induced hyperalgesia (OIH) and why is it clinically important?",
        "options": {
            "A": "OIH is synonymous with opioid tolerance and describes reduced analgesic efficacy over time",
            "B": "OIH describes paradoxically increased sensitivity to pain caused by opioid use, potentially worsening pain despite escalating doses",
            "C": "OIH occurs exclusively with intrathecal opioids",
            "D": "OIH is prevented by combining opioids with NSAIDs",
            "E": "OIH is mediated exclusively by peripheral opioid receptor downregulation",
        },
        "answer": "B",
        "explanation": "OIH is paradoxical sensitisation to pain caused by opioid use itself, distinct from tolerance. Mechanisms: central sensitisation via NMDA receptor activation, glial activation, dynorphin release. High-dose remifentanil infusions are particularly associated with post-operative hyperalgesia. NMDA antagonists (ketamine, magnesium) may prevent/treat OIH. Important rationale for opioid-sparing perioperative strategies.",
    },
    {
        "id": "phar034", "topic": "Pharmacology",
        "question": "Tramadol has which combination of analgesic mechanisms?",
        "options": {
            "A": "Mu-opioid agonism and NMDA antagonism",
            "B": "Weak mu-opioid agonism plus inhibition of noradrenaline and serotonin reuptake",
            "C": "Kappa-opioid agonism and COX inhibition",
            "D": "Mu-opioid agonism and sodium channel blockade",
            "E": "Selective serotonin reuptake inhibition with no opioid activity",
        },
        "answer": "B",
        "explanation": "Tramadol: dual mechanism \u2014 weak mu-opioid agonism (and its O-desmethyl metabolite via CYP2D6 is more potent) plus inhibition of noradrenaline and serotonin reuptake in dorsal horn (descending inhibition). CYP2D6 polymorphism: poor metabolisers get reduced analgesia; ultra-rapid metabolisers get toxic levels. Serotonin syndrome risk with SSRIs/MAOIs. Lowers seizure threshold.",
    },
    {
        "id": "phar035", "topic": "Pharmacology",
        "question": "Which non-depolarising NMB is primarily eliminated by Hofmann degradation and is safest in organ failure?",
        "options": {
            "A": "Rocuronium",
            "B": "Vecuronium",
            "C": "Atracurium/cisatracurium",
            "D": "Pancuronium",
            "E": "Mivacurium",
        },
        "answer": "C",
        "explanation": "Atracurium and cisatracurium undergo Hofmann elimination (spontaneous non-enzymatic degradation at physiological pH and temperature) and ester hydrolysis, independent of renal or hepatic function \u2014 safest in multi-organ failure. Laudanosine (active metabolite) is a CNS stimulant \u2014 accumulates in ICU causing seizures historically. Cisatracurium produces less laudanosine. Rocuronium/vecuronium undergo hepatic metabolism; pancuronium is renally excreted.",
    },
    {
        "id": "phar036", "topic": "Pharmacology",
        "question": "What dose of sugammadex is required for immediate reversal of rocuronium 1.2 mg/kg given 3 minutes previously?",
        "options": {
            "A": "2 mg/kg",
            "B": "4 mg/kg",
            "C": "8 mg/kg",
            "D": "16 mg/kg",
            "E": "0.5 mg/kg",
        },
        "answer": "D",
        "explanation": "Sugammadex dosing: routine reversal at TOF count 1-2 twitches: 4 mg/kg; reversal at TOF count >=2: 2 mg/kg; immediate reversal (within 3 min of rocuronium 1.2 mg/kg): 16 mg/kg. The 16 mg/kg dose is used in the CICO scenario where rocuronium RSI has been performed \u2014 allows rapid return of spontaneous ventilation.",
    },
    {
        "id": "phar037", "topic": "Pharmacology",
        "question": "Which property of local anaesthetics determines their potency?",
        "options": {
            "A": "pKa \u2014 lower pKa leads to greater potency",
            "B": "Lipid solubility \u2014 more lipid-soluble agents penetrate the nerve membrane more readily and are more potent",
            "C": "Protein binding \u2014 higher protein binding increases receptor affinity and potency",
            "D": "Molecular weight \u2014 smaller molecules penetrate nerve sheaths more effectively",
            "E": "Water solubility \u2014 more water-soluble agents distribute more evenly around nerves",
        },
        "answer": "B",
        "explanation": "LA potency correlates with lipid solubility (membrane penetration and receptor affinity). Bupivacaine (most lipid-soluble, most potent) > ropivacaine > lidocaine > chloroprocaine. pKa determines onset speed (proportion un-ionised at physiological pH). Protein binding determines duration (bupivacaine 95% protein-bound, long duration). The ionised form (cation) is the active form binding sodium channels from the intracellular side.",
    },
    {
        "id": "phar038", "topic": "Pharmacology",
        "question": "Why are local anaesthetics less effective in infected tissue?",
        "options": {
            "A": "Increased vascularity causes faster washout of the agent",
            "B": "Tissue acidosis increases the ionised fraction of LA, reducing membrane penetration",
            "C": "Neutrophil enzymes metabolise local anaesthetics before they reach the nerve",
            "D": "Oedema creates a physical barrier preventing LA diffusion",
            "E": "Bacterial toxins competitively block sodium channels",
        },
        "answer": "B",
        "explanation": "Infection causes local tissue acidosis. LAs are weak bases \u2014 in acidic environments, more of the drug is protonated (ionised cationic form). Only the un-ionised (free base) form crosses the cell membrane. At pH 7.4, lidocaine (pKa 7.9) is approximately 25% un-ionised; at pH 6.5 (infected tissue), less than 5% un-ionised. Solution: use larger volumes, consider techniques proximal to infection, or alkalinisation with sodium bicarbonate.",
    },
    {
        "id": "phar039", "topic": "Pharmacology",
        "question": "Noradrenaline infusion causes hypertension primarily through which mechanism?",
        "options": {
            "A": "Beta-1 agonism increasing cardiac output",
            "B": "Alpha-1 agonism increasing systemic vascular resistance",
            "C": "Beta-2 agonism increasing cardiac contractility",
            "D": "V1 receptor activation in blood vessels",
            "E": "Direct cardiac stimulation via the SA node",
        },
        "answer": "B",
        "explanation": "Noradrenaline: potent alpha-1 agonist (vasoconstriction, increased SVR) with beta-1 activity (maintains cardiac contractility). Minimal beta-2 activity. In vasodilatory shock (sepsis): increased SVR restores MAP despite potentially slightly reduced CO. Contrast with adrenaline (alpha+beta: increases SVR AND CO) and dopamine (dose-dependent dopamine, beta-1, and alpha-1 receptor effects).",
    },
    {
        "id": "phar040", "topic": "Pharmacology",
        "question": "Phosphodiesterase III (PDE3) inhibitors such as milrinone exert their inotropic and vasodilatory effects by:",
        "options": {
            "A": "Stimulating beta-1 adrenoceptors increasing cAMP",
            "B": "Inhibiting breakdown of cAMP, increasing intracellular cAMP and Ca2+-dependent contractility",
            "C": "Blocking alpha-1 receptors causing vasodilation",
            "D": "Activating ATP-sensitive K+ channels causing vasodilation",
            "E": "Directly increasing SR Ca2+ release via ryanodine receptors",
        },
        "answer": "B",
        "explanation": "PDE3 inhibitors (milrinone, enoximone) block phosphodiesterase 3 preventing cAMP breakdown \u2192 increased cAMP \u2192 increased PKA \u2192 increased Ca2+ influx/SR release in myocardium (inotropy) AND vasodilation. Often called inodilators. Useful in low-CO states with high SVR (cardiogenic shock, post-cardiotomy). Risk: tachycardia, arrhythmias, systemic hypotension.",
    },
    {
        "id": "phar041", "topic": "Pharmacology",
        "question": "Which antiarrhythmic drug class does amiodarone belong to, and what are its main side effects?",
        "options": {
            "A": "Class I (Na+ channel blocker); QRS widening and proarrhythmia",
            "B": "Class II (beta-blocker); bradycardia, bronchoconstriction, fatigue",
            "C": "Class III (K+ channel blocker); thyroid dysfunction, pulmonary toxicity, corneal microdeposits, photosensitivity",
            "D": "Class IV (Ca2+ channel blocker); AV block, constipation, negative inotropy",
            "E": "Class Ia; Torsades de Pointes and QT prolongation only",
        },
        "answer": "C",
        "explanation": "Amiodarone is predominantly class III but also has class I, II, and IV properties. Extensive side effects due to high iodine content (~37%) and lipid solubility (t1/2 40-55 days): thyroid dysfunction (hypo or hyper), pulmonary toxicity (fibrosis, pneumonitis), hepatotoxicity, corneal microdeposits, blue-grey skin discolouration, photosensitivity, peripheral neuropathy, bradycardia, hypotension (IV). Despite side effects, the most effective antiarrhythmic available.",
    },
    {
        "id": "phar042", "topic": "Pharmacology",
        "question": "Dexamethasone is used perioperatively for PONV. What is its mechanism?",
        "options": {
            "A": "5-HT3 receptor antagonism in the CTZ",
            "B": "Dopamine D2 antagonism in the chemoreceptor trigger zone",
            "C": "The exact mechanism is unclear but involves prostaglandin synthesis inhibition, serotonin depletion in the gut, and central anti-inflammatory effects",
            "D": "Histamine H1 antagonism in the vomiting centre",
            "E": "NK1 receptor antagonism preventing substance P binding",
        },
        "answer": "C",
        "explanation": "Dexamethasone's antiemetic mechanism is incompletely understood \u2014 proposed mechanisms include glucocorticoid-mediated reduction in prostaglandin and serotonin synthesis, central anti-inflammatory effects, and opioid-sparing analgesia. Dose: 4-8 mg IV at induction. Effective in multimodal PONV prophylaxis. Causes transient hyperglycaemia \u2014 clinically significant in diabetes. Single dose has not been shown to impair wound healing or increase infection risk clinically.",
    },
    {
        "id": "phar043", "topic": "Pharmacology",
        "question": "Regarding plasma protein binding, which statement is correct?",
        "options": {
            "A": "Only albumin binds drugs in clinical practice",
            "B": "Basic drugs (e.g. local anaesthetics, opioids) bind primarily to alpha-1-acid glycoprotein (AAG)",
            "C": "Protein-bound drug is the pharmacologically active fraction",
            "D": "Reduced albumin has no effect on drug dosing requirements",
            "E": "AAG levels fall during stress, surgery and inflammation",
        },
        "answer": "B",
        "explanation": "Two main plasma binding proteins: albumin (acidic drugs \u2014 NSAIDs, warfarin, barbiturates; also some basic drugs) and alpha-1-acid glycoprotein/AAG (basic drugs \u2014 local anaesthetics, opioids, propranolol). Only FREE (unbound) drug is pharmacologically active. AAG rises acutely with surgery/trauma/inflammation \u2014 reducing free fraction of basic drugs. Albumin falls in chronic illness/liver disease \u2014 raising free fraction of acidic drugs (phenytoin, warfarin).",
    },
    {
        "id": "phys026", "topic": "Physics & Clinical Measurement",
        "question": "What is the difference between macroshock and microshock?",
        "options": {
            "A": "Macroshock: >1 mA applied to the heart; microshock: >100 mA applied to skin",
            "B": "Macroshock: >100 mA through the body causing VF; microshock: >150 microA directly to the heart causing VF",
            "C": "Macroshock and microshock both require >1 A to cause VF",
            "D": "Microshock only occurs with high-frequency current",
            "E": "Macroshock causes burns only; microshock causes VF",
        },
        "answer": "B",
        "explanation": "Macroshock: current applied externally \u2014 skin resistance limits current. >100 mA causes VF threshold. Microshock: current applied directly to or near the heart (intracardiac catheter) bypasses skin resistance. VF threshold: only 150 microA. This is why electrically susceptible patients require additional isolation measures. Theatre isolated power supply (IPS) with line isolation monitor (LIM) limits fault current to <5 mA, protecting against macroshock.",
    },
    {
        "id": "phys027", "topic": "Physics & Clinical Measurement",
        "question": "The BIS (Bispectral Index) monitor analyses which signal to quantify depth of anaesthesia?",
        "options": {
            "A": "Cerebral blood flow velocity via transcranial Doppler",
            "B": "Processed EEG signal from frontal electrodes \u2014 analysing frequency, amplitude, and inter-hemisphere synchrony",
            "C": "Electromyography from facial muscles as a surrogate for arousal",
            "D": "Infrared absorption of haemoglobin as a measure of cortical perfusion",
            "E": "Evoked potentials from auditory stimuli",
        },
        "answer": "B",
        "explanation": "BIS analyses the processed EEG (frontal electrodes) using a proprietary algorithm combining time-domain analysis (burst suppression ratio), frequency-domain analysis (beta ratio), and bispectral analysis (phase coupling between frequencies). Output: 0-100 scale. Awake: 95-100; sedation: 60-80; anaesthesia: 40-60; burst suppression: 20-40. BIS reduces but does not eliminate awareness risk. Ketamine/nitrous oxide (dissociatives) may give misleadingly high readings.",
    },
    {
        "id": "phys028", "topic": "Physics & Clinical Measurement",
        "question": "What does a critically damped arterial line waveform indicate?",
        "options": {
            "A": "The transducer is positioned too high",
            "B": "Excessive damping causing underestimation of systolic and overestimation of diastolic pressure",
            "C": "The waveform is accurate and optimal for clinical use",
            "D": "Air bubbles causing over-amplification of systolic pressure",
            "E": "The natural frequency of the system is too high",
        },
        "answer": "B",
        "explanation": "Critical damping (coefficient ~1.0) causes the system to return to baseline slowly without oscillation, losing fine detail of the arterial waveform. This underestimates systolic and overestimates diastolic pressure (mean BP relatively preserved). Causes: kinked tubing, soft tubing, blood clot, or compliant connections. Optimal damping coefficient is 0.64 (slightly underdamped). Air bubbles cause underdamping with systolic overshoot.",
    },
    {
        "id": "phys029", "topic": "Physics & Clinical Measurement",
        "question": "Boyle's Law states pressure and volume are inversely related at constant temperature. What is its clinical application to nitrous oxide cylinders?",
        "options": {
            "A": "Pressure directly reflects remaining N2O content until the cylinder is empty",
            "B": "N2O is stored as a liquid/gas mixture; pressure remains constant (~44 bar) until all liquid has vaporised \u2014 pressure alone cannot gauge remaining content",
            "C": "N2O pressure increases as the cylinder cools, warning of depletion",
            "D": "Boyle's Law applies equally to O2 and N2O cylinders for content estimation",
            "E": "The critical temperature of N2O is above room temperature, so it exists only as gas in the cylinder",
        },
        "answer": "B",
        "explanation": "N2O critical temperature is 36.5 degrees C (just above room temperature); at room temperature N2O exists as liquid/vapour in equilibrium. Cylinder pressure (44 bar) reflects saturated vapour pressure \u2014 remains constant regardless of liquid level until all liquid has evaporated. N2O cylinder pressure does NOT indicate content until near-empty. Must weigh the cylinder. Contrast O2 (critical temp -118 degrees C) \u2014 always gaseous at room temperature, pressure directly proportional to remaining volume.",
    },
    {
        "id": "phys030", "topic": "Physics & Clinical Measurement",
        "question": "Critical temperature of a gas is defined as:",
        "options": {
            "A": "The temperature at which a liquid begins to boil at atmospheric pressure",
            "B": "The temperature above which a gas CANNOT be liquefied regardless of pressure",
            "C": "The temperature at which a gas poses an explosion risk",
            "D": "The minimum temperature for safe anaesthetic use",
            "E": "The temperature at which gas density equals liquid density",
        },
        "answer": "B",
        "explanation": "Critical temperature (Tc): above Tc, kinetic energy exceeds intermolecular forces \u2014 the gas cannot be liquefied regardless of applied pressure. O2 Tc = -118 degrees C (always gas at room temperature \u2014 stored as compressed gas). N2O Tc = 36.5 degrees C (stored as liquid at room temperature at 44 bar). Entonox (50:50 O2/N2O) Tc = -6 degrees C (Poynting effect) \u2014 separates below -6 degrees C requiring shaking before use.",
    },
    {
        "id": "phys031", "topic": "Physics & Clinical Measurement",
        "question": "What does a sudden rise in peak airway pressure with UNCHANGED plateau pressure indicate in a mechanically ventilated patient?",
        "options": {
            "A": "Reduced lung compliance (e.g. pneumothorax, pulmonary oedema)",
            "B": "Increased airway resistance (e.g. bronchospasm, secretions, kinked ETT)",
            "C": "Decreased PEEP causing alveolar derecruitment",
            "D": "Increased respiratory rate causing air trapping",
            "E": "Disconnection of the ventilator circuit",
        },
        "answer": "B",
        "explanation": "Peak pressure = resistance + elastic recoil. Plateau pressure (inspiratory hold with no flow) = purely elastic recoil (compliance). Peak minus Plateau = resistance component. Rise in peak with unchanged plateau: increased RESISTANCE (bronchospasm, secretions, kinked or bitten ETT, water in circuit). Rise in BOTH: decreased COMPLIANCE (pneumothorax, haemothorax, pulmonary oedema, ARDS, abdominal compartment syndrome). This distinction guides management.",
    },
    {
        "id": "phys032", "topic": "Physics & Clinical Measurement",
        "question": "What is intrinsic PEEP (auto-PEEP) and how can it be detected?",
        "options": {
            "A": "PEEP set by the clinician on the ventilator; detected by alveolar pressure measurement",
            "B": "Positive end-expiratory pressure generated by incomplete exhalation (gas trapping); detected by end-expiratory hold manoeuvre showing positive residual pressure",
            "C": "Pressure generated by chest wall recoil at FRC",
            "D": "PEEP delivered via a non-invasive interface; detected by desaturation",
            "E": "A pneumatic artefact from the ventilator circuit; eliminated by circuit change",
        },
        "answer": "B",
        "explanation": "Intrinsic/auto-PEEP: incomplete exhalation due to insufficient expiratory time (high RR, prolonged I:E ratio, high VT) or increased expiratory resistance (COPD, bronchospasm) \u2192 gas trapping \u2192 positive pressure remains at end-expiration. Detection: end-expiratory hold manoeuvre \u2014 airway pressure equilibrates with alveolar pressure, revealing iPEEP. Consequences: barotrauma, haemodynamic compromise (reduces venous return), patient-ventilator dyssynchrony.",
    },
    {
        "id": "phys033", "topic": "Physics & Clinical Measurement",
        "question": "In a study comparing two anaesthetic agents, the 95% confidence interval for the difference in pain scores is -0.5 to +2.5. What can be concluded?",
        "options": {
            "A": "The result is statistically significant \u2014 the upper bound is positive",
            "B": "The result is not statistically significant \u2014 the CI crosses zero, meaning no statistically significant difference is demonstrated",
            "C": "The result confirms clinical equivalence of the two agents",
            "D": "The study needs a larger sample size only if the point estimate is zero",
            "E": "The p-value must be <0.05 since the CI has a positive upper bound",
        },
        "answer": "B",
        "explanation": "A 95% CI for a difference that includes zero means the null hypothesis (no difference) cannot be rejected at the 5% significance level \u2014 the result is NOT statistically significant (equivalent to p >0.05). The CI gives the range of plausible true differences with 95% probability. Crossing zero = not significant. Note: statistical significance does not equal clinical significance \u2014 a significant result may be clinically trivial.",
    },
    {
        "id": "phys034", "topic": "Physics & Clinical Measurement",
        "question": "What is the number needed to treat (NNT) and how is it calculated?",
        "options": {
            "A": "The number of patients who must receive treatment for one to be harmed",
            "B": "1 divided by absolute risk reduction (ARR); the number of patients who must be treated for one additional patient to benefit",
            "C": "The relative risk reduction expressed as a percentage",
            "D": "The reciprocal of the odds ratio",
            "E": "The number of patients in the control group divided by the event rate",
        },
        "answer": "B",
        "explanation": "NNT = 1/ARR. ARR = control event rate minus treatment event rate. Example: control 20% mortality, treatment 15% gives ARR 5% (0.05) so NNT = 1/0.05 = 20 (treat 20 patients to prevent 1 death). NNT is more clinically meaningful than relative risk reduction \u2014 RRR would be 25% regardless of baseline risk. NNH (number needed to harm) = 1/absolute risk increase.",
    },
    {
        "id": "phys035", "topic": "Physics & Clinical Measurement",
        "question": "What is the Wheatstone bridge circuit used for in medicine?",
        "options": {
            "A": "Pulse oximeter",
            "B": "Capnograph",
            "C": "Strain gauge pressure transducer (e.g. invasive arterial line)",
            "D": "Paramagnetic oxygen analyser",
            "E": "Infrared CO2 analyser",
        },
        "answer": "C",
        "explanation": "The Wheatstone bridge is used in strain gauge pressure transducers (arterial lines, CVP monitors). When pressure deforms a diaphragm, resistors in the strain gauge change \u2014 the bridge becomes unbalanced, producing a voltage proportional to pressure. Zero-referencing (levelling to the phlebostatic axis) and calibration balance the bridge at zero. Also used in platinum resistance thermometers.",
    },
    {
        "id": "phys036", "topic": "Physics & Clinical Measurement",
        "question": "In the context of medical gas cylinders, what does the 'CF' classification indicate?",
        "options": {
            "A": "Class F protection against defibrillation",
            "B": "Cardiac Floating \u2014 highest level of protection, suitable for direct cardiac connection with leakage current <10 microA",
            "C": "Continuous Function \u2014 equipment can be used without interruption",
            "D": "Condensate Filter \u2014 protects against liquid ingress",
            "E": "Class II double insulated equipment suitable for cardiac monitoring",
        },
        "answer": "B",
        "explanation": "Medical device electrical safety classifications (IEC 60601): B (Body) leakage <100 microA, general patient contact; BF (Body Floating) leakage <100 microA, isolated applied part; CF (Cardiac Floating) leakage <10 microA, isolated applied part specifically for cardiac connection (intracardiac catheters). CF provides greatest protection against microshock. Also: Type I (earth connected), Type II (double insulated).",
    },
    {
        "id": "phys037", "topic": "Physics & Clinical Measurement",
        "question": "The Tec-7 vaporiser is temperature-compensated. What does this mean?",
        "options": {
            "A": "The vaporiser heats the agent to a fixed temperature for consistent output",
            "B": "The splitting ratio is automatically adjusted by a bimetallic strip to compensate for falling vapour pressure as the agent cools during use",
            "C": "The vaporiser uses a thermoelectric cooler to prevent temperature changes",
            "D": "Temperature compensation refers to use of a water bath to maintain agent temperature",
            "E": "The bimetallic strip increases fresh gas flow to the vaporising chamber when ambient temperature rises",
        },
        "answer": "B",
        "explanation": "As volatile agent vaporises, it absorbs latent heat of vaporisation causing liquid to cool and SVP to fall, delivering less agent. A bimetallic strip automatically adjusts the splitting ratio \u2014 directing more FGF through the vaporising chamber when temperature falls \u2014 maintaining constant delivered concentration. Desflurane is heated to 39 degrees C above its boiling point of 23.5 degrees C in a pressurised vaporiser (Tec-6) \u2014 a fundamentally different mechanism.",
    },
    {
        "id": "phys038", "topic": "Physics & Clinical Measurement",
        "question": "What does the FEV1/FVC (Tiffeneau) ratio indicate, and what is a normal value?",
        "options": {
            "A": "Total lung capacity as a fraction of vital capacity",
            "B": "The proportion of forced vital capacity exhaled in the first second; normal >70%",
            "C": "Residual volume as a proportion of TLC",
            "D": "Peak flow as a proportion of FVC",
            "E": "The ratio of functional residual capacity to TLC",
        },
        "answer": "B",
        "explanation": "FEV1/FVC (Tiffeneau index) is the proportion of forced vital capacity exhaled in the first second. Normal is >70-75%. In obstructive disease (asthma, COPD): FEV1 reduced disproportionately, ratio <0.7. In restrictive disease: both FEV1 and FVC reduced proportionally, ratio normal or elevated (>0.7-0.8). This distinction is fundamental to preoperative respiratory assessment.",
    },
    {
        "id": "phys039", "topic": "Physics & Clinical Measurement",
        "question": "What statistical test is most appropriate for comparing means of two normally distributed continuous variables from independent groups?",
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
        "id": "phys040", "topic": "Physics & Clinical Measurement",
        "question": "The oxygen flush valve on an anaesthetic machine delivers:",
        "options": {
            "A": "100% O2 at 200-700 mL/min",
            "B": "100% O2 at 35-75 L/min bypassing the vaporiser",
            "C": "A mixture of O2 and air at 15 L/min",
            "D": "100% O2 at flowmeter-set rate only",
            "E": "100% O2 through the vaporiser at full concentration",
        },
        "answer": "B",
        "explanation": "The oxygen flush valve delivers 100% O2 at 35-75 L/min directly to the common gas outlet, bypassing the vaporisers and flowmeters. Hazards include: barotrauma (high flow during inspiration), dilution of volatile agent (awareness risk if used during maintenance), and delivery of undiluted O2. Should be used with care with spontaneously breathing patients \u2014 high flow can distend the chest.",
    },
    {
        "id": "clin026", "topic": "Clinical Anaesthesia",
        "question": "A patient undergoing thyroid surgery develops stridor and significant inspiratory distress in the recovery room 20 minutes after extubation. The MOST likely cause is:",
        "options": {
            "A": "Laryngeal oedema from prolonged intubation",
            "B": "Bilateral recurrent laryngeal nerve palsy causing bilateral vocal cord adduction",
            "C": "Tracheomalacia from long-standing goitre",
            "D": "Reactionary haemorrhage and haematoma causing tracheal compression \u2014 immediate bedside decompression required",
            "E": "Laryngospasm from airway secretions",
        },
        "answer": "D",
        "explanation": "Post-thyroidectomy haematoma: reactionary bleeding expanding in a closed fascial space compresses the trachea. Time course: typically within hours of surgery. Management: IMMEDIATE bedside opening of wound \u2014 release clips/sutures/drain incision to decompress haematoma (even before returning to theatre). This is a scalpel-in-recovery situation. Unilateral RLN palsy causes hoarseness. Bilateral RLN palsy causes immediate bilateral cord adduction and severe stridor requiring emergency airway. Tracheomalacia: trachea collapses on extubation from loss of cartilage support.",
    },
    {
        "id": "clin027", "topic": "Clinical Anaesthesia",
        "question": "Which grade on the Cormack-Lehane classification indicates that only the epiglottis is visible?",
        "options": {
            "A": "Grade 1",
            "B": "Grade 2a",
            "C": "Grade 2b",
            "D": "Grade 3",
            "E": "Grade 4",
        },
        "answer": "D",
        "explanation": "Cormack-Lehane at direct laryngoscopy: Grade 1 = full vocal cord view; Grade 2a = partial cords visible; Grade 2b = only posterior commissure/arytenoids visible; Grade 3 = only epiglottis visible (no part of the larynx seen); Grade 4 = neither epiglottis nor cords visible. Grade 3 intubation success: >90% with videolaryngoscopy, approximately 60-75% with direct laryngoscopy and bougie. Grade 4 requires videolaryngoscopy or fibreoptic technique.",
    },
    {
        "id": "clin028", "topic": "Clinical Anaesthesia",
        "question": "What is the recommended technique for confirming correct tracheal intubation?",
        "options": {
            "A": "Chest auscultation alone in all cases",
            "B": "Visualisation of ETT passing through cords, waveform capnography (gold standard), and chest auscultation combined",
            "C": "Chest rise, auscultation, and SpO2 normalisation",
            "D": "Oesophageal detector device alone",
            "E": "Post-intubation chest X-ray in all cases",
        },
        "answer": "B",
        "explanation": "Confirmation of tracheal intubation: (1) Direct visualisation of ETT through cords (primary), (2) Waveform capnography (continuous ETCO2 waveform \u2014 gold standard, identifies oesophageal intubation: no waveform or rapid fall to zero), (3) Bilateral chest auscultation and chest rise. False-negative capnography in cardiac arrest (no CO2 produced). RSI confirmation must occur before releasing cricoid pressure.",
    },
    {
        "id": "clin029", "topic": "Clinical Anaesthesia",
        "question": "What is the MOST appropriate initial management of suspected malignant hyperthermia intraoperatively?",
        "options": {
            "A": "Increase fresh gas flow and give IV paracetamol",
            "B": "Stop all triggering agents, call for help, give dantrolene 2.5 mg/kg IV, active cooling",
            "C": "Give dantrolene 1 mg/kg and await response before further action",
            "D": "Give sodium bicarbonate and surface cooling only",
            "E": "Change to a propofol TIVA and continue the case",
        },
        "answer": "B",
        "explanation": "MH is triggered by volatile anaesthetics and suxamethonium. Management: stop trigger agents immediately, call for help, hyperventilate with 100% O2 at maximum fresh gas flow, give dantrolene 2.5 mg/kg IV (repeat every 5 min to max 10 mg/kg), active cooling, treat hyperkalaemia and acidosis, continue monitoring in ICU. Dantrolene inhibits SR Ca2+ release via RyR1 receptor. Do not continue volatile anaesthetics.",
    },
    {
        "id": "clin030", "topic": "Clinical Anaesthesia",
        "question": "What volume of blood does a fully soaked standard surgical swab hold?",
        "options": {
            "A": "5 mL",
            "B": "10 mL",
            "C": "15 mL",
            "D": "25 mL",
            "E": "50 mL",
        },
        "answer": "B",
        "explanation": "A standard 4x4 cm gauze swab holds approximately 10 mL of blood when fully soaked. Larger surgical swabs (10x10 cm) hold approximately 100-150 mL. Accurate intraoperative blood loss estimation requires counting swabs, weighing (1g approximately 1 mL blood), and measuring suction losses. Surgical swab counting is also a WHO safety checklist item.",
    },
    {
        "id": "clin031", "topic": "Clinical Anaesthesia",
        "question": "Which of the following is the MOST common cause of perioperative anaphylaxis in the UK?",
        "options": {
            "A": "Latex",
            "B": "Antibiotics (penicillin)",
            "C": "Neuromuscular blocking agents",
            "D": "Colloids (gelatin)",
            "E": "Chlorhexidine",
        },
        "answer": "C",
        "explanation": "Neuromuscular blocking agents (NMBAs) account for approximately 50-60% of perioperative anaphylaxis cases in the UK (AAGBI/NAP6 data). Antibiotics are second (20-30%), followed by latex, chlorhexidine, and colloids. Cross-reactivity between NMBAs occurs due to the quaternary ammonium group. Skin testing and allergy investigation should be performed after any suspected reaction.",
    },
    {
        "id": "clin032", "topic": "Clinical Anaesthesia",
        "question": "What is the first-line drug and dose for anaphylaxis under anaesthesia?",
        "options": {
            "A": "Hydrocortisone 200 mg IV",
            "B": "Chlorphenamine 10 mg IV",
            "C": "Adrenaline 50-100 mcg IV titrated, or 500 mcg IM if no IV access",
            "D": "Adrenaline 1 mg IV bolus",
            "E": "Salbutamol 2.5 mg nebulised",
        },
        "answer": "C",
        "explanation": "Adrenaline is first-line for anaphylaxis. IV: 50 mcg (0.5 mL of 1:10,000) boluses repeated every 1-2 min, with infusion if repeated boluses required. IM adrenaline 500 mcg (0.5 mL of 1:1000) into the lateral thigh if no IV access. 1 mg IV bolus is for cardiac arrest ONLY \u2014 in conscious or semi-conscious patients this dose causes severe hypertension and arrhythmias. Chlorphenamine and hydrocortisone are adjuncts with delayed onset.",
    },
    {
        "id": "clin033", "topic": "Clinical Anaesthesia",
        "question": "Regarding spinal anaesthesia, which statement is correct about absolute contraindications?",
        "options": {
            "A": "Prior back surgery at a different level",
            "B": "Patient refusal",
            "C": "Age over 80",
            "D": "Mild aortic stenosis",
            "E": "Diabetes mellitus",
        },
        "answer": "B",
        "explanation": "Patient refusal is an absolute contraindication to any anaesthetic technique. Other absolute contraindications: infection at the injection site, true LA allergy, raised intracranial pressure (risk of coning with CSF loss), severe coagulopathy. Relative contraindications include: anticoagulation, fixed cardiac output states (severe AS), pre-existing neurological disease, hypovolaemia. Age, prior back surgery, and diabetes are not contraindications in themselves.",
    },
    {
        "id": "clin034", "topic": "Clinical Anaesthesia",
        "question": "A standard interscalene brachial plexus block provides excellent analgesia for shoulder surgery. Which structure is consistently blocked causing potential respiratory compromise?",
        "options": {
            "A": "Recurrent laryngeal nerve",
            "B": "Phrenic nerve causing ipsilateral hemidiaphragm paresis (100% incidence)",
            "C": "Cervical sympathetic chain causing ipsilateral ptosis",
            "D": "Suprascapular nerve",
            "E": "Accessory nerve causing trapezius weakness",
        },
        "answer": "B",
        "explanation": "Interscalene block: performed at C5-C7 between anterior and middle scalene muscles. Spread to the phrenic nerve (C3-5) is virtually universal (>=100% incidence), causing ipsilateral hemidiaphragm paresis \u2014 FVC decreases approximately 25%. Well-tolerated in healthy patients but CONTRAINDICATED with: contralateral phrenic nerve palsy, severe COPD/respiratory compromise, contralateral pneumonectomy. Horner's syndrome occurs in 70-90% of cases.",
    },
    {
        "id": "clin035", "topic": "Clinical Anaesthesia",
        "question": "When performing a spinal anaesthetic, at which interspace should the needle be inserted in an adult to avoid spinal cord damage?",
        "options": {
            "A": "L1-L2",
            "B": "L2-L3",
            "C": "L3-L4 or below",
            "D": "T12-L1",
            "E": "C7-T1",
        },
        "answer": "C",
        "explanation": "The spinal cord terminates at L1-L2 (conus medullaris) in adults. To avoid cord damage, spinal anaesthesia should be performed at L3-L4 or L4-L5 in adults (safely below the cord, in the cauda equina). In neonates, the cord extends to L3 \u2014 use L4-L5. Tuffier's line (intercristal line connecting iliac crests) corresponds approximately to L3-L4 but is unreliable \u2014 ultrasound identification is more accurate, particularly in obesity.",
    },
    {
        "id": "clin036", "topic": "Clinical Anaesthesia",
        "question": "Which of the following is NOT a sign of intravascular injection of local anaesthetic during epidural top-up?",
        "options": {
            "A": "Metallic taste in the mouth",
            "B": "Tinnitus and perioral numbness",
            "C": "Loss of proprioception in the legs",
            "D": "Sudden cardiovascular collapse if a large volume is injected",
            "E": "Slurred speech and tremor",
        },
        "answer": "C",
        "explanation": "Signs of inadvertent intravascular LA injection: metallic taste, circumoral/tongue numbness, tinnitus, lightheadedness, visual disturbances, agitation; then convulsions, cardiovascular collapse. Loss of proprioception is a sign of NEURAXIAL block (sensory level ascending), not systemic toxicity. Prevention: aspiration before injection, incremental dosing (3-5 mL aliquots with 30s between), use of adrenaline-containing test dose.",
    },
    {
        "id": "clin037", "topic": "Clinical Anaesthesia",
        "question": "In the CICO (can't intubate, can't oxygenate) scenario, what is the DAS 2015 recommended approach?",
        "options": {
            "A": "Continue attempting bag-mask ventilation indefinitely",
            "B": "Declare emergency, attempt supraglottic airway, then proceed immediately to front-of-neck access (FONA) if unsuccessful",
            "C": "Immediately proceed to percutaneous tracheostomy",
            "D": "Administer suxamethonium to facilitate spontaneous ventilation",
            "E": "Perform retrograde intubation as the first rescue technique",
        },
        "answer": "B",
        "explanation": "DAS 2015 guidelines for CICO: declare emergency (call for help), attempt supraglottic airway (LMA/ILMA) as a bridge, if unsuccessful proceed IMMEDIATELY to front-of-neck access (FONA) \u2014 scalpel cricothyroidotomy is fastest and most reliable. Do not delay FONA with multiple failed airway attempts. Time-critical: hypoxic cardiac arrest follows within minutes. Can't intubate + can't oxygenate = proceed to FONA.",
    },
    {
        "id": "clin038", "topic": "Clinical Anaesthesia",
        "question": "A 72-year-old man on warfarin for AF (INR 2.8) requires elective right hemicolectomy. What is the MOST appropriate management?",
        "options": {
            "A": "Proceed with surgery and reverse with vitamin K only if excessive bleeding occurs",
            "B": "Give FFP 4 units preoperatively to reduce INR",
            "C": "Stop warfarin and bridge with LMWH, targeting INR <1.5 on day of surgery",
            "D": "Cancel the case indefinitely",
            "E": "Give vitamin K 1 mg IV the night before and proceed next morning",
        },
        "answer": "C",
        "explanation": "For elective major surgery with significant bleeding risk, warfarin should be stopped 5 days pre-op. For high thromboembolic risk (AF with CHA2DS2-VASc >=5, mechanical heart valves, recent VTE), bridging with LMWH is appropriate. Target INR <1.5. FFP is not appropriate for elective reversal. The decision to bridge should be individualised with haematology/cardiology input.",
    },
    {
        "id": "clin039", "topic": "Clinical Anaesthesia",
        "question": "Which preoperative investigations should be routinely ordered before an elective inguinal hernia repair in a healthy 45-year-old non-smoker?",
        "options": {
            "A": "Full blood count, urea and electrolytes, ECG, chest X-ray, and clotting screen",
            "B": "No investigations are routinely indicated in a fit patient for this procedure",
            "C": "Full blood count and ECG only",
            "D": "Chest X-ray and spirometry",
            "E": "Group and save, full blood count, and clotting screen",
        },
        "answer": "B",
        "explanation": "NICE guidance (NG45, 2016): investigations should be based on patient risk factors and surgical complexity \u2014 NOT performed routinely. For a healthy (ASA 1-2) patient undergoing minor or intermediate surgery (e.g. inguinal hernia repair): NO routine tests needed. Investigations are indicated by comorbidities, medications, or surgical factors (major haemorrhage risk). Routine preoperative testing in low-risk patients leads to incidental findings and unnecessary delays without improving outcomes.",
    },
    {
        "id": "clin040", "topic": "Clinical Anaesthesia",
        "question": "A patient with a known grade 3 Cormack-Lehane view requires repeat anaesthesia. Which is the MOST appropriate primary plan?",
        "options": {
            "A": "Proceed with direct laryngoscopy using a standard Macintosh blade",
            "B": "Cancel the case until an ENT surgeon is available for awake tracheotomy",
            "C": "Plan awake fibreoptic intubation as the primary technique in all cases",
            "D": "Use a video laryngoscope as primary technique with a plan B of awake FOI",
            "E": "Pre-oxygenate for 5 minutes and perform standard RSI",
        },
        "answer": "D",
        "explanation": "Cormack-Lehane grade 3 (only epiglottis visible) indicates a difficult airway. DAS guidelines recommend videolaryngoscopy as the primary technique for anticipated difficult intubation in non-emergency cases. Awake fibreoptic intubation is preferred when there are additional concerns: obstructive pathology, cervical instability, high aspiration risk, predicted impossible mask ventilation. A plan B must always be formulated. The decision requires clear communication with the patient.",
    },
    {
        "id": "clin041", "topic": "Clinical Anaesthesia",
        "question": "Tranexamic acid works by which mechanism, and what evidence supports its use in major haemorrhage?",
        "options": {
            "A": "It activates coagulation factors II, VII, IX, X",
            "B": "It inhibits fibrinolysis by competitively blocking lysine binding sites on plasminogen and plasmin, preventing activation by tPA",
            "C": "It stimulates platelet aggregation via thromboxane A2",
            "D": "It reverses heparin anticoagulation",
            "E": "It activates antithrombin III to inhibit thrombin",
        },
        "answer": "B",
        "explanation": "Tranexamic acid (TXA): synthetic lysine analogue that competitively inhibits lysine binding sites on plasminogen and plasmin, preventing fibrinolysis. CRASH-2 trial: TXA 1g IV within 3 hours of injury reduces mortality in traumatic haemorrhage. Late administration (>3h) may increase mortality (prothrombotic). WOMAN trial: similar benefit in PPH. Dose: 1g IV over 10 min (faster administration causes hypotension/seizures). Dose adjustment needed in renal failure.",
    },
    {
        "id": "clin042", "topic": "Clinical Anaesthesia",
        "question": "A 28-year-old parturient requires emergency caesarean section for fetal bradycardia with no epidural in situ. The MOST appropriate anaesthetic technique is:",
        "options": {
            "A": "Spinal anaesthesia in all cases \u2014 it is always faster than general anaesthesia",
            "B": "General anaesthesia in all cases as it is fastest",
            "C": "Spinal anaesthesia if achievable without unacceptable delay, or general anaesthesia with RSI if time does not allow",
            "D": "Epidural top-up as this is safest",
            "E": "Sedation with regional anaesthesia",
        },
        "answer": "C",
        "explanation": "Spinal anaesthesia is preferred for Category 1 LSCS if it can be performed without unacceptable delay \u2014 it avoids risks of GA in the obstetric airway (Mendelson's, difficult intubation) and provides excellent analgesia. However, if time does not allow (genuine immediate threat to life), GA with RSI is appropriate. The decision requires communication between obstetrician and anaesthetist about urgency. RCOA guidelines support both depending on clinical context.",
    },
    {
        "id": "clin043", "topic": "Clinical Anaesthesia",
        "question": "What is the recommended approach to pre-oxygenation before RSI in an adult?",
        "options": {
            "A": "4 deep breaths of 100% O2 over 30 seconds",
            "B": "3 minutes of tidal volume breathing of 100% O2 via tight-fitting mask, or 8 vital capacity breaths in 60 seconds",
            "C": "1 minute of normal breathing on the anaesthetic circuit",
            "D": "2 minutes on a non-rebreathing mask",
            "E": "High-flow nasal oxygen alone (15 L/min) for 3 minutes",
        },
        "answer": "B",
        "explanation": "Optimal pre-oxygenation: 3 minutes of normal tidal breathing of 100% O2 via a tight-fitting facemask (FGF >=10 L/min), or 8 vital capacity breaths in 60 seconds. Target ETO2 >90%. This replaces nitrogen in the FRC with oxygen, extending the safe apnoea period from approximately 1 min to approximately 8 min in healthy adults. Obese, pregnant, and paediatric patients have reduced FRC and desaturate faster. High-flow nasal O2 may be used as an adjunct (apnoeic oxygenation) but not a replacement.",
    },
    {
        "id": "clin044", "topic": "Clinical Anaesthesia",
        "question": "Which of the following is a recognised risk factor for PONV according to the Apfel score?",
        "options": {
            "A": "Male sex",
            "B": "Age over 50",
            "C": "History of motion sickness or previous PONV",
            "D": "Use of regional anaesthesia",
            "E": "Use of propofol TIVA",
        },
        "answer": "C",
        "explanation": "The simplified Apfel score has 4 risk factors: female sex, non-smoker, history of PONV or motion sickness, and postoperative opioid use. Each factor adds approximately 20% risk (0 factors approximately 10%, 4 factors approximately 80%). Regional anaesthesia and propofol TIVA are PROTECTIVE against PONV. Age, type of surgery, and duration affect risk but are not in the simplified Apfel score.",
    },
    {
        "id": "clin045", "topic": "Clinical Anaesthesia",
        "question": "A 3-year-old child is scheduled for myringotomy and grommet insertion (5 minutes). What is the MOST appropriate airway management?",
        "options": {
            "A": "Rapid sequence induction and cuffed endotracheal tube",
            "B": "Awake nasal intubation",
            "C": "Inhalational induction with sevoflurane, LMA or spontaneous ventilation with facemask",
            "D": "Total intravenous anaesthesia with propofol target-controlled infusion",
            "E": "Ketamine IM with no airway device",
        },
        "answer": "C",
        "explanation": "Myringotomy/grommet insertion: very brief procedure (5 min), no aspiration risk in fasted elective child. Standard approach: inhalational induction with sevoflurane (preferred in children \u2014 no IV access needed), maintain spontaneous ventilation, facemask or LMA (LMA preferred for hands-free approach). RSI is not indicated \u2014 no aspiration risk. Nitrous oxide is commonly used as an adjunct.",
    },
    {
        "id": "clin046", "topic": "Clinical Anaesthesia",
        "question": "What weight-based dose of atropine is used to treat symptomatic bradycardia in a child?",
        "options": {
            "A": "0.02 mg/kg (minimum 0.1 mg); atropine is preferred as vagal tone is the primary cause of bradycardia in children",
            "B": "0.1 mg/kg; atropine is more potent than adrenaline in children",
            "C": "1 mg/kg; children have high vagal tone and need large doses",
            "D": "0.01 mg/kg; adrenaline is first-line in paediatric bradycardia",
            "E": "Atropine is not recommended in children under 2 years",
        },
        "answer": "A",
        "explanation": "Atropine paediatric dose: 0.02 mg/kg (minimum 0.1 mg to prevent paradoxical bradycardia from central vagal stimulation at very low doses; maximum 0.5 mg per single dose). Children are vagally dominant \u2014 bradycardia is most commonly vagally mediated (laryngoscopy, suction, hypoxia, peritoneal stimulation). For cardiac arrest bradycardia, adrenaline 10 mcg/kg is first-line per ERC/PALS guidelines. Hypoxia is the commonest cause \u2014 always treat hypoxia first.",
    },
    {
        "id": "clin047", "topic": "Clinical Anaesthesia",
        "question": "What is the definition of massive haemorrhage and the immediate management priorities?",
        "options": {
            "A": "Loss of >500 mL blood in 1 hour; priority is colloid infusion",
            "B": "Loss of one circulating blood volume in 24 hours (>70 mL/kg), or >50% volume in 3 hours; priorities are haemorrhage control, massive transfusion protocol activation, damage control resuscitation",
            "C": "Loss of >1L intraoperatively; replace with crystalloid and packed red cells only",
            "D": "Any haemorrhage requiring blood transfusion; priority is FFP administration",
            "E": "Loss causing Hb <80 g/L; priority is identifying the bleeding source",
        },
        "answer": "B",
        "explanation": "Massive haemorrhage: loss of >1 blood volume in 24h (70 mL/kg adult approximately 5L); >50% volume in 3h; or rate >150 mL/min. Management: (1) CONTROL haemorrhage source; (2) Activate massive transfusion protocol; (3) Damage control resuscitation: 1:1:1 RBC:FFP:platelets, minimise crystalloid, early cryoprecipitate if fibrinogen <2g/L; (4) Permissive hypotension for penetrating trauma until haemostasis; (5) Correct the lethal triad (hypothermia, acidosis, coagulopathy); (6) TXA within 3 hours.",
    },
    {
        "id": "clin048", "topic": "Clinical Anaesthesia",
        "question": "What formula estimates the endotracheal tube size for an uncuffed tube in a child aged 4 years?",
        "options": {
            "A": "Age/4 + 4 = 5.0 mm",
            "B": "Age/4 + 4.5 = 5.5 mm",
            "C": "Age/3 + 3.5 = 4.8 mm",
            "D": "Weight/10 + 2",
            "E": "Use the child's little finger diameter",
        },
        "answer": "A",
        "explanation": "Standard formula for uncuffed ETT internal diameter: (Age in years / 4) + 4. For a 4-year-old: (4/4) + 4 = 5.0 mm. Always have 0.5 sizes above and below available. Uncuffed tubes: ensure a small leak at 15-20 cmH2O to prevent subglottic oedema. Modern practice increasingly uses cuffed tubes in children >2 years. ETT depth: (Age/2) + 12 cm at lips. The cricoid ring is the narrowest point in children under 8-10 years.",
    },
    {
        "id": "phy_gi001", "topic": "Physiology",
        "question": "Which of the following correctly describes the Child-Pugh score?",
        "options": {
            "A": "It uses serum creatinine, INR, and bilirubin to predict 90-day mortality",
            "B": "It scores five variables \u2014 bilirubin, albumin, PT, ascites, and encephalopathy \u2014 to stratify hepatic reserve",
            "C": "It is used exclusively to stage hepatocellular carcinoma",
            "D": "A score of 5\u20136 indicates Child-Pugh class C (worst prognosis)",
            "E": "It incorporates renal function as a key variable",
        },
        "answer": "B",
        "explanation": "The Child-Pugh score combines bilirubin, albumin, PT/INR, degree of ascites, and hepatic encephalopathy grade to produce a score of 5\u201315. Class A (5\u20136) = well-compensated; Class B (7\u20139) = significant compromise; Class C (10\u201315) = decompensated. MELD score uses creatinine, bilirubin and INR. Both are used in anaesthetic risk stratification for liver disease.",
    },
    {
        "id": "phy_gi002", "topic": "Physiology",
        "question": "What is the primary function of bile salts in digestion?",
        "options": {
            "A": "Hydrolysis of triglycerides into fatty acids",
            "B": "Emulsification of dietary fats to increase lipase surface area",
            "C": "Active transport of glucose across the intestinal epithelium",
            "D": "Neutralisation of gastric acid in the duodenum",
            "E": "Synthesis of clotting factors in the portal circulation",
        },
        "answer": "B",
        "explanation": "Bile salts (synthesised from cholesterol in hepatocytes) are amphipathic molecules that emulsify dietary fats \u2014 breaking large fat globules into smaller droplets, vastly increasing the surface area available to pancreatic lipase. They also form micelles that facilitate absorption of fat-soluble vitamins (A, D, E, K) and fatty acids. They do not hydrolyse fats (that is lipase's role).",
    },
    {
        "id": "phy_gi003", "topic": "Physiology",
        "question": "Which of the following is the MOST important determinant of hepatic drug clearance for a high-extraction drug?",
        "options": {
            "A": "Plasma protein binding",
            "B": "Hepatic blood flow",
            "C": "Intrinsic hepatic enzymatic capacity",
            "D": "Renal clearance rate",
            "E": "Drug lipid solubility",
        },
        "answer": "B",
        "explanation": "For high-extraction drugs (extraction ratio >0.7, e.g. morphine, lignocaine, propranolol), hepatic clearance approaches hepatic blood flow \u2014 the liver can clear nearly all drug presented to it on each pass. Therefore clearance is limited by and directly proportional to hepatic blood flow, not enzyme capacity. Protein binding and intrinsic clearance dominate for low-extraction drugs (e.g. warfarin, diazepam).",
    },
    {
        "id": "phy_gi004", "topic": "Physiology",
        "question": "A patient with obstructive jaundice is taken for emergency surgery. Which coagulopathy pattern would you MOST expect?",
        "options": {
            "A": "Isolated thrombocytopaenia",
            "B": "Prolonged APTT with normal PT",
            "C": "Prolonged PT correctable with vitamin K",
            "D": "Disseminated intravascular coagulation pattern",
            "E": "Factor VIII deficiency",
        },
        "answer": "C",
        "explanation": "Obstructive jaundice prevents bile from reaching the gut, impairing absorption of fat-soluble vitamins including vitamin K. Vitamin K is required for hepatic synthesis of factors II, VII, IX, X (and protein C/S). Factor VII has the shortest half-life, so PT (extrinsic pathway) prolongs first. This is correctable with IV vitamin K (or FFP acutely). This contrasts with hepatocellular failure where liver synthetic function is impaired and may not respond to vitamin K.",
    },
    {
        "id": "phy_gi005", "topic": "Physiology",
        "question": "What is the approximate normal portal venous pressure?",
        "options": {
            "A": "2\u20135 mmHg",
            "B": "5\u201310 mmHg",
            "C": "15\u201320 mmHg",
            "D": "25\u201330 mmHg",
            "E": "35\u201340 mmHg",
        },
        "answer": "B",
        "explanation": "Normal portal venous pressure is 5\u201310 mmHg (portal\u2013hepatic venous pressure gradient <5 mmHg). Portal hypertension is defined as a hepatic venous pressure gradient (HVPG) >5 mmHg; clinically significant portal hypertension (risk of varices) is HVPG >10 mmHg. Causes include cirrhosis (sinusoidal), Budd-Chiari (post-sinusoidal), and portal vein thrombosis (pre-sinusoidal).",
    },
    {
        "id": "phy_gi006", "topic": "Physiology",
        "question": "Which enzyme is primarily responsible for first-pass metabolism of oral morphine?",
        "options": {
            "A": "CYP3A4 in intestinal epithelium only",
            "B": "UDP-glucuronosyltransferase (UGT) in hepatocytes, conjugating morphine to M3G and M6G",
            "C": "Plasma cholinesterase in the portal circulation",
            "D": "Monoamine oxidase in the gut wall",
            "E": "CYP2D6 producing normorphine",
        },
        "answer": "B",
        "explanation": "Oral morphine undergoes extensive first-pass metabolism (bioavailability ~30%). The primary pathway is hepatic conjugation by UGT2B7 to morphine-3-glucuronide (M3G, inactive/neuroexcitatory) and morphine-6-glucuronide (M6G, active and potent). CYP2D6 plays a minor role. This high first-pass effect explains why oral:IV morphine dose ratio is approximately 3:1.",
    },
    {
        "id": "phy_gi007", "topic": "Physiology",
        "question": "Regarding gastric emptying, which factor MOST significantly delays it?",
        "options": {
            "A": "Fasting state",
            "B": "Liquid meals",
            "C": "High fat content of a meal",
            "D": "Metoclopramide administration",
            "E": "Upright posture",
        },
        "answer": "C",
        "explanation": "Fat in the duodenum potently delays gastric emptying via CCK release and the enterogastric reflex \u2014 this is a key perioperative concern. Solids delay emptying more than liquids; high osmolarity also delays it. Anxiety, opioids, pregnancy, diabetes (gastroparesis), and pain all delay emptying. Metoclopramide is a prokinetic that accelerates emptying. The 2-hour clear fluid / 6-hour solid fasting guideline reflects these different emptying times.",
    },
    {
        "id": "phy_gi008", "topic": "Physiology",
        "question": "Which statement about the cytochrome P450 system is correct?",
        "options": {
            "A": "CYP2D6 is the most abundant hepatic CYP enzyme and metabolises the majority of drugs",
            "B": "CYP3A4 metabolises approximately 50% of all drugs and is inducible by rifampicin",
            "C": "All CYP enzymes are located exclusively in hepatocytes",
            "D": "Enzyme induction typically occurs within minutes of exposure",
            "E": "CYP inhibition increases drug clearance by competing for binding sites",
        },
        "answer": "B",
        "explanation": "CYP3A4 is the most abundant hepatic CYP (~30% of total CYP) and metabolises ~50% of drugs. It is induced by rifampicin, carbamazepine, phenytoin, and St John's Wort (increasing drug metabolism, reducing effect). Inhibited by erythromycin, azole antifungals, and grapefruit juice. CYP enzymes are also present in gut wall, lung, and kidney. Induction requires de novo protein synthesis (days not minutes). Inhibition reduces drug clearance.",
    },
    {
        "id": "ca_paeds001", "topic": "Clinical Anaesthesia",
        "question": "What is the correct formula for estimating endotracheal tube (ETT) size in children aged 2\u201310 years?",
        "options": {
            "A": "Age/4 + 3.5 (cuffed) or Age/4 + 4 (uncuffed)",
            "B": "Weight/10 + 2",
            "C": "Age/3 + 3",
            "D": "(Age + 16)/4",
            "E": "Age/2 + 6",
        },
        "answer": "A",
        "explanation": "The standard formula: uncuffed ETT internal diameter (mm) = Age/4 + 4; cuffed ETT = Age/4 + 3.5. The cuff accounts for ~0.5 mm additional external diameter. Tube length (oral) \u2248 Age/2 + 12 cm. Always have tubes 0.5 mm above and below the estimated size available. Under 2 years, size is estimated from weight and clinical assessment rather than the formula.",
    },
    {
        "id": "ca_paeds002", "topic": "Clinical Anaesthesia",
        "question": "A 6-week-old ex-premature infant (34 weeks gestation) undergoes inguinal hernia repair. What is the MOST important postoperative concern?",
        "options": {
            "A": "Hypoglycaemia from prolonged fasting",
            "B": "Postoperative apnoea requiring monitoring for at least 12 hours",
            "C": "Malignant hyperthermia from volatile anaesthetic use",
            "D": "Emergence delirium from sevoflurane",
            "E": "Hypothermia from regional anaesthetic techniques",
        },
        "answer": "B",
        "explanation": "Ex-premature infants are at significant risk of postoperative apnoea (central and obstructive) up to 60 weeks postconceptual age (PCA). This is due to immature respiratory control and brainstem chemoreceptor function. Caffeine may be given prophylactically. These infants require postoperative monitoring (SpO2 and apnoea monitor) for a minimum of 12 hours. Risk is highest in those <44 weeks PCA, with anaemia, or with prior apnoea history.",
    },
    {
        "id": "ca_paeds003", "topic": "Clinical Anaesthesia",
        "question": "Regarding laryngeal anatomy in infants compared to adults, which statement is correct?",
        "options": {
            "A": "The narrowest part of the infant airway is the glottis",
            "B": "The infant epiglottis is shorter, flatter, and less omega-shaped",
            "C": "The infant larynx is located at a higher cervical level (C3\u20134) and is more anterior",
            "D": "The infant trachea is proportionally longer relative to body size",
            "E": "Subglottic oedema has proportionally less impact on airway resistance in infants",
        },
        "answer": "C",
        "explanation": "The infant larynx is at C3\u20134 (adult C4\u20135), more anterior and cephalad \u2014 contributing to the 'sniffing' position preferred for intubation without a pillow. Classically, the narrowest point was said to be subglottis (cricoid ring), making uncuffed tubes appropriate \u2014 though this is debated. The infant epiglottis is longer, floppy, and omega-shaped, which can obstruct the view at laryngoscopy and is why straight (Miller) blades are preferred. Subglottic oedema of 1 mm reduces cross-sectional area by 75% in infants vs ~44% in adults (r\u2074 law).",
    },
    {
        "id": "ca_paeds004", "topic": "Clinical Anaesthesia",
        "question": "What is the correct intraosseous fluid resuscitation dose for a 20 kg child in septic shock?",
        "options": {
            "A": "5 mL/kg 0.9% saline",
            "B": "10 mL/kg 0.9% saline over 30 minutes",
            "C": "20 mL/kg 0.9% saline (or balanced crystalloid) as a bolus, reassessing after each",
            "D": "40 mL/kg colloid immediately",
            "E": "2 mL/kg/hr maintenance only",
        },
        "answer": "C",
        "explanation": "APLS guidelines: 20 mL/kg IV/IO bolus of 0.9% NaCl or balanced crystalloid (e.g. Hartmann's) for septic shock, reassessing after each bolus. For a 20 kg child, this is 400 mL. Up to 60 mL/kg may be given in the first hour if no improvement, watching for signs of fluid overload. The FEAST trial showed harm from albumin in African children, but crystalloid boluses remain standard in UK practice.",
    },
    {
        "id": "ca_paeds005", "topic": "Clinical Anaesthesia",
        "question": "Which of the following is a recognised feature of Pierre Robin sequence relevant to airway management?",
        "options": {
            "A": "Macroglossia, mandibular hyperplasia, and choanal atresia",
            "B": "Micrognathia, glossoptosis, and cleft palate causing airway obstruction",
            "C": "Tracheomalacia and subglottic stenosis as primary features",
            "D": "The condition is associated with normal airway anatomy at birth",
            "E": "Bag-mask ventilation is invariably impossible",
        },
        "answer": "B",
        "explanation": "Pierre Robin sequence: micrognathia (small mandible) \u2192 glossoptosis (posterior displacement of tongue) \u2192 airway obstruction \u00b1 cleft palate. Airway management is challenging \u2014 prone positioning helps acutely. Anaesthetic management may require fibreoptic intubation awake or under inhalational induction, video laryngoscopy, or tracheostomy. Associated with Stickler and other syndromes. Bag-mask ventilation is usually possible with airway adjuncts.",
    },
    {
        "id": "ca_paeds006", "topic": "Clinical Anaesthesia",
        "question": "What is the approximate blood volume of a neonate?",
        "options": {
            "A": "40 mL/kg",
            "B": "60 mL/kg",
            "C": "85 mL/kg",
            "D": "100 mL/kg",
            "E": "120 mL/kg",
        },
        "answer": "C",
        "explanation": "Estimated blood volume (EBV): neonates ~85 mL/kg; infants ~80 mL/kg; children ~75 mL/kg; adults ~70 mL/kg (male) / ~65 mL/kg (female). A 3 kg neonate has ~255 mL EBV. Maximum allowable blood loss = EBV \u00d7 (starting Hb \u2212 minimum acceptable Hb) / starting Hb. In neonates, even small volumes of blood loss represent a significant percentage of EBV, requiring careful measurement and early replacement.",
    },
    {
        "id": "ca_paeds007", "topic": "Clinical Anaesthesia",
        "question": "A 4-year-old child requires tonsillectomy. Which analgesic combination is currently recommended by NICE/RCoA guidance following concerns about codeine?",
        "options": {
            "A": "Codeine 1 mg/kg and paracetamol",
            "B": "Tramadol and ibuprofen",
            "C": "Paracetamol, ibuprofen, and dexamethasone with opioid-sparing technique",
            "D": "Morphine PCA from age 4",
            "E": "Fentanyl transdermal patch",
        },
        "answer": "C",
        "explanation": "Codeine is CONTRAINDICATED in children under 12 for post-tonsillectomy pain following EMA/MHRA guidance after deaths from respiratory depression in ultra-rapid CYP2D6 metabolisers. Current best practice: regular paracetamol + ibuprofen (if no contraindication) + dexamethasone (reduces PONV and swelling). IV morphine or intranasal diamorphine for breakthrough pain under supervision. Tramadol also has CYP2D6-dependent metabolism and is not recommended under 12.",
    },
    {
        "id": "ca_paeds008", "topic": "Clinical Anaesthesia",
        "question": "Regarding sevoflurane in paediatric anaesthesia, which statement is correct?",
        "options": {
            "A": "It cannot be used for inhalational induction due to its high pungency",
            "B": "Emergence delirium occurs in up to 80% of children and is best treated with IV ketamine",
            "C": "It is the preferred agent for inhalational induction due to its pleasant odour and low blood:gas coefficient",
            "D": "Sevoflurane causes less cardiovascular depression than halothane at equipotent doses",
            "E": "It is contraindicated in children under 1 year",
        },
        "answer": "C",
        "explanation": "Sevoflurane has replaced halothane for paediatric inhalational induction \u2014 pleasant, non-pungent odour; low blood:gas coefficient (0.65) gives rapid onset/offset; haemodynamically better tolerated than halothane (less myocardial depression, no sensitisation to catecholamines). Emergence delirium occurs in 10\u201380% \u2014 associated with rapid emergence, pain, and young age. Management: adequate analgesia (paracetamol, NSAID, opioid), quiet recovery, dexmedetomidine prophylaxis, or small-dose propofol at end of case.",
    },
    {
        "id": "ph_la002", "topic": "Pharmacology",
        "question": "Which property of a local anaesthetic MOST determines its speed of onset?",
        "options": {
            "A": "Protein binding",
            "B": "Lipid solubility",
            "C": "pKa relative to tissue pH",
            "D": "Molecular weight",
            "E": "Vasoconstrictive activity",
        },
        "answer": "C",
        "explanation": "Speed of onset is primarily determined by the fraction of drug in the unionised (lipid-soluble) form at tissue pH, governed by the Henderson-Hasselbalch equation. LA with pKa closer to physiological pH (7.4) has more unionised drug available to cross the nerve membrane \u2014 hence faster onset. Lidocaine (pKa 7.7) has faster onset than bupivacaine (pKa 8.1). Infected tissue (lower pH) reduces unionised fraction and diminishes LA efficacy. Lipid solubility relates to potency and duration.",
    },
    {
        "id": "ph_la003", "topic": "Pharmacology",
        "question": "What is the mechanism by which adrenaline prolongs local anaesthetic block?",
        "options": {
            "A": "It increases the pKa of the local anaesthetic",
            "B": "Alpha-1 mediated vasoconstriction reduces systemic absorption, maintaining local concentration",
            "C": "It directly potentiates sodium channel blockade",
            "D": "It increases protein binding of the local anaesthetic",
            "E": "It stimulates local nerve demyelination prolonging block",
        },
        "answer": "B",
        "explanation": "Adrenaline (typically 1:200,000 = 5 mcg/mL) causes alpha-1 mediated local vasoconstriction, reducing vascular uptake and systemic absorption of the LA. This prolongs block duration and reduces peak plasma concentrations (reducing systemic toxicity risk). It also allows higher total doses. Not all sites benefit equally \u2014 digital, penile, and end-arterial blocks: adrenaline-containing LA traditionally avoided due to ischaemia risk, though evidence for fingers is less clear.",
    },
    {
        "id": "ph_la004", "topic": "Pharmacology",
        "question": "Which local anaesthetic is an amide and is primarily used topically for airway anaesthesia?",
        "options": {
            "A": "Cocaine",
            "B": "Benzocaine",
            "C": "Lidocaine",
            "D": "Chloroprocaine",
            "E": "Tetracaine",
        },
        "answer": "C",
        "explanation": "Lidocaine is an amide LA with good topical activity used for airway anaesthesia (spray/nebulisation/gargle) before awake fibreoptic intubation. Max topical airway dose: 9 mg/kg (4% solution; higher limit due to slower systemic absorption from mucosa). Cocaine is an ester LA that also causes vasoconstriction \u2014 used in nasal surgery but abuse potential limits use. Benzocaine and tetracaine are esters. Chloroprocaine is an ester used in obstetrics for its rapid onset and metabolism.",
    },
    {
        "id": "ph_la005", "topic": "Pharmacology",
        "question": "Regarding prilocaine toxicity, which statement is correct?",
        "options": {
            "A": "It causes cardiac toxicity at lower doses than lidocaine",
            "B": "Its metabolite o-toluidine causes methaemoglobinaemia",
            "C": "It is safe in doses exceeding 10 mg/kg without adrenaline",
            "D": "It has a higher protein binding than bupivacaine",
            "E": "It is the preferred agent for epidural infusions",
        },
        "answer": "B",
        "explanation": "Prilocaine is metabolised to o-toluidine which oxidises haemoglobin to methaemoglobin. At doses >600 mg, clinically significant methaemoglobinaemia can occur (SpO2 falsely reads ~85%). Treatment: methylene blue 1\u20132 mg/kg IV (reduces metHb back to Hb). Despite this, prilocaine has the lowest systemic toxicity of all amide LAs \u2014 making it the agent of choice for IVRA (Bier's block). Maximum dose: 6 mg/kg plain, 8 mg/kg with adrenaline. Contraindicated in methaemoglobinaemia, anaemia.",
    },
    {
        "id": "ph_la006", "topic": "Pharmacology",
        "question": "What is the key pharmacological difference between levobupivacaine and racemic bupivacaine?",
        "options": {
            "A": "Levobupivacaine has a higher pKa giving slower onset",
            "B": "Levobupivacaine is the S(\u2013) enantiomer with reduced cardiac toxicity compared to the racemate",
            "C": "Levobupivacaine is more lipid soluble, producing a shorter duration of action",
            "D": "Levobupivacaine cannot be used for spinal anaesthesia",
            "E": "There is no clinically meaningful difference between the two",
        },
        "answer": "B",
        "explanation": "Racemic bupivacaine is a 50:50 mixture of R(+) and S(\u2013) enantiomers. The R(+) enantiomer is responsible for greater cardiac toxicity (slow Na\u207a channel dissociation, V-fib risk). Levobupivacaine (S(\u2013) enantiomer) and ropivacaine (also S(\u2013) enantiomer) have similar analgesic efficacy to racemic bupivacaine but with improved cardiovascular safety profiles. Ropivacaine also causes slightly less motor block than bupivacaine at equivalent analgesic concentrations.",
    },
    {
        "id": "ph_la007", "topic": "Pharmacology",
        "question": "Which of the following correctly describes the differential block produced by local anaesthetics?",
        "options": {
            "A": "Motor fibres are blocked before sensory fibres due to their larger diameter",
            "B": "Pain fibres (A\u03b4, C) are blocked before motor fibres (A\u03b1) due to smaller diameter and greater surface area:volume ratio",
            "C": "All fibre types are blocked simultaneously at the same LA concentration",
            "D": "Sympathetic fibres are the most resistant to LA blockade",
            "E": "Myelinated fibres are always more resistant to LA block than unmyelinated fibres",
        },
        "answer": "B",
        "explanation": "Differential block occurs because sensitivity to LA relates to fibre diameter and myelination. Order of blockade (most to least sensitive): B fibres (preganglionic sympathetic) > A\u03b4/C fibres (pain/temp) > A\u03b2 (touch/pressure) > A\u03b1 (motor). Smaller diameter = shorter internodal distance = fewer nodes needed to block (minimum 3 nodes of Ranvier must be blocked for conduction failure). This explains epidural 'sympathetic then sensory then motor' progression and the window where analgesia exists without paralysis.",
    },
    {
        "id": "ph_cvd002", "topic": "Pharmacology",
        "question": "Which of the following correctly describes the pharmacology of noradrenaline in critical care?",
        "options": {
            "A": "It acts primarily on beta-1 receptors, increasing heart rate and contractility",
            "B": "It is a potent alpha-1 and alpha-2 agonist with weak beta-1 activity, increasing SVR",
            "C": "It causes predominant vasodilation through nitric oxide release",
            "D": "It is the first-line vasopressor for anaphylaxis",
            "E": "Its half-life is approximately 4 hours requiring once-daily dosing",
        },
        "answer": "B",
        "explanation": "Noradrenaline (norepinephrine) has potent alpha-1 and alpha-2 agonist activity (vasoconstriction, increased SVR/MAP) with weak beta-1 activity. Heart rate often reflexly decreases despite increased contractility. It is first-line vasopressor for septic shock (Surviving Sepsis guidelines). Half-life is 2\u20133 minutes \u2014 given as continuous infusion only. Adrenaline is first-line for anaphylaxis. Unlike adrenaline, noradrenaline has minimal beta-2 activity.",
    },
    {
        "id": "ph_cvd003", "topic": "Pharmacology",
        "question": "A patient on a high-dose beta-blocker develops severe bradycardia and hypotension unresponsive to atropine and adrenaline. What is the MOST appropriate next step?",
        "options": {
            "A": "Digoxin 0.5 mg IV",
            "B": "Glucagon 50\u2013150 mcg/kg IV bolus",
            "C": "Amiodarone 300 mg IV",
            "D": "Calcium gluconate 10 mL 10% IV",
            "E": "Magnesium 2 g IV",
        },
        "answer": "B",
        "explanation": "Glucagon is the antidote for severe beta-blocker toxicity. It activates a distinct receptor (bypassing the blocked beta receptor) to increase cAMP, increasing HR and contractility. Dose: 50\u2013150 mcg/kg IV (5\u201310 mg in adults) as bolus, then infusion. High-dose insulin euglycaemic therapy (HIET) is a second-line option. Calcium channel blocker toxicity responds to calcium and HIET. Standard ACLS resuscitation drugs are often ineffective in beta-blocker toxicity.",
    },
    {
        "id": "ph_cvd004", "topic": "Pharmacology",
        "question": "Which statement about digoxin is correct?",
        "options": {
            "A": "It increases heart rate by enhancing AV nodal conduction",
            "B": "It inhibits Na\u207a/K\u207a-ATPase, increasing intracellular Ca\u00b2\u207a and myocardial contractility",
            "C": "Toxicity is less likely in hyperkalaemia",
            "D": "It has a short half-life of 2\u20134 hours",
            "E": "It acts primarily on vascular smooth muscle",
        },
        "answer": "B",
        "explanation": "Digoxin inhibits Na\u207a/K\u207a-ATPase \u2192 intracellular Na\u207a rises \u2192 Na\u207a/Ca\u00b2\u207a exchanger less effective \u2192 intracellular Ca\u00b2\u207a rises \u2192 positive inotropy. It also increases vagal tone (reduces HR and AV conduction \u2014 rate control in AF). Toxicity (nausea, visual disturbance, arrhythmias) is potentiated by hypokalaemia, hypomagnesaemia, hypercalcaemia, renal failure, hypothyroidism, and amiodarone. Half-life 36\u201348 hours. Therapeutic window is narrow (0.5\u20132 ng/mL).",
    },
    {
        "id": "ph_cvd005", "topic": "Pharmacology",
        "question": "What is the mechanism of action of milrinone?",
        "options": {
            "A": "Beta-1 agonist increasing cAMP via adenylyl cyclase activation",
            "B": "Phosphodiesterase-3 inhibitor preventing cAMP breakdown, producing inotropy and vasodilation",
            "C": "Alpha-1 agonist causing vasoconstriction and increased afterload",
            "D": "Calcium sensitiser at troponin C",
            "E": "Direct activation of L-type calcium channels",
        },
        "answer": "B",
        "explanation": "Milrinone (and enoximone) are PDE-3 inhibitors \u2014 preventing breakdown of cAMP in both myocardium (positive inotropy) and vascular smooth muscle (vasodilation). This 'inodilator' effect is useful in decompensated heart failure with elevated SVR and reduced CO. Unlike beta-agonists, it works independently of beta receptors (useful in beta-blocker treated patients). Side effects: hypotension, arrhythmias. Levosimendan is a calcium sensitiser (different mechanism) also used in acute heart failure.",
    },
    {
        "id": "ph_cvd006", "topic": "Pharmacology",
        "question": "Regarding vasopressin (ADH) as a vasopressor, which statement is correct?",
        "options": {
            "A": "It acts exclusively through V2 receptors in the kidney",
            "B": "It causes vasoconstriction via V1 receptors on vascular smooth muscle and is used as an adjunct in vasodilatory shock",
            "C": "It increases heart rate and cardiac output as its primary haemodynamic effect",
            "D": "It is contraindicated in septic shock",
            "E": "At clinical doses, it causes significant coronary vasoconstriction",
        },
        "answer": "B",
        "explanation": "Vasopressin acts on V1 receptors (vascular smooth muscle \u2014 vasoconstriction) and V2 receptors (renal collecting duct \u2014 water reabsorption/ADH effect). In vasodilatory shock (sepsis, post-cardiopulmonary bypass), low-dose vasopressin (0.01\u20130.04 U/min) can restore vascular tone without increasing HR. It is relatively spared by acidosis compared to catecholamines. Pitressin (terlipressin) is used in hepatorenal syndrome and variceal bleeding.",
    },
    {
        "id": "ph_cvd007", "topic": "Pharmacology",
        "question": "Which antiarrhythmic drug class do beta-blockers belong to according to the Vaughan Williams classification?",
        "options": {
            "A": "Class Ia",
            "B": "Class Ib",
            "C": "Class II",
            "D": "Class III",
            "E": "Class IV",
        },
        "answer": "C",
        "explanation": "Vaughan Williams classification: Class I = Na\u207a channel blockers (Ia: quinidine/procainamide \u2014 intermediate kinetics; Ib: lidocaine \u2014 fast off; Ic: flecainide \u2014 slow off); Class II = beta-blockers (reduce automaticity, slow AV conduction); Class III = K\u207a channel blockers prolonging APD/QT (amiodarone, sotalol); Class IV = Ca\u00b2\u207a channel blockers (verapamil, diltiazem). Amiodarone has activity across classes I\u2013IV.",
    },
    {
        "id": "phy_endo002", "topic": "Physiology",
        "question": "A patient with known phaeochromocytoma is listed for adrenalectomy. Which preoperative medication is administered FIRST?",
        "options": {
            "A": "Beta-blocker to control tachycardia",
            "B": "Alpha-blocker (phenoxybenzamine) for at least 10\u201314 days before adding beta-blockade",
            "C": "ACE inhibitor to prevent hypertensive crises",
            "D": "Spironolactone for aldosterone excess",
            "E": "Calcium channel blocker alone is sufficient",
        },
        "answer": "B",
        "explanation": "Alpha-blockade (phenoxybenzamine \u2014 irreversible non-selective; or doxazosin \u2014 selective alpha-1) must be established FIRST, for at least 10\u201314 days. This restores vascular volume and prevents uncontrolled hypertension. Only after adequate alpha-blockade is beta-blockade added (propranolol) to control reflex tachycardia. Starting a beta-blocker first risks paradoxical severe hypertension by blocking beta-2 vasodilation while alpha-mediated vasoconstriction remains unopposed \u2014 a potentially fatal error.",
    },
    {
        "id": "phy_endo003", "topic": "Physiology",
        "question": "Which of the following correctly describes normal maternal physiological changes in pregnancy that are relevant to anaesthesia?",
        "options": {
            "A": "Gastric emptying is accelerated from the first trimester",
            "B": "Minimum alveolar concentration (MAC) increases by 25\u201330%",
            "C": "Plasma cholinesterase activity increases by 25%",
            "D": "Aortocaval compression from 20 weeks causes supine hypotension syndrome",
            "E": "Functional residual capacity increases to improve oxygenation reserve",
        },
        "answer": "D",
        "explanation": "From ~20 weeks, the gravid uterus compresses the aorta and IVC in the supine position, reducing venous return and cardiac output (supine hypotension syndrome). Left lateral tilt (15\u00b0) or manual uterine displacement is mandatory for all procedures from 20 weeks. MAC decreases ~30% in pregnancy (progesterone effect). Plasma cholinesterase falls ~25% (reduced synthesis + haemodilution). FRC decreases ~20%. Gastric emptying is delayed from first trimester (progesterone) and more significantly in labour.",
    },
    {
        "id": "phy_endo004", "topic": "Physiology",
        "question": "What is the MOST likely cause of perioperative hypoglycaemia in a type 1 diabetic patient who received their usual morning insulin before surgery?",
        "options": {
            "A": "Stress hyperglycaemia masking the hypoglycaemia",
            "B": "Insulin taken without carbohydrate intake combined with surgical stress suppressing gluconeogenesis",
            "C": "Anaesthetic agents stimulating pancreatic insulin release",
            "D": "Volatile agents increasing peripheral glucose uptake",
            "E": "Hypothermia causing excess glucose utilisation",
        },
        "answer": "B",
        "explanation": "Type 1 diabetics continuing insulin without carbohydrate intake (fasting) are at high risk of hypoglycaemia. Surgical stress normally causes hyperglycaemia (cortisol, adrenaline, glucagon release) but in insulin-dependent patients who have taken their usual dose, this may be overwhelmed. Current JBDS guidelines recommend omitting rapid-acting insulin if fasting, reducing long-acting insulin by 20%, and monitoring BM hourly. Target glucose 6\u201310 mmol/L perioperatively.",
    },
    {
        "id": "phy_endo005", "topic": "Physiology",
        "question": "Which hormone is primarily responsible for the 'fight or flight' response and is secreted by the adrenal medulla?",
        "options": {
            "A": "Cortisol (80%) and aldosterone (20%)",
            "B": "Adrenaline (80%) and noradrenaline (20%)",
            "C": "ACTH and CRH",
            "D": "Glucagon and insulin",
            "E": "Noradrenaline (80%) and dopamine (20%)",
        },
        "answer": "B",
        "explanation": "The adrenal medulla secretes approximately 80% adrenaline and 20% noradrenaline in humans (chromaffin cells, modified postganglionic sympathetic neurons). Adrenaline predominates in metabolic stress responses; noradrenaline at sympathetic nerve terminals in cardiovascular regulation. Both are released in response to ACh from preganglionic sympathetic fibres. Phaeochromocytoma: medullary tumour secreting catecholamines; paraganglioma: extra-adrenal equivalent.",
    },
    {
        "id": "phy_endo006", "topic": "Physiology",
        "question": "Regarding thyroid storm, which statement is most accurate?",
        "options": {
            "A": "It is characterised by hypothermia and bradycardia",
            "B": "It is a medical emergency triggered by surgical stress, infection, or iodinated contrast in an uncontrolled hyperthyroid patient",
            "C": "Treatment with propylthiouracil alone is sufficient",
            "D": "It occurs exclusively in patients with Graves' disease",
            "E": "Serum TSH is markedly elevated",
        },
        "answer": "B",
        "explanation": "Thyroid storm is a life-threatening hypermetabolic crisis (temperature, HR, AF, CNS disturbance, heart failure). Triggers: surgery, sepsis, trauma, iodinated contrast, radioiodine. Treatment (Burch-Wartofsky criteria): propylthiouracil (blocks synthesis AND peripheral conversion of T4\u2192T3) \u2192 iodine (1 hour after PTU) \u2192 beta-blocker (propranolol) \u2192 hydrocortisone + supportive care. TSH is suppressed (undetectable), not elevated. Euthyroid state preoperatively is essential before elective surgery.",
    },
    {
        "id": "phy_endo007", "topic": "Physiology",
        "question": "What is the primary mechanism of action of insulin in glucose regulation?",
        "options": {
            "A": "Stimulates hepatic gluconeogenesis",
            "B": "Inhibits GLUT4 translocation to cell membranes",
            "C": "Facilitates glucose uptake via GLUT4 translocation in muscle and adipose tissue",
            "D": "Inhibits glycolysis in red blood cells",
            "E": "Stimulates glucagon secretion from alpha cells",
        },
        "answer": "C",
        "explanation": "Insulin binds its tyrosine kinase receptor \u2192 PI3K/Akt signalling pathway \u2192 GLUT4 vesicle translocation to plasma membrane \u2192 increased glucose uptake in skeletal muscle and adipose tissue. Insulin also promotes glycogen synthesis (liver/muscle), inhibits gluconeogenesis and glycogenolysis, stimulates protein synthesis and lipogenesis, and inhibits lipolysis. GLUT4 is the insulin-sensitive transporter; GLUT1/2 are constitutively expressed. Glucose uptake by brain and RBCs is insulin-independent.",
    },
    {
        "id": "phy_haem002", "topic": "Physiology",
        "question": "Which of the following blood products is the MOST appropriate first-line treatment for warfarin-associated intracranial haemorrhage requiring urgent reversal?",
        "options": {
            "A": "Fresh frozen plasma 15 mL/kg",
            "B": "Vitamin K 10 mg IV alone",
            "C": "Prothrombin complex concentrate (PCC) + vitamin K 5 mg IV",
            "D": "Cryoprecipitate 2 pools",
            "E": "Platelet transfusion 1 adult therapeutic dose",
        },
        "answer": "C",
        "explanation": "For emergency warfarin reversal (life-threatening bleeding): four-factor PCC (Beriplex/Octaplex) is superior to FFP \u2014 faster, smaller volume, predictable dosing, no crossmatch required. Given with vitamin K 5 mg IV (slow IV, not rapid \u2014 risk of anaphylaxis) to prevent rebound coagulopathy as PCC effect wanes. PCC restores factors II, VII, IX, X, and proteins C/S within minutes. FFP takes longer to prepare and gives large volumes. Dabigatran reversal: idarucizumab. Xa inhibitor reversal: andexanet alfa or PCC.",
    },
    {
        "id": "phy_haem003", "topic": "Physiology",
        "question": "What is the significance of 2,3-diphosphoglycerate (2,3-DPG) in haemoglobin function?",
        "options": {
            "A": "It stabilises oxyhaemoglobin, shifting the ODC to the left",
            "B": "It binds to deoxyhaemoglobin, stabilising the T-state and causing a right shift of the ODC",
            "C": "It is a cofactor for carbonic anhydrase",
            "D": "It increases haemoglobin's affinity for carbon monoxide",
            "E": "It is present in foetal haemoglobin at higher concentrations than adult Hb",
        },
        "answer": "B",
        "explanation": "2,3-DPG binds to the central cavity of deoxyhaemoglobin (T-state), stabilising it and reducing O\u2082 affinity \u2014 right shift of ODC, facilitating O\u2082 delivery to tissues. 2,3-DPG increases in: chronic hypoxia, anaemia, high altitude, chronic lung disease. Decreases in: stored blood (depleted within 24 hours of storage), hypothyroidism. HbF has lower affinity for 2,3-DPG than HbA \u2192 HbF has higher O\u2082 affinity (left-shifted ODC) \u2014 important for placental O\u2082 transfer.",
    },
    {
        "id": "phy_haem004", "topic": "Physiology",
        "question": "Regarding the coagulation cascade, which statement is correct?",
        "options": {
            "A": "The intrinsic pathway is primarily responsible for haemostasis in vivo",
            "B": "Tissue factor (TF) initiates the extrinsic pathway, which drives in vivo coagulation",
            "C": "Factor XIII is the first factor activated in the cascade",
            "D": "The PT measures intrinsic pathway function",
            "E": "Thrombin activates factors V and VIII \u2014 this is an anticoagulant feedback mechanism",
        },
        "answer": "B",
        "explanation": "In vivo haemostasis is primarily driven by the extrinsic pathway: tissue factor (TF/factor III, expressed by damaged subendothelial cells) binds factor VIIa \u2192 activates X and IX. The intrinsic pathway (contact activation \u2014 XII, XI, IX, VIII) amplifies the response. PT tests extrinsic/common pathway (factors VII, X, V, II, I); APTT tests intrinsic/common pathway (XII, XI, IX, VIII, X, V, II, I). Thrombin feedback: activates factors V, VIII, XI, XIII (amplification, not anticoagulation) and activates protein C (anticoagulant).",
    },
    {
        "id": "phy_haem005", "topic": "Physiology",
        "question": "A patient requires a massive transfusion. Which transfusion ratio is recommended by current major haemorrhage protocols?",
        "options": {
            "A": "RBC:FFP:Platelets = 6:1:1",
            "B": "RBC:FFP:Platelets = 1:1:1 (or 1:1:1 as a minimum target)",
            "C": "RBC alone until Hb <7 g/dL then add FFP",
            "D": "FFP first then RBCs",
            "E": "Cryoprecipitate as first-line product",
        },
        "answer": "B",
        "explanation": "Current UK and ATLS guidance for major haemorrhage: balanced ('damage control') resuscitation with RBC:FFP:Platelets in a 1:1:1 ratio (aiming to approximate whole blood). Tranexamic acid should be given within 3 hours of injury (CRASH-2 trial). Cryoprecipitate given early for fibrinogen <1.5 g/L. Avoid crystalloid-heavy resuscitation. Viscoelastic testing (ROTEM/TEG) guides product choice. Permissive hypotension (MAP 50\u201365 mmHg) until surgical control in penetrating trauma.",
    },
    {
        "id": "phy_haem006", "topic": "Physiology",
        "question": "Which of the following is a direct thrombin inhibitor used for heparin-induced thrombocytopaenia (HIT)?",
        "options": {
            "A": "Fondaparinux",
            "B": "Warfarin",
            "C": "Argatroban",
            "D": "Rivaroxaban",
            "E": "Protamine",
        },
        "answer": "C",
        "explanation": "HIT is a life-threatening immune-mediated complication of heparin causing paradoxical thrombosis. ALL heparin must be stopped immediately. Alternative anticoagulation: argatroban (direct thrombin inhibitor, IV, hepatically cleared \u2014 preferred in renal failure) or bivalirudin. Fondaparinux (anti-Xa, usually safe in HIT) or danaparoid may also be used. Warfarin is initially contraindicated (can cause warfarin necrosis from protein C depletion) but may be started once platelets >150. Diagnosis: 4Ts score + anti-PF4 antibodies + serotonin release assay.",
    },
    {
        "id": "phy_neuro003", "topic": "Physiology",
        "question": "What is the MOST important mechanism by which volatile anaesthetic agents produce unconsciousness?",
        "options": {
            "A": "Blockade of voltage-gated sodium channels in cortical neurons",
            "B": "Potentiation of GABA-A receptors and inhibition of NMDA receptors in the CNS",
            "C": "Activation of alpha-2 adrenoceptors in the locus coeruleus",
            "D": "Blockade of glycine receptors in the spinal cord",
            "E": "Inhibition of acetylcholinesterase at central synapses",
        },
        "answer": "B",
        "explanation": "Volatile agents have multiple CNS targets but key mechanisms include: GABA-A potentiation (hyperpolarisation, inhibition), NMDA receptor inhibition (anti-excitatory), and two-pore domain K\u207a channel (TREK-1) activation. No single 'unitary theory' explains anaesthesia. Immobility component of MAC is spinal cord mediated; unconsciousness involves thalamocortical and subcortical circuits. Alpha-2 agonists (dexmedetomidine) produce sedation via locus coeruleus. Propofol/barbiturates are pure GABA-A modulators.",
    },
    {
        "id": "phy_neuro004", "topic": "Physiology",
        "question": "Regarding intracranial pressure (ICP), which statement is correct?",
        "options": {
            "A": "Normal ICP is 15\u201325 mmHg",
            "B": "The Monro-Kellie doctrine states total intracranial volume is constant; increase in one component requires decrease in another",
            "C": "Cerebral perfusion pressure (CPP) = MAP \u2212 CVP",
            "D": "Cushing's triad consists of tachycardia, hypertension, and irregular breathing",
            "E": "Hyperventilation causes permanent reduction in ICP",
        },
        "answer": "B",
        "explanation": "Monro-Kellie doctrine: skull is a rigid box containing brain (~80%), CSF (~10%), blood (~10%). Any volume increase must be compensated by decrease in another \u2014 initially CSF displacement, then venous blood. CPP = MAP \u2212 ICP (not CVP, unless CVP > ICP). Normal ICP: 7\u201315 mmHg; raised >20 mmHg. Cushing's triad (late sign of herniation): hypertension + bradycardia + irregular breathing. Hyperventilation causes cerebral vasoconstriction (hypocapnia) reducing CBF and ICP acutely but effect wanes within hours (CSF pH normalises) \u2014 only for acute ICP crises.",
    },
    {
        "id": "phy_neuro005", "topic": "Physiology",
        "question": "Which of the following correctly describes the gate control theory of pain?",
        "options": {
            "A": "Pain signals are only transmitted via C fibres in the spinothalamic tract",
            "B": "A\u03b2 fibre activity in the dorsal horn can modulate C fibre pain transmission via inhibitory interneurons",
            "C": "Descending pain modulation originates exclusively from the cortex",
            "D": "Substance P is the primary inhibitory neurotransmitter in pain pathways",
            "E": "Gate control theory explains only acute nociceptive pain",
        },
        "answer": "B",
        "explanation": "Gate control theory (Melzack & Wall, 1965): inhibitory interneurons in the substantia gelatinosa (lamina II) modulate pain transmission cells. A\u03b2 fibre (touch/vibration) activity activates these interneurons, 'closing the gate' to C fibre pain signals. This explains: rubbing an injury reduces pain, TENS analgesia, acupuncture. Descending modulation from PAG, RVM, and locus coeruleus (endorphins, serotonin, noradrenaline) also modulates the gate. Substance P is an excitatory neuropeptide \u2014 not inhibitory.",
    },
    {
        "id": "phy_neuro006", "topic": "Physiology",
        "question": "What is the definition of wind-up in pain physiology?",
        "options": {
            "A": "Peripheral sensitisation of nociceptors following tissue injury",
            "B": "Frequency-dependent progressive amplification of spinal cord neuron responses to repeated C fibre stimulation",
            "C": "Descending facilitation of pain from the brainstem",
            "D": "The phenomenon of hyperalgesia distal to an injury site",
            "E": "Allodynia caused by sympathetically maintained pain",
        },
        "answer": "B",
        "explanation": "Wind-up: repeated low-frequency C fibre stimulation causes progressive increase in action potential output from dorsal horn neurons \u2014 a form of short-term synaptic plasticity mediated by NMDA receptor activation (requires removal of Mg\u00b2\u207a block by repeated depolarisation) and NK1 (substance P) receptor activation. Wind-up contributes to central sensitisation. Ketamine (NMDA antagonist) prevents/treats wind-up. Clinically relevant for understanding why pain escalates with repeated stimulation and why pre-emptive analgesia matters.",
    },
    {
        "id": "phy_neuro007", "topic": "Physiology",
        "question": "Which neurotransmitter is primarily released at the neuromuscular junction and what is its post-synaptic receptor?",
        "options": {
            "A": "Noradrenaline at muscarinic receptors",
            "B": "Acetylcholine at nicotinic (NM) receptors",
            "C": "Glutamate at AMPA receptors",
            "D": "GABA at GABA-A receptors",
            "E": "Acetylcholine at muscarinic M2 receptors",
        },
        "answer": "B",
        "explanation": "The NMJ: motor nerve releases ACh (from vesicles by exocytosis triggered by Ca\u00b2\u207a influx) \u2192 ACh binds nicotinic NM receptors (pentameric, 2\u03b11-\u03b2-\u03b4-\u03b5 subunits) on the end plate \u2192 Na\u207a/K\u207a influx \u2192 end plate potential \u2192 muscle action potential. ACh is hydrolysed by acetylcholinesterase. Muscarinic receptors (M1\u2013M5) are G-protein coupled \u2014 present in cardiac muscle (M2, bradycardia), smooth muscle, glands. NMBs act at nicotinic NM receptors, not muscarinic. Neostigmine inhibits AChE at both sites \u2014 hence need for anticholinergic cover.",
    },
    {
        "id": "phx_resp003", "topic": "Physics & Clinical Measurement",
        "question": "What does the flow-volume loop appearance of a fixed extrathoracic airway obstruction look like?",
        "options": {
            "A": "Normal inspiratory loop with reduced and flattened expiratory loop",
            "B": "Flattening of both inspiratory and expiratory portions of the loop",
            "C": "Reduced peak expiratory flow with a scooped-out expiratory curve",
            "D": "Markedly reduced FVC with preserved FEV1/FVC ratio",
            "E": "Normal flow-volume loop with reduced total lung capacity",
        },
        "answer": "B",
        "explanation": "Fixed extrathoracic obstruction (e.g. tracheal stenosis, rigid foreign body): limits flow equally during both inspiration AND expiration \u2192 bilateral plateau/flattening of the flow-volume loop. Variable extrathoracic (e.g. vocal cord paralysis): flattening during inspiration only (negative transmural pressure worsens obstruction). Variable intrathoracic (e.g. tracheomalacia): flattening during expiration only. The flow-volume loop is more sensitive than spirometry alone for detecting upper airway obstruction.",
    },
    {
        "id": "phx_resp004", "topic": "Physics & Clinical Measurement",
        "question": "What is lung compliance and what is the normal value for total lung compliance in an adult?",
        "options": {
            "A": "Resistance to airflow; normal 1\u20132 cmH\u2082O/L/s",
            "B": "Change in lung volume per unit change in pressure; normal ~200 mL/cmH\u2082O",
            "C": "Maximum lung volume achievable; normal 6 L",
            "D": "Pressure required to overcome airway resistance; normal 5 cmH\u2082O",
            "E": "Work of breathing per breath; normal 0.5 J/breath",
        },
        "answer": "B",
        "explanation": "Compliance = \u0394V/\u0394P (change in volume per unit change in pressure). Lung compliance alone ~200 mL/cmH\u2082O; chest wall compliance ~200 mL/cmH\u2082O; total respiratory system compliance ~100 mL/cmH\u2082O (combined in series: 1/Ctotal = 1/Clung + 1/Cwall). Compliance decreases in: pulmonary fibrosis, pulmonary oedema, ARDS, pneumonia, supine position, anaesthesia. Compliance increases in: emphysema (lung), ageing. Measured as static compliance (no flow) or dynamic compliance (during breathing, affected by airway resistance and frequency).",
    },
    {
        "id": "phx_resp005", "topic": "Physics & Clinical Measurement",
        "question": "A mechanically ventilated patient has a peak airway pressure of 35 cmH\u2082O and a plateau pressure of 20 cmH\u2082O. What does this indicate?",
        "options": {
            "A": "Reduced lung compliance",
            "B": "Increased airway resistance with normal lung compliance",
            "C": "Auto-PEEP accumulation",
            "D": "Normal ventilation parameters",
            "E": "Tension pneumothorax",
        },
        "answer": "B",
        "explanation": "Peak pressure reflects both airway resistance AND lung compliance. Plateau pressure (measured during inspiratory hold \u2014 no flow) reflects only lung compliance (static compliance = Vt/(Pplat \u2212 PEEP)). A large gradient between peak and plateau (here 15 cmH\u2082O) indicates high airway resistance (bronchospasm, kinked ETT, secretions). If plateau were also elevated (>30 cmH\u2082O), this would indicate reduced lung compliance (ARDS, pulmonary oedema). Auto-PEEP (gas trapping) also elevates both pressures but typically with abnormal flow-time waveform.",
    },
    {
        "id": "phx_resp006", "topic": "Physics & Clinical Measurement",
        "question": "What is the closing capacity and when does it become clinically relevant?",
        "options": {
            "A": "The total lung capacity at which all airways close; relevant only in emphysema",
            "B": "The lung volume at which dependent airways begin to close; becomes greater than FRC in elderly, obese, and supine patients causing V/Q mismatch",
            "C": "The volume at which the patient can no longer generate expiratory flow",
            "D": "The residual volume minus the expiratory reserve volume",
            "E": "The pressure at which the carina closes during forced expiration",
        },
        "answer": "B",
        "explanation": "Closing capacity (CC) = closing volume + residual volume. It is the lung volume at which small dependent airways begin to close, trapping gas. Normally CC < FRC (airways remain open throughout tidal breathing). CC becomes > FRC (causing airway closure, V/Q mismatch, and shunting) in: elderly (CC increases with age \u2014 reduced elastic recoil), obese patients, supine position (FRC reduces by ~25%), and pregnancy (FRC reduced 20%). This explains why these patients desaturate faster during apnoea and why PEEP improves oxygenation.",
    },
    {
        "id": "phx_resp007", "topic": "Physics & Clinical Measurement",
        "question": "What is the purpose of the PEEP valve in anaesthetic breathing circuits and what is the clinical effect of 5 cmH\u2082O PEEP?",
        "options": {
            "A": "Prevents rebreathing by maintaining FGF above minute ventilation",
            "B": "Maintains positive end-expiratory pressure, preventing alveolar collapse and improving FRC and oxygenation",
            "C": "Limits peak inspiratory pressure to prevent barotrauma",
            "D": "Regulates the fresh gas flow rate in the circuit",
            "E": "Prevents auto-PEEP by increasing expiratory time",
        },
        "answer": "B",
        "explanation": "PEEP (positive end-expiratory pressure) splints the alveoli open at end-expiration, increasing FRC and recruiting collapsed alveoli. 5 cmH\u2082O ('physiological PEEP') is commonly applied in theatre to partially offset the FRC reduction of anaesthesia and improve oxygenation. Higher PEEP (e.g. 10\u201315 in ARDS) improves oxygenation but risks: barotrauma, reduced venous return, reduced CO (especially with hypovolaemia), increased ICP, and hepatic/renal hypoperfusion. Optimal PEEP balances alveolar recruitment vs overdistension.",
    },
    {
        "id": "phx_stats003", "topic": "Physics & Clinical Measurement",
        "question": "What is the number needed to treat (NNT) if a treatment reduces absolute risk of an outcome from 20% to 15%?",
        "options": {
            "A": "5",
            "B": "10",
            "C": "15",
            "D": "20",
            "E": "100",
        },
        "answer": "D",
        "explanation": "NNT = 1 / Absolute Risk Reduction (ARR). ARR = control risk \u2212 treatment risk = 20% \u2212 15% = 5% = 0.05. NNT = 1/0.05 = 20. This means 20 patients need to be treated for 1 to benefit. NNT of 1 = perfect treatment. Relative risk reduction (RRR) = ARR/control risk = 5/20 = 25% \u2014 this sounds more impressive but doesn't account for baseline risk. Always prefer ARR/NNT for clinical decision-making. NNH (number needed to harm) uses the same calculation for adverse events.",
    },
    {
        "id": "phx_stats004", "topic": "Physics & Clinical Measurement",
        "question": "What is the difference between sensitivity and specificity of a diagnostic test?",
        "options": {
            "A": "Sensitivity = TP/(TP+FP); specificity = TN/(TN+FN)",
            "B": "Sensitivity = TP/(TP+FN) \u2014 ability to detect true positives; specificity = TN/(TN+FP) \u2014 ability to correctly identify true negatives",
            "C": "Sensitivity measures how reproducible the test is; specificity measures its accuracy",
            "D": "Both are independent of disease prevalence in the test population",
            "E": "A test with 100% specificity will have no false negatives",
        },
        "answer": "B",
        "explanation": "Sensitivity = TP/(TP+FN) = 'SN OUT' \u2014 a highly sensitive test, when negative, rules OUT disease (high sensitivity \u2192 few false negatives). Specificity = TN/(TN+FP) = 'SP IN' \u2014 a highly specific test, when positive, rules IN disease (high specificity \u2192 few false positives). Positive predictive value (PPV) and negative predictive value (NPV) depend on disease prevalence. Likelihood ratios (+LR = sensitivity/(1-specificity); \u2212LR = (1-sensitivity)/specificity) are independent of prevalence.",
    },
    {
        "id": "phx_stats005", "topic": "Physics & Clinical Measurement",
        "question": "Which study design provides the highest level of evidence for therapeutic interventions?",
        "options": {
            "A": "Prospective cohort study",
            "B": "Randomised controlled trial (RCT)",
            "C": "Systematic review and meta-analysis of RCTs",
            "D": "Case-control study",
            "E": "Cross-sectional survey",
        },
        "answer": "C",
        "explanation": "Evidence hierarchy (GRADE/Oxford CEBM): systematic review/meta-analysis of RCTs > individual RCT > cohort study > case-control study > case series > expert opinion. Meta-analyses pool data from multiple RCTs, increasing statistical power and precision. However, quality depends on the constituent trials (GIGO \u2014 garbage in, garbage out). For rare outcomes or questions where RCTs are unethical, observational studies may be best available evidence. The 'hierarchy' guides, not dictates \u2014 a single large well-designed RCT may outweigh a poor meta-analysis.",
    },
    {
        "id": "phx_stats006", "topic": "Physics & Clinical Measurement",
        "question": "A clinical trial reports a hazard ratio (HR) of 0.75 with 95% CI 0.60\u20130.95, p=0.02. How should this be interpreted?",
        "options": {
            "A": "The treatment increases the hazard of the outcome by 75%",
            "B": "The treatment reduces the hazard of the outcome by 25%; the result is statistically significant and the CI does not cross 1",
            "C": "The result is not statistically significant as p >0.01",
            "D": "The wide confidence interval means the result is clinically insignificant",
            "E": "A HR of 0.75 means 75 fewer events per 1000 patients",
        },
        "answer": "B",
        "explanation": "HR = ratio of hazard rates between groups. HR < 1 = reduced hazard (benefit). HR 0.75 = 25% reduction in hazard. The 95% CI 0.60\u20130.95 does not cross 1 (null hypothesis) \u2192 statistically significant. p=0.02 < 0.05 confirms this. The width of the CI reflects precision \u2014 narrower is more precise. Statistical significance (p < threshold) and clinical significance (magnitude of effect and CI) must both be considered. A statistically significant result with a tiny effect size may not be clinically meaningful.",
    },
    {
        "id": "phx_stats007", "topic": "Physics & Clinical Measurement",
        "question": "What is the MOST appropriate measure of central tendency for a skewed dataset such as length of hospital stay?",
        "options": {
            "A": "Mean, as it uses all data points",
            "B": "Mode, as it represents the most common value",
            "C": "Median, as it is resistant to the influence of extreme values (outliers)",
            "D": "Standard deviation",
            "E": "Variance",
        },
        "answer": "C",
        "explanation": "Length of hospital stay is typically right-skewed (most patients have short stays; a few have very long stays). The mean is distorted by outliers in skewed data. The median (middle value when ranked) is robust to extreme values and is the appropriate measure of central tendency for skewed data. Parametric statistics (mean, SD, t-tests) assume normally distributed data; non-parametric equivalents (median, IQR, Mann-Whitney) are used for skewed or ordinal data. Mode = most frequent value \u2014 useful for categorical data.",
    },
    {
        "id": "phx_elec005", "topic": "Physics & Clinical Measurement",
        "question": "What is microshock and why is it a significant risk in the cardiac catheter laboratory?",
        "options": {
            "A": "Electrical current > 1 A delivered via skin \u2014 causes burns",
            "B": "Small current (as little as 100 \u00b5A) delivered directly to the heart via an intracardiac catheter causing ventricular fibrillation",
            "C": "Static discharge from theatre equipment causing pacemaker interference",
            "D": "Diathermy current causing electrolyte disturbance",
            "E": "Current leakage causing tingling sensation without cardiac risk",
        },
        "answer": "B",
        "explanation": "Macroshock: current passing through the body surface \u2014 skin resistance limits effect; VF threshold ~100 mA. Microshock: current bypassing skin (via intracardiac catheter, pacemaker wire, saline column in CVP line) \u2014 directly to myocardium; VF threshold as low as 50\u2013100 \u00b5A. At-risk situations: cardiac catheterisation, temporary pacing wires, CVP with saline conductor. Prevention: isolated circuits, earth-free environments, equipotential bonding, careful handling of intracardiac conductors. Maximum safe leakage current in cardiac-protected areas: 10 \u00b5A.",
    },
    {
        "id": "phx_elec006", "topic": "Physics & Clinical Measurement",
        "question": "What is the purpose of the isolated circuit (floating earth) in an operating theatre?",
        "options": {
            "A": "To reduce electrical resistance in surgical diathermy equipment",
            "B": "To prevent current flowing through the patient to earth if a single fault occurs, requiring two simultaneous faults for electrocution",
            "C": "To increase voltage available for defibrillation",
            "D": "To ground all equipment to the same earth point",
            "E": "To eliminate all electromagnetic interference from monitoring equipment",
        },
        "answer": "B",
        "explanation": "Standard mains supply has a live and neutral wire (neutral earthed at the substation). Single fault (live wire contact) = current flows through patient to earth \u2192 electrocution. Isolated (IT) systems float both conductors above earth \u2014 single fault creates an alarm (line isolation monitor/LIM) but NO completed circuit \u2192 no current flows through the patient. Two simultaneous faults required for electrocution. Required in wet areas (operating theatres, catheter labs) where patient contact resistance is reduced. The LIM monitors impedance to earth and alarms if it falls below a safe threshold.",
    },
    {
        "id": "phx_elec007", "topic": "Physics & Clinical Measurement",
        "question": "What is the difference between cutting and coagulation modes of surgical diathermy?",
        "options": {
            "A": "Cutting uses DC current; coagulation uses AC current",
            "B": "Cutting uses continuous high-frequency AC causing rapid cell vaporisation; coagulation uses interrupted bursts causing slower heating and protein denaturation",
            "C": "Cutting mode uses higher voltages with lower frequency",
            "D": "Coagulation mode delivers higher total energy than cutting mode",
            "E": "They both use the same waveform but at different frequencies",
        },
        "answer": "B",
        "explanation": "Both modes use high-frequency AC (300 kHz \u2013 3 MHz) \u2014 high frequency avoids nerve/muscle stimulation. Cutting: continuous sine wave \u2192 rapid resistive heating \u2192 immediate cell vaporisation (cutting effect). Coagulation: interrupted (damped/pulsed) waveform \u2192 slower heating \u2192 protein denaturation and thrombosis without vaporisation. Blend: mixture of both. Bipolar diathermy (current flows between two tips of forceps) safer than monopolar (current flows through patient to plate) near implants, in limbs, and during pregnancy.",
    },
    {
        "id": "phx_elec008", "topic": "Physics & Clinical Measurement",
        "question": "A patient's defibrillator delivers 200 J. Which physical quantity does this measure?",
        "options": {
            "A": "Power (watts)",
            "B": "Charge (coulombs)",
            "C": "Voltage (volts)",
            "D": "Energy (joules)",
            "E": "Current (amperes)",
        },
        "answer": "D",
        "explanation": "Joules measure energy (E = \u00bdCV\u00b2 for a capacitor discharge). Defibrillation dose is prescribed in joules: monophasic 360 J; biphasic (more efficient \u2014 same efficacy at lower energy) 120\u2013200 J for VF/pulseless VT (RCUK guidelines). Power = energy/time (watts). Voltage = energy/charge. The defibrillator charges a capacitor to a set energy level, then discharges it across the chest wall. Transthoracic impedance (~70 \u03a9) affects the actual current delivered, which is why some defibrillators use impedance compensation.",
    },
    {
        "id": "phx_elec009", "topic": "Physics & Clinical Measurement",
        "question": "Which of the following statements about pacemakers and diathermy is correct?",
        "options": {
            "A": "Bipolar diathermy has no effect on pacemakers",
            "B": "Monopolar diathermy can cause pacemaker inhibition or reprogramming; bipolar diathermy is preferred and current should be kept away from the pacemaker",
            "C": "All modern pacemakers are immune to diathermy interference",
            "D": "Diathermy should be used only in burst mode to prevent interference",
            "E": "The pacemaker should be deactivated before all surgical procedures",
        },
        "answer": "B",
        "explanation": "Monopolar diathermy: current path through patient to return plate \u2014 if this passes near the pacemaker/leads, it can cause: inhibition (device 'sees' diathermy as intrinsic activity and withholds pacing), triggering, or reprogramming. Precautions: use bipolar diathermy where possible; if monopolar, use short bursts (<1 s) at lowest effective power; place return plate so current path avoids pacemaker; have magnet available (converts to asynchronous mode). Pacemaker-dependent patients: programme to asynchronous (DOO/VOO) mode preoperatively. Consult electrophysiology/manufacturer.",
    },
    {
        "id": "ca_obs004", "topic": "Clinical Anaesthesia",
        "question": "A parturient develops a high spinal block following epidural top-up for LSCS. BP drops to 65/40 mmHg and she becomes apnoeic. After securing the airway, which vasopressor is MOST appropriate?",
        "options": {
            "A": "Metaraminol 0.5 mg IV bolus",
            "B": "Noradrenaline 0.1 mcg/kg/min infusion",
            "C": "Ephedrine 30 mg IV bolus",
            "D": "Adrenaline 1 mg IV (1:10,000)",
            "E": "Phenylephrine 100 mcg IV",
        },
        "answer": "A",
        "explanation": "In total spinal with cardiovascular collapse, bolus vasopressors (metaraminol 0.5\u20132 mg IV or phenylephrine 50\u2013100 mcg IV) are first line to restore BP rapidly. Noradrenaline infusion is appropriate if sustained vasopressor support is needed. Ephedrine 3\u20136 mg boluses may be used (acts faster than infusion, has beta activity preserving HR). Adrenaline 1 mg is for cardiac arrest only \u2014 at this dose in a conscious patient would cause severe hypertension and arrhythmias. Left lateral tilt, IV fluids, and atropine for bradycardia are also required.",
    },
    {
        "id": "ca_obs005", "topic": "Clinical Anaesthesia",
        "question": "Which of the following is the MOST effective intervention to prevent spinal anaesthesia-induced hypotension at elective caesarean section?",
        "options": {
            "A": "Pre-loading with 1 litre of crystalloid before spinal",
            "B": "Phenylephrine infusion started prophylactically at spinal insertion",
            "C": "Performing spinal with the patient in the left lateral position throughout",
            "D": "Using hyperbaric bupivacaine rather than isobaric",
            "E": "Limiting the spinal dose to 7 mg bupivacaine",
        },
        "answer": "B",
        "explanation": "Prophylactic phenylephrine infusion (titrated to maintain systolic BP \u226580% baseline) is the most evidence-based intervention to prevent hypotension at spinal LSCS (Cochrane reviews, NICE guidance). Pre-loading with crystalloid is largely ineffective (rapidly redistributes). Co-loading (crystalloid at time of spinal) is more effective than pre-loading. Metaraminol infusion is an equally effective alternative. Phenylephrine was previously avoided due to concerns about bradycardia and reduced CO, but uteroplacental flow is better preserved than with ephedrine.",
    },
    {
        "id": "ca_obs006", "topic": "Clinical Anaesthesia",
        "question": "What is the MOST common anaesthetic cause of maternal death in the UK according to MBRRACE-UK reports?",
        "options": {
            "A": "Failed intubation",
            "B": "Failed regional anaesthesia leading to awareness",
            "C": "Aspiration of gastric contents (Mendelson's syndrome)",
            "D": "Complications of general anaesthesia including aspiration and failed intubation",
            "E": "Epidural haematoma",
        },
        "answer": "D",
        "explanation": "MBRRACE-UK consistently identifies complications of general anaesthesia (principally failed intubation and aspiration) as the leading direct anaesthetic causes of maternal mortality, though absolute numbers are small. The overall anaesthetic-related maternal death rate has fallen dramatically with increased use of regional anaesthesia for LSCS. Failed intubation in obstetrics is ~1:300 (cf. ~1:2000 non-obstetric) due to airway oedema, weight, and reduced FRC. RSI with cricoid pressure and video laryngoscopy are standard. MBRRACE-UK reports every 3 years.",
    },
    {
        "id": "ca_obs007", "topic": "Clinical Anaesthesia",
        "question": "Regarding the use of oxytocin intraoperatively, which statement is correct?",
        "options": {
            "A": "A rapid IV bolus of oxytocin 10 IU is recommended at delivery",
            "B": "Oxytocin causes vasodilation, hypotension, and reflex tachycardia; slow IV administration (3 IU over 30s) or infusion is recommended",
            "C": "Oxytocin is contraindicated in patients with pre-eclampsia",
            "D": "Carboprost is the first-line agent for uterine atony",
            "E": "Oxytocin has a long half-life, requiring only a single dose",
        },
        "answer": "B",
        "explanation": "Oxytocin causes vasodilation (NO-mediated), hypotension, and reflex tachycardia \u2014 a rapid 10 IU IV bolus can cause severe cardiovascular compromise, particularly in haemodynamically compromised patients. Current RCOG/AAGBI guidance: 3 IU slow IV bolus (over 30 seconds) at delivery of anterior shoulder, followed by infusion 20\u201340 mIU/min. Short half-life (~3\u20135 min) necessitates infusion. Carboprost (PGF2\u03b1) is third-line after oxytocin and ergometrine. Ergometrine causes vasoconstriction \u2014 use with caution in hypertension.",
    },
    {
        "id": "ca_obs008", "topic": "Clinical Anaesthesia",
        "question": "A patient with pre-eclampsia is on magnesium infusion. She develops areflexia and respiratory rate drops to 8/min. What is the immediate management?",
        "options": {
            "A": "Reduce the magnesium infusion rate by 50%",
            "B": "Administer calcium gluconate 10 mL of 10% IV immediately and stop the infusion",
            "C": "Give naloxone 400 mcg IV",
            "D": "Intubate and ventilate",
            "E": "Observe and recheck in 30 minutes",
        },
        "answer": "B",
        "explanation": "Magnesium toxicity: loss of deep tendon reflexes is the first sign of toxicity (~4\u20135 mmol/L) and is the clinical monitor. Respiratory depression (~5\u20136 mmol/L) is a medical emergency. Immediate management: stop magnesium infusion + calcium gluconate 10 mL 10% IV over 10 minutes (calcium antagonises magnesium competitively at the NMJ and neurone). Calcium chloride 10 mL 10% is an alternative (3\u00d7 more elemental calcium). Have resuscitation equipment available. Check Mg level. Antidote must be immediately available whenever magnesium is infused.",
    },
    {
        "id": "ca_obs009", "topic": "Clinical Anaesthesia",
        "question": "Which epidural drug combination is used for labour epidural analgesia in the UK and what are its advantages?",
        "options": {
            "A": "High-concentration bupivacaine 0.5% alone for rapid dense block",
            "B": "Low-concentration bupivacaine (0.0625\u20130.1%) with fentanyl (1\u20132 mcg/mL) providing analgesia with minimal motor block",
            "C": "Ropivacaine 0.75% for its superior motor-sparing properties",
            "D": "Lignocaine 2% for rapid onset",
            "E": "Chloroprocaine alone as it is the safest option",
        },
        "answer": "B",
        "explanation": "Low-concentration local anaesthetic + opioid combinations (e.g. bupivacaine 0.1% + fentanyl 2 mcg/mL, or levobupivacaine/ropivacaine equivalent) are standard for labour epidurals. Advantages: good analgesia with preserved motor function (mobile epidural), lower LA dose, synergism allows LA dose reduction. Fentanyl enhances analgesia via spinal opioid receptors (A\u03b4/C fibre modulation). High-concentration bupivacaine 0.5% causes dense motor block incompatible with mobilisation and birthing positions, and has higher cardiac toxicity risk.",
    },
    {
        "id": "ca_preop005", "topic": "Clinical Anaesthesia",
        "question": "A patient is listed for total hip replacement. She has a bare metal coronary stent inserted 3 weeks ago and takes aspirin and clopidogrel. What is the most appropriate advice?",
        "options": {
            "A": "Proceed immediately \u2014 stents are not a contraindication to surgery",
            "B": "Delay elective surgery for at least 1 year post-BMS; if essential, continue DAPT perioperatively with haematology input",
            "C": "Stop both antiplatelet agents 7 days before surgery",
            "D": "Switch to warfarin anticoagulation perioperatively",
            "E": "Proceed if clopidogrel is stopped but continue aspirin",
        },
        "answer": "B",
        "explanation": "Bare metal stents (BMS) require dual antiplatelet therapy (DAPT) for minimum 4\u20136 weeks post-insertion to prevent in-stent thrombosis (mortality ~45%). Drug-eluting stents (DES): minimum 6\u201312 months DAPT. Elective surgery should be delayed to complete this period. If surgery is truly essential (life-threatening emergency), discuss with cardiologist \u2014 DAPT continued perioperatively with haematologist input regarding bleeding risk, arterial sheath access rather than neuraxial blocks. The risk of catastrophic stent thrombosis from premature DAPT withdrawal greatly outweighs surgical bleeding risk.",
    },
    {
        "id": "ca_preop006", "topic": "Clinical Anaesthesia",
        "question": "What is the ASA physical status classification for a patient with symptomatic heart failure (NYHA III), poorly controlled type 2 diabetes, and morbid obesity (BMI 45)?",
        "options": {
            "A": "ASA I",
            "B": "ASA II",
            "C": "ASA III",
            "D": "ASA IV",
            "E": "ASA V",
        },
        "answer": "C",
        "explanation": "ASA classification: I = normal healthy; II = mild systemic disease (no functional limitation); III = severe systemic disease with functional limitation (not incapacitating); IV = severe disease that is constant threat to life; V = moribund, not expected to survive 24h without surgery; VI = brain-dead organ donor. Symptomatic heart failure NYHA III (significant limitation with ordinary activity), poorly controlled DM, and morbid obesity each qualify as ASA III. Multiple ASA III conditions do not automatically create ASA IV unless they constitute an immediate threat to life. This patient = ASA III.",
    },
    {
        "id": "ca_preop007", "topic": "Clinical Anaesthesia",
        "question": "Regarding CPET (cardiopulmonary exercise testing) before major surgery, what does a VO\u2082 max of less than 11 mL/kg/min indicate?",
        "options": {
            "A": "Low anaesthetic risk requiring no further investigation",
            "B": "High cardiorespiratory risk associated with significantly increased perioperative morbidity and mortality",
            "C": "Respiratory disease requiring bronchodilators preoperatively",
            "D": "Cardiac output is adequate for surgery",
            "E": "Normal functional capacity for a 70-year-old",
        },
        "answer": "B",
        "explanation": "CPET measures VO\u2082max (maximal oxygen consumption) and the anaerobic threshold (AT). VO\u2082max <11 mL/kg/min or AT <10 mL/kg/min predicts significantly increased perioperative risk for major abdominal, thoracic, and vascular surgery. Guides: HDU/ICU planning, patient counselling, risk optimisation (e.g. cardiac rehabilitation). Functional capacity equivalent: <4 METs (unable to climb one flight of stairs) correlates with increased risk. CPET is more objective than questionnaire-based METs estimation and is recommended for high-risk patients before major surgery (NICE, ERAS guidelines).",
    },
    {
        "id": "ca_preop008", "topic": "Clinical Anaesthesia",
        "question": "Which is the most appropriate perioperative management of a patient's regular ACE inhibitor before elective major surgery?",
        "options": {
            "A": "Always continue \u2014 withholding causes rebound hypertension",
            "B": "Withhold on the day of surgery and 24 hours before major surgery to reduce risk of refractory intraoperative hypotension",
            "C": "Switch to an oral beta-blocker for 48 hours perioperatively",
            "D": "Double the dose to provide cardiovascular protection",
            "E": "Continue only if the patient has heart failure",
        },
        "answer": "B",
        "explanation": "ACE inhibitors (and ARBs) inhibit angiotensin II-mediated vasoconstriction \u2014 on induction of anaesthesia (vasodilation, reduced sympathetic tone) this can cause refractory hypotension unresponsive to ephedrine/phenylephrine (requires vasopressin/methylene blue). NICE/RCoA guidance: withhold ACE inhibitors and ARBs on the day of surgery (and ideally 24 hours before for major surgery). Exception: consider continuing in patients with significant heart failure where haemodynamic benefits may outweigh risks, with senior anaesthetic input. Restart when euvolaemic postoperatively.",
    },
    {
        "id": "ph_other004", "topic": "Pharmacology",
        "question": "What is the mechanism of action of dexamethasone as an antiemetic?",
        "options": {
            "A": "5-HT3 receptor antagonism in the vagus nerve and CTZ",
            "B": "NK1 receptor antagonism in the vomiting centre",
            "C": "The precise mechanism is unclear but likely involves prostaglandin inhibition and changes in serotonin turnover in the CNS",
            "D": "Dopamine D2 antagonism in the chemoreceptor trigger zone",
            "E": "Histamine H1 antagonism in the vestibular nucleus",
        },
        "answer": "C",
        "explanation": "Dexamethasone's antiemetic mechanism is incompletely understood \u2014 proposed mechanisms include: inhibition of prostaglandin synthesis, reduced serotonin (5-HT) release in the GI tract, and direct central effects on the nucleus tractus solitarius. It is highly effective for PONV prophylaxis (NNT ~4), with additional benefits of antiemesis extending to 24h (longer duration than ondansetron), pain reduction, and reduced fatigue. Dose: 4\u20138 mg IV at induction. It reduces PONV most when given before induction. QualAP and IMPACT meta-analyses confirmed efficacy.",
    },
    {
        "id": "ph_other005", "topic": "Pharmacology",
        "question": "What is the mechanism by which sodium citrate is given before rapid sequence induction in obstetrics?",
        "options": {
            "A": "It neutralises gastric acid, raising gastric pH to reduce aspiration pneumonitis risk",
            "B": "It increases lower oesophageal sphincter tone",
            "C": "It reduces gastric volume by promoting emptying",
            "D": "It coats the gastric mucosa to prevent acid secretion",
            "E": "It acts as a prokinetic agent",
        },
        "answer": "A",
        "explanation": "Sodium citrate 30 mL (0.3M) is a non-particulate antacid that rapidly neutralises gastric acid, raising pH to >2.5 within minutes (duration ~30\u201360 min). Aspiration pneumonitis (Mendelson's syndrome) risk is greatly increased when gastric pH <2.5 and volume >25 mL. Non-particulate (clear) antacids are preferred over particulate (magnesium trisilicate) which themselves cause pulmonary damage if aspirated. Sodium citrate is given immediately before RSI in obstetric anaesthesia, combined with ranitidine (H2 blocker) and/or metoclopramide for maximum protection.",
    },
    {
        "id": "ph_other006", "topic": "Pharmacology",
        "question": "Regarding tranexamic acid, which statement is correct?",
        "options": {
            "A": "It directly inhibits thrombin formation in the coagulation cascade",
            "B": "It is a synthetic lysine analogue that competitively inhibits plasminogen activation, reducing fibrinolysis",
            "C": "It should be given with heparin to prevent thrombosis",
            "D": "Its use is limited to topical surgical application only",
            "E": "It increases the risk of venous thromboembolism at standard doses used in trauma",
        },
        "answer": "B",
        "explanation": "Tranexamic acid (TXA) is a synthetic lysine analogue that competitively inhibits plasminogen binding to fibrin, preventing plasmin formation and thereby reducing fibrinolysis. Evidence: CRASH-2 (trauma \u2014 reduced mortality when given within 3h), WOMAN (postpartum haemorrhage \u2014 reduced death from bleeding), HiTAS (TXA in hip arthroplasty). Standard doses do not significantly increase VTE risk. Dose: 1g IV over 10 minutes (trauma/PPH), topically in arthroplasty. Contraindications: haematuria (risk of ureteral clot), established thrombus.",
    },
    {
        "id": "ph_other007", "topic": "Pharmacology",
        "question": "What is the clinical significance of the interaction between MAO inhibitors (MAOIs) and pethidine (meperidine)?",
        "options": {
            "A": "It causes excessive sedation through additive opioid effects only",
            "B": "It can cause a potentially fatal serotonin syndrome or excitatory reaction characterised by hyperpyrexia, agitation, convulsions, and cardiovascular instability",
            "C": "It reduces the analgesic efficacy of pethidine",
            "D": "It causes severe respiratory depression through enhanced opioid effect",
            "E": "The interaction is clinically insignificant with modern reversible MAOIs",
        },
        "answer": "B",
        "explanation": "Pethidine has weak serotonin reuptake inhibitor (SRI) activity. Combined with MAOIs (irreversible: phenelzine, tranylcypromine; reversible RIMA: moclobemide), this causes serotonin syndrome: hyperthermia, agitation, myoclonus, autonomic instability \u2014 potentially fatal. This is an absolute contraindication. All opioids should be used with caution in patients on MAOIs, but pethidine is the most dangerous. Morphine is safer but still use with caution. Even two weeks washout after stopping irreversible MAOIs is required before elective anaesthesia. Modern SSRIs/SNRIs with tramadol/pethidine also risk serotonin syndrome.",
    },
    {
        "id": "ph_other008", "topic": "Pharmacology",
        "question": "Which of the following correctly describes the pharmacology of cyclizine?",
        "options": {
            "A": "It is a 5-HT3 antagonist used for chemotherapy-induced nausea",
            "B": "It is an H1 antihistamine with antimuscarinic properties acting on the vomiting centre and vestibular pathways",
            "C": "It acts on dopamine D2 receptors in the CTZ and causes extrapyramidal side effects",
            "D": "It is a neurokinin-1 antagonist with prolonged antiemetic duration",
            "E": "It enhances gastric emptying through cholinergic mechanisms",
        },
        "answer": "B",
        "explanation": "Cyclizine is an H1 antihistamine with anticholinergic (antimuscarinic) properties. It acts primarily on the vomiting centre (nucleus tractus solitarius/lateral reticular formation) and vestibular pathways \u2014 making it useful for motion sickness, inner ear disease, and opioid-induced nausea. Does not act on CTZ dopamine receptors (cf. prochlorperazine/metoclopramide). Antimuscarinic effects: dry mouth, blurred vision, urinary retention. IV administration can cause tachycardia \u2014 give slowly. Contraindicated in severe heart failure (causes tachycardia and peripheral vasoconstriction).",
    },
    {
        "id": "ph_nmb005", "topic": "Pharmacology",
        "question": "What is the significance of the train-of-four (TOF) ratio in neuromuscular monitoring?",
        "options": {
            "A": "A ratio >0.9 confirms complete reversal and safe extubation",
            "B": "The TOF ratio measures peak inspiratory force",
            "C": "A TOF count of 4 with fade confirms adequate reversal",
            "D": "TOF is measured using single-twitch stimulation at 0.1 Hz",
            "E": "A TOF count of 2 is sufficient for safe extubation",
        },
        "answer": "A",
        "explanation": "TOF: four supramaximal stimuli at 2 Hz. TOF ratio = T4/T1. With non-depolarising NMBs, fade occurs (later twitches more blocked). TOF ratio <0.9 indicates residual block \u2014 the patient may appear awake but have pharyngeal dysfunction, aspiration risk, and hypoxic ventilatory response impairment. TOF ratio \u22650.9 (acceleromyography) or ideally \u22651.0 confirms adequate recovery. TOF count (number of twitches 0\u20134) guides reversal: neostigmine most effective when TOF count = 4 (with fade); sugammadex can reverse at any count. Subjective 'feel' of fade is unreliable \u2014 quantitative monitoring is strongly recommended.",
    },
    {
        "id": "ph_nmb006", "topic": "Pharmacology",
        "question": "What is the ED95 and how does it relate to intubating dose of rocuronium?",
        "options": {
            "A": "The dose producing 95% neuromuscular block at the adductor pollicis; intubating dose is typically 2\u00d7 ED95 (0.6 mg/kg)",
            "B": "The dose producing 95% neuromuscular block used as the standard intubating dose without modification",
            "C": "The maximum safe dose of any NMB agent",
            "D": "The dose at which 95% of patients are fully paralysed within 60 seconds",
            "E": "The dose equivalent to 1 mg/kg suxamethonium",
        },
        "answer": "A",
        "explanation": "ED95 = dose producing 95% suppression of twitch at the adductor pollicis under nitrous oxide/opioid anaesthesia. Rocuronium ED95 \u2248 0.3 mg/kg. Standard intubating dose = 2\u00d7 ED95 = 0.6 mg/kg (onset ~90s, duration ~30\u201345 min, reversible with sugammadex). RSI dose = 1.2 mg/kg rocuronium (onset ~60s, equivalent to suxamethonium for RSI when sugammadex available immediately). Vecuronium ED95 \u2248 0.05 mg/kg; intubating dose 0.1 mg/kg. Higher doses \u2192 faster onset but longer duration.",
    },
    {
        "id": "ph_nmb007", "topic": "Pharmacology",
        "question": "Which condition is an absolute contraindication to the use of suxamethonium?",
        "options": {
            "A": "Hiatus hernia",
            "B": "History of malignant hyperthermia in a first-degree relative",
            "C": "Age under 1 year",
            "D": "Recent (7-day-old) full thickness burn injury covering 30% BSA",
            "E": "Mildly elevated serum potassium of 5.2 mmol/L",
        },
        "answer": "B",
        "explanation": "Absolute contraindications to suxamethonium: personal or family history of malignant hyperthermia; known or suspected myopathies (Duchenne, Becker \u2014 risk of life-threatening hyperkalaemia and rhabdomyolysis); previous suxamethonium-related complications. Relative contraindications (hyperkalaemia risk): burns (>48h post-injury up to 2 years), denervation injuries, prolonged immobilisation, upper motor neurone lesions, crush injuries. A 7-day burn = in the vulnerable period (extrajunctional AChR upregulation peaking at days 4\u20137 and persisting up to 18 months). MH is the only absolute contraindication listed; suxamethonium is the strongest trigger (with volatiles).",
    },
    {
        "id": "ph_nmb008", "topic": "Pharmacology",
        "question": "What is the mechanism by which phase II block differs from phase I block with suxamethonium?",
        "options": {
            "A": "Phase II occurs with inadequate reversal by neostigmine",
            "B": "Phase I = persistent depolarisation blocking Na\u207a channels; Phase II = receptor desensitisation resembling non-depolarising block with TOF fade",
            "C": "Phase II occurs only with atypical pseudocholinesterase",
            "D": "Phase I block shows TOF fade; Phase II shows no fade",
            "E": "Phase II is caused by accumulation of succinic acid metabolites",
        },
        "answer": "B",
        "explanation": "Phase I (depolarising) block: suxamethonium occupies and persistently activates AChR \u2192 sustained depolarisation \u2192 surrounding Na\u207a channels inactivated; TOF shows no fade; not reversed by neostigmine. Phase II (desensitisation) block: develops with repeated/prolonged dosing \u2192 receptors desensitise (return to resting conformation but unresponsive) \u2192 resembles non-depolarising block: TOF fade present, post-tetanic facilitation, potentially reversed by neostigmine (though response unpredictable). Clinically relevant threshold: >3\u20134 mg/kg total suxamethonium or infusion >30 min.",
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
def generate_question(topic: str, used_ids: list, recent_themes: list = None, subtopic: str = None) -> dict | None:
    """Generate a novel MCQ using Claude, with optional inline SVG diagram."""
    client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    subtopic_line = f"Target subtopic: {subtopic}" if subtopic else ""
    avoid_block = ""
    if recent_themes:
        avoid_block = "AVOID these recently used themes (do not write a question on the same concept):\n" + "\n".join(f"- {t}" for t in recent_themes[-12:])

    prompt = f"""Generate a single, high-quality Primary FRCA standard SBA (single best answer) MCQ on the topic: {topic}.
{subtopic_line}
{avoid_block}

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
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []  # per-question chat history
if "chat_q_id" not in st.session_state:
    st.session_state.chat_q_id = None  # which question the chat is about
if "quiz_review_idx" not in st.session_state:
    st.session_state.quiz_review_idx = None  # None = not in review mode; int = reviewing result at that index
if "mid_session_review" not in st.session_state:
    st.session_state.mid_session_review = False
if "confidence_rating" not in st.session_state:
    st.session_state.confidence_rating = None  # 1=unsure, 2=think so, 3=certain

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

# ── Session Resume Supabase ───────────────────────────────────────────────────
def save_session_state(session: dict):
    """Persist quiz session for resume. Strips SVG data to keep payload small."""
    try:
        import copy as _copy
        slim = _copy.deepcopy(session)
        for q in slim.get("queue", []):
            q.pop("svg", None); q.pop("svg_caption", None)
        for r in slim.get("results", []):
            r.pop("svg", None); r.pop("svg_caption", None)
        sb = get_supabase()
        payload = {
            "id": 1,
            "session": json.dumps(slim),
            "saved_at": datetime.now().isoformat(),
        }
        sb.table("session_resume").upsert(payload).execute()
        return True
    except Exception as e:
        print(f"[session_resume] save failed: {e}")
        return False

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


# ── Flagged questions Supabase ────────────────────────────────────────────────
def load_flags() -> list:
    try:
        sb = get_supabase()
        r = sb.table("mcq_stats").select("data").eq("id", 1).execute()
        if r.data and r.data[0]["data"]:
            d = r.data[0]["data"]
            data = d if isinstance(d, dict) else json.loads(d)
            return data.get("flagged_ids", [])
    except Exception:
        pass
    return []


def save_flag(q_id: str, stats: dict):
    flagged = stats.setdefault("flagged_ids", [])
    if q_id not in flagged:
        flagged.append(q_id)
        save_stats(stats)


def remove_flag(q_id: str, stats: dict):
    flagged = stats.setdefault("flagged_ids", [])
    if q_id in flagged:
        flagged.remove(q_id)
        save_stats(stats)



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

    # Question count presets
    st.markdown("""
    <p style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--muted);
              text-transform:uppercase;letter-spacing:0.06em;margin:14px 0 8px;">Questions</p>
    """, unsafe_allow_html=True)
    preset_cols = st.columns(4)
    preset_counts = [5, 10, 20, 30]
    if "cfg_n" not in st.session_state:
        st.session_state.cfg_n = 10
    for i, (pc, pv) in enumerate(zip(preset_cols, preset_counts)):
        with pc:
            active = st.session_state.cfg_n == pv
            label = f"**{pv}**" if active else str(pv)
            if st.button(label, key=f"preset_{pv}", use_container_width=True):
                st.session_state.cfg_n = pv
                st.rerun()
    n_questions = st.session_state.cfg_n

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Weak spots quick-start ─────────────────────────────────────────────────
    topic_pcts_home = {
        t: int(v["correct"] / v["total"] * 100)
        for t, v in stats["topic_totals"].items()
        if v["total"] >= 3
    }
    if len(topic_pcts_home) >= 2:
        weakest_topics = sorted(topic_pcts_home, key=topic_pcts_home.get)[:2]
        w1, w2 = weakest_topics
        w1_pct = topic_pcts_home[w1]
        w2_pct = topic_pcts_home[w2]
        w_colour = "#f87171"
        st.markdown(f"""
        <div style="background:#1c0a0a;border:1px solid #7f1d1d;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;display:flex;
                    align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
            <div>
                <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:{w_colour};
                          text-transform:uppercase;letter-spacing:0.08em;margin:0 0 4px;">Weak spots drill</p>
                <p style="font-size:13px;color:#e8edf5;margin:0;">
                    {w1.split(" &")[0]} <span style="color:{w_colour};">{w1_pct}%</span>
                    &nbsp;·&nbsp;
                    {w2.split(" &")[0]} <span style="color:{w_colour};">{w2_pct}%</span>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        ws_c1, ws_c2 = st.columns(2)
        with ws_c1:
            if st.button(f"Drill {w1.split(' &')[0]} →", use_container_width=True, key="ws_drill1"):
                st.session_state.cfg_topic_override = w1
                st.session_state._start_session_now = True
                st.rerun()
        with ws_c2:
            if st.button(f"Drill {w2.split(' &')[0]} →", use_container_width=True, key="ws_drill2"):
                st.session_state.cfg_topic_override = w2
                st.session_state._start_session_now = True
                st.rerun()

    # ── Flagged questions drill ────────────────────────────────────────────────
    flagged_ids = stats.get("flagged_ids", [])
    if flagged_ids:
        st.markdown(f"""
        <div style="background:#161b27;border:1px solid #2e3a52;border-left:3px solid #fbbf24;
                    border-radius:6px;padding:14px 18px;margin-bottom:16px;
                    display:flex;align-items:center;justify-content:space-between;">
            <div>
                <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#fbbf24;
                          text-transform:uppercase;letter-spacing:0.08em;margin:0 0 2px;">Flagged for review</p>
                <p style="font-size:13px;color:#e8edf5;margin:0;">{len(flagged_ids)} question{"s" if len(flagged_ids)!=1 else ""} saved</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Drill Flagged Questions →", use_container_width=True, key="drill_flagged"):
            st.session_state._drill_flagged = True
            st.rerun()

    if st.button("Start Session →", use_container_width=True):
        st.session_state._start_session_now = True
        st.rerun()

    # ── Handle session start (normal or weak-spots override or flagged) ────────
    if st.session_state.get("_drill_flagged"):
        st.session_state._drill_flagged = False
        flagged_bank = [q for q in FIXED_BANK if q["id"] in flagged_ids]
        if flagged_bank:
            import copy as _cp2
            flagged_bank_shuffled = _cp2.deepcopy(flagged_bank)
            random.shuffle(flagged_bank_shuffled)
            st.session_state.session = {
                "topic_filter": None,
                "use_ai": False,
                "ai_needed": 0,
                "timed": False,
                "queue": flagged_bank_shuffled,
                "idx": 0,
                "results": [],
                "n_target": len(flagged_bank_shuffled),
                "shown_ids": [q["id"] for q in flagged_bank_shuffled],
            }
            st.session_state.current_q = None
            st.session_state.selected_answer = None
            st.session_state.submitted = False
            st.session_state.quiz_review_idx = None
            st.session_state.mid_session_review = False
            st.session_state.confidence_rating = None
            nav("quiz")
            st.rerun()

    if st.session_state.get("_start_session_now"):
        st.session_state._start_session_now = False
        topic_override = st.session_state.pop("cfg_topic_override", None)
        # Build question queue
        topic_filter = topic_override or (None if topic_choice == "All Topics" else topic_choice)

        # Split bank into unseen-first, then seen — avoids repeats across sessions
        answered_ids = st.session_state.stats.get("answered_ids", [])
        full_bank = [q for q in FIXED_BANK if (not topic_filter or q["topic"] == topic_filter)]
        unseen = [q for q in full_bank if q["id"] not in answered_ids]
        seen   = [q for q in full_bank if q["id"] in answered_ids]

        def interleave_topics(pool):
            """Shuffle within each subtopic bucket then round-robin so consecutive questions differ."""
            from collections import defaultdict
            by_sub = defaultdict(list)
            for q in pool:
                sub_key = Q_SUBTOPICS.get(q.get("id", ""), (None, q["topic"]))[1]
                by_sub[sub_key].append(q)
            for s in by_sub:
                random.shuffle(by_sub[s])
            result = []
            sub_queues = list(by_sub.values())
            random.shuffle(sub_queues)
            while any(sub_queues):
                sub_queues = [sq for sq in sub_queues if sq]
                for sq in list(sub_queues):
                    if sq:
                        result.append(sq.pop(0))
            return result

        bank = interleave_topics(unseen) + interleave_topics(seen)

        def shuffle_answers(q):
            import copy
            q = copy.deepcopy(q)
            keys = list("ABCDE")
            correct_text = q["options"][q["answer"]]
            vals = list(q["options"].values())
            random.shuffle(vals)
            q["options"] = dict(zip(keys, vals))
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
        st.session_state.confidence_rating = None
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
            (f'<div style="margin-bottom:14px;">{Q_IMAGES[r["id"]]}</div>' if r.get('id','') in Q_IMAGES
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

        st.markdown("")
        # Retry wrong answers
        wrong_qs = [r for r in results if not r["correct"]]
        if wrong_qs:
            if st.button(f"Retry {len(wrong_qs)} Wrong Answer{'s' if len(wrong_qs)!=1 else ''} →",
                         use_container_width=True, key="retry_wrong"):
                import copy as _cp3
                retry_bank = []
                for r in wrong_qs:
                    q_obj = next((q for q in FIXED_BANK if q.get("id") == r.get("id")), None)
                    if q_obj:
                        retry_bank.append(_cp3.deepcopy(q_obj))
                    else:
                        # Reconstruct from result entry for AI questions
                        retry_bank.append({
                            "id": r.get("id", ""), "topic": r["topic"],
                            "question": r["question"], "options": r["options"],
                            "answer": r["answer"], "explanation": r["explanation"],
                        })
                random.shuffle(retry_bank)
                st.session_state.session = {
                    "topic_filter": None, "use_ai": False, "ai_needed": 0, "timed": False,
                    "queue": retry_bank, "idx": 0, "results": [],
                    "n_target": len(retry_bank), "shown_ids": [q["id"] for q in retry_bank],
                }
                st.session_state.current_q = None
                st.session_state.selected_answer = None
                st.session_state.submitted = False
                st.session_state.quiz_review_idx = None
                st.session_state.confidence_rating = None
                nav("quiz")
                st.rerun()

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
                # Generate AI question — pick underrepresented subtopic
                with st.spinner("Generating question…"):
                    topic = session["topic_filter"] or random.choice(list(TOPICS.keys()))
                    # Build recent_themes from last 12 results to avoid repetition
                    recent_themes = [r.get("question","")[:60] for r in session.get("results",[])[-12:]]
                    # Pick a subtopic for this topic that hasn't been covered recently
                    topic_subs = [name for _, name in TOPIC_DECK_SUGGESTIONS.get(topic, [])]
                    used_subs = [Q_SUBTOPICS.get(r.get("id",""), (None, None))[1]
                                 for r in session.get("results", [])]
                    fresh_subs = [s for s in topic_subs if s not in used_subs]
                    target_sub = random.choice(fresh_subs) if fresh_subs else (
                        random.choice(topic_subs) if topic_subs else None)
                    q = generate_question(topic, shown_ids,
                                          recent_themes=recent_themes, subtopic=target_sub)
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
                + (f'<div style="margin-bottom:14px;">{Q_IMAGES[r["id"]]}</div>' if r.get('id','') in Q_IMAGES
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

            # Confidence rating
            st.markdown("""
            <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;
                      text-transform:uppercase;letter-spacing:0.06em;margin:0 0 8px;">Confidence</p>
            """, unsafe_allow_html=True)
            conf_cols = st.columns(3)
            conf_labels = {1: "🤔  Not sure", 2: "🙂  Think so", 3: "✓  Certain"}
            conf_colours = {1: "#f87171", 2: "#fbbf24", 3: "#4ade80"}
            for ci, (cv, cl) in enumerate(conf_labels.items()):
                with conf_cols[ci]:
                    is_sel = st.session_state.confidence_rating == cv
                    if st.button(cl, key=f"conf_{done}_{cv}", use_container_width=True):
                        st.session_state.confidence_rating = cv
                        st.rerun()

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
                # Flag for review button
                _q_id_flag = q.get("id", "")
                _is_flagged = _q_id_flag in st.session_state.stats.get("flagged_ids", [])
                flag_label = "🚩 Flagged" if _is_flagged else "🚩 Flag"
                if st.button(flag_label, key=f"flag_{q_id}", use_container_width=True):
                    if _is_flagged:
                        remove_flag(_q_id_flag, st.session_state.stats)
                        st.toast("Removed from flagged questions")
                    else:
                        save_flag(_q_id_flag, st.session_state.stats)
                        st.toast("Flagged for review!")
                    st.rerun()

            st.markdown("")

            # ── Navigation ─────────────────────────────────────────────────
            nav_c1, nav_c2 = st.columns([3, 1])
            with nav_c1:
                if st.button("Next Question →", use_container_width=True):
            