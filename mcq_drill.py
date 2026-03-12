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

html, body, [class*="css"] {
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
    st.session_state.sidebar_visible = True

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
toggle_label = "☰" if not st.session_state.sidebar_visible else "✕  Menu"
st.markdown(
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">',
    unsafe_allow_html=True
)
if st.button(toggle_label, key="sidebar_toggle"):
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ── Topic colours ─────────────────────────────────────────────────────────────
TOPICS = {
    "Physiology":                   {"colour": "#2dd4bf", "emoji": ""},
    "Pharmacology":                 {"colour": "#a78bfa", "emoji": ""},
    "Physics & Clinical Measurement": {"colour": "#38bdf8", "emoji": ""},
    "Clinical Anaesthesia":         {"colour": "#fb923c", "emoji": ""},
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
    """Generate a novel MCQ using Claude."""
    client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    prompt = f"""Generate a single, high-quality Primary FRCA standard SBA (single best answer) MCQ on the topic: {topic}.

Requirements:
- Five options labelled A–E
- Only ONE correct answer
- Plausible distractors based on common exam misconceptions
- A clear, detailed explanation of why the answer is correct and why distractors are wrong
- Difficulty level: appropriate for Primary FRCA written paper

Respond ONLY with a JSON object in this exact format (no markdown, no preamble):
{{
  "id": "ai_{uuid}",
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
  "explanation": "..."
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        q = json.loads(text)
        q["id"] = f"ai_{uuid.uuid4().hex[:8]}"
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
            return d if isinstance(d, dict) else json.loads(d)
    except Exception:
        pass
    return {"decks": [{"id": "default", "name": "FRCA Revision", "colour": "#4f9cf9", "cards": []}]}

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
    st.markdown("""
    <div style="padding:24px 16px 20px;border-bottom:1px solid #252e42;margin-bottom:8px;">
        <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#6b7a99;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 6px;">Primary FRCA</p>
        <h2 style="font-family:Fraunces,serif;color:#e8edf5;font-size:24px;font-weight:300;margin:0;letter-spacing:-0.02em;">MCQ Drill</h2>
    </div>
    """, unsafe_allow_html=True)

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

        bank = [q for q in FIXED_BANK if (not topic_filter or q["topic"] == topic_filter)]
        random.shuffle(bank)

        use_fixed = mode_choice != "AI-generated only"
        use_ai    = mode_choice != "Fixed bank only"

        if use_fixed:
            fixed_qs = bank[:n_questions]
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

        # Per-question review
        st.markdown("#### Answer Review")
        for i, r in enumerate(session["results"]):
            icon = "✅" if r["correct"] else "❌"
            with st.expander(f"{icon}  Q{i+1} · {r['topic']} · Your answer: {r['selected']} · Correct: {r['answer']}"):
                st.markdown(f"**{r['question']}**")
                for opt, text in r["options"].items():
                    colour = "#34d399" if opt == r["answer"] else ("#f87171" if opt == r["selected"] and not r["correct"] else "#6b7280")
                    prefix = "✓ " if opt == r["answer"] else ("✗ " if opt == r["selected"] and not r["correct"] else "  ")
                    st.markdown(f'<p style="color:{colour};margin:4px 0;">{prefix}<strong>{opt}.</strong> {text}</p>', unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background:#1a1e28;border-left:3px solid #06b6d4;padding:12px 16px;
                            border-radius:0 8px 8px 0;margin-top:12px;font-size:14px;line-height:1.6;">
                    {r['explanation']}
                </div>
                """, unsafe_allow_html=True)

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

        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">'
            '<div>'
            '<p style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#6b7a99;'
            'margin:0 0 5px;text-transform:uppercase;letter-spacing:0.06em;">'
            'Question ' + str(done+1) + ' of ' + str(total_target) + '</p>'
            '<div style="display:flex;align-items:center;gap:8px;">'
            '<div style="width:3px;height:16px;background:' + colour + ';border-radius:2px;"></div>'
            '<span style="font-family:IBM Plex Mono,monospace;font-size:12px;color:' + colour + ';">' + q["topic"] + '</span>'
            '</div>'
            '</div>'
            + timer_block +
            '</div>'
            '<div style="background:#252e42;border-radius:2px;height:3px;margin-bottom:24px;">'
            '<div style="width:' + str(progress_pct) + '%;height:3px;background:' + colour + ';border-radius:2px;"></div>'
            '</div>',
            unsafe_allow_html=True
        )

        # Question box
        st.markdown(
            '<div style="background:#161b27;border:1px solid #252e42;border-radius:12px;'
            'padding:28px 32px;margin-bottom:24px;border-top:3px solid ' + colour + ';">'
            '<p style="font-family:IBM Plex Sans,sans-serif;font-size:18px;font-weight:400;'
            'line-height:1.7;margin:0;color:#e8edf5;">' + q["question"] + '</p>'
            '</div>',
            unsafe_allow_html=True
        )

        if not st.session_state.submitted:
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

            # ── Save as flashcard ───────────────────────────────────────────
            with chat_col2:
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

                st.markdown("""
                <div style="background:#161b27;border:1px solid #252e42;border-radius:8px;
                            padding:20px 24px;margin:12px 0;">
                    <p style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#4f9cf9;
                              text-transform:uppercase;letter-spacing:0.08em;margin:0 0 14px;">
                        New Flashcard
                    </p>
                """, unsafe_allow_html=True)

                # Deck selector
                if decks:
                    deck_names = [d["name"] for d in decks]
                    chosen_deck_name = st.selectbox(
                        "Deck", deck_names,
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
                }
                session["results"].append(result_entry)
                session["idx"] += 1
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
        decks = [{"id": "default", "name": "FRCA Revision", "colour": "#4f9cf9", "cards": []}]
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
