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
from datetime import datetime
from anthropic import Anthropic

st.set_page_config(
    page_title="FRCA MCQ Drill",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500;600&display=swap');

:root {
    --bg: #0d0f14; --surface: #13161e; --surface2: #1a1e28;
    --border: #252a38; --accent: #06b6d4; --text: #e8eaf0;
    --muted: #6b7280; --green: #34d399; --yellow: #fbbf24;
    --red: #f87171; --orange: #fb923c; --indigo: #818cf8;
}
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}
[data-testid="stSidebar"] {
    background: #13161e !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
.stButton > button {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
    background: var(--surface2) !important;
    color: var(--text) !important;
    transition: all 0.15s !important;
}
.stButton > button:hover { border-color: var(--accent) !important; color: var(--accent) !important; }
.stRadio label { color: var(--text) !important; font-size: 15px !important; }
.stRadio > div { gap: 8px !important; }
[data-testid="metric-container"] {
    background: #13161e !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}
[data-testid="metric-container"] label {
    color: var(--muted) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Instrument Serif', serif !important;
    font-size: 32px !important;
    color: var(--accent) !important;
}
.stProgress > div > div {
    background: linear-gradient(90deg, #06b6d4, #818cf8) !important;
    border-radius: 2px !important;
}
.stProgress > div { background: var(--border) !important; border-radius: 2px !important; height: 5px !important; }
.stSelectbox > div > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}
[data-testid="stDataFrame"] { background: var(--surface) !important; }
#MainMenu, footer, header { visibility: hidden; }
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ── Topic colours ─────────────────────────────────────────────────────────────
TOPICS = {
    "Physiology":                   {"colour": "#06b6d4", "emoji": "🫀"},
    "Pharmacology":                 {"colour": "#818cf8", "emoji": "💊"},
    "Physics & Clinical Measurement": {"colour": "#34d399", "emoji": "⚗️"},
    "Clinical Anaesthesia":         {"colour": "#fbbf24", "emoji": "🩺"},
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
    st.session_state.textbook_docs = None  # loaded lazily

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


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding-bottom:20px;border-bottom:1px solid #252a38;margin-bottom:16px;">
        <h2 style="font-family:'Instrument Serif',serif;color:#06b6d4;font-size:26px;margin:0;">FRCA Drill</h2>
        <p style="font-family:'DM Mono',monospace;font-size:11px;color:#6b7280;margin:4px 0 0;">Primary MCQ Practice</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🏠  Home", use_container_width=True):
        nav("home")
    if st.button("📊  Performance", use_container_width=True):
        nav("stats")
    if st.button("📖  Textbook", use_container_width=True):
        nav("textbook")

    # Quick topic stats in sidebar
    st.markdown("""
    <p style="font-family:'DM Mono',monospace;font-size:10px;color:#6b7280;
              text-transform:uppercase;letter-spacing:1px;margin:20px 0 10px;">Topic Scores</p>
    """, unsafe_allow_html=True)

    for topic, meta in TOPICS.items():
        t = stats["topic_totals"].get(topic, {"correct": 0, "total": 0})
        pct = int(t["correct"] / t["total"] * 100) if t["total"] else 0
        bar_colour = meta["colour"]
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;">
                <span style="color:#e8eaf0;">{meta['emoji']} {topic.split(' &')[0].split(' ')[0]}</span>
                <span style="font-family:'DM Mono',monospace;color:{bar_colour};">{pct}%</span>
            </div>
            <div style="background:#252a38;border-radius:2px;height:4px;">
                <div style="width:{pct}%;height:4px;background:{bar_colour};border-radius:2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: HOME
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.page == "home":
    st.markdown("""
    <h2 style="font-family:'Instrument Serif',serif;font-size:36px;font-weight:400;
               letter-spacing:-0.5px;margin-bottom:6px;">Primary FRCA MCQ Drill</h2>
    <p style="color:#6b7280;font-size:15px;margin-bottom:36px;">
        Timed SBA practice · Fixed bank + AI-generated questions · Per-topic tracking
    </p>
    """, unsafe_allow_html=True)

    # Config columns
    col1, col2, col3 = st.columns(3)
    with col1:
        topic_choice = st.selectbox(
            "TOPIC", ["All Topics"] + list(TOPICS.keys()), key="cfg_topic"
        )
    with col2:
        mode_choice = st.selectbox(
            "QUESTION SOURCE",
            ["Mixed (Fixed + AI)", "Fixed bank only", "AI-generated only"],
            key="cfg_mode",
        )
    with col3:
        timing_choice = st.selectbox(
            "TIMING",
            ["Timed — 90s per question", "Untimed"],
            key="cfg_timing",
        )

    n_questions = st.slider("Number of questions", 5, 30, 10, key="cfg_n")
    st.markdown("")

    if st.button("▶  Start Session", use_container_width=True):
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
            "timed": timing_choice.startswith("Timed"),
            "queue": fixed_qs,
            "idx": 0,
            "results": [],
            "n_target": n_questions,
        }
        st.session_state.current_q = None
        st.session_state.selected_answer = None
        st.session_state.submitted = False
        nav("quiz")
        st.rerun()

    # Recent performance summary
    if stats["sessions"]:
        st.markdown("---")
        st.markdown("#### Recent Sessions")
        recent = stats["sessions"][-5:][::-1]
        import pandas as pd
        rows = []
        for s in recent:
            rows.append({
                "Date": datetime.fromisoformat(s["ts"]).strftime("%d %b %H:%M"),
                "Topic": s.get("topic", "All"),
                "Score": f"{s['correct']}/{s['total']}",
                "Pct": f"{int(s['correct']/s['total']*100)}%" if s['total'] else "—",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


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

        st.markdown(f"""
        <div style="text-align:center;padding:40px 0 20px;">
            <h2 style="font-family:'Instrument Serif',serif;font-size:42px;margin-bottom:8px;">
                {correct}/{done}
            </h2>
            <p style="font-size:20px;color:{'#34d399' if pct >= 60 else '#f87171'};">
                {'✅ Pass territory' if pct >= 60 else '❌ Below pass mark'} — {pct}%
            </p>
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
            if st.button("🏠 Home", use_container_width=True):
                nav("home")
                st.rerun()
        with c2:
            if st.button("📊 View Stats", use_container_width=True):
                nav("stats")
                st.rerun()

    else:
        # Load next question
        if st.session_state.current_q is None:
            queue = session["queue"]
            if idx < len(queue):
                st.session_state.current_q = queue[idx]
                st.session_state.selected_answer = None
                st.session_state.submitted = False
                st.session_state.start_time = time.time()
            elif session["use_ai"] and session["ai_needed"] > 0:
                # Generate AI question
                with st.spinner("🤖 Generating question…"):
                    topic = session["topic_filter"] or random.choice(list(TOPICS.keys()))
                    q = generate_question(topic, [])
                    if q:
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
                # Pad with more fixed questions if needed
                st.session_state.current_q = random.choice(FIXED_BANK)
                st.session_state.selected_answer = None
                st.session_state.submitted = False
                st.session_state.start_time = time.time()

        q = st.session_state.current_q
        if not q:
            st.rerun()

        # Header
        progress = done / total_target
        st.progress(progress)
        col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
        with col_h1:
            st.markdown(f'<p style="font-family:\'DM Mono\',monospace;font-size:12px;color:#6b7280;">Q{done+1} of {total_target}</p>', unsafe_allow_html=True)
        with col_h2:
            colour = TOPICS.get(q["topic"], {}).get("colour", "#06b6d4")
            emoji  = TOPICS.get(q["topic"], {}).get("emoji", "")
            st.markdown(f'<span style="color:{colour};font-size:12px;font-family:\'DM Mono\',monospace;">{emoji} {q["topic"]}</span>', unsafe_allow_html=True)
        with col_h3:
            if session["timed"] and not st.session_state.submitted:
                elapsed = time.time() - (st.session_state.start_time or time.time())
                remaining = max(0, 90 - elapsed)
                time_colour = "#f87171" if remaining < 20 else "#fbbf24" if remaining < 45 else "#34d399"
                st.markdown(f'<p style="font-family:\'DM Mono\',monospace;font-size:14px;color:{time_colour};text-align:right;">⏱ {int(remaining)}s</p>', unsafe_allow_html=True)

        # Question box
        st.markdown(f"""
        <div style="background:#13161e;border:1px solid #252a38;border-radius:14px;
                    padding:28px 32px;margin:16px 0 20px;border-left:4px solid {colour};">
            <p style="font-size:18px;font-family:'Outfit',sans-serif;font-weight:500;
                      line-height:1.6;margin:0;">{q['question']}</p>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.submitted:
            selected = st.radio(
                "Select your answer:",
                options=list(q["options"].keys()),
                format_func=lambda k: f"{k}.  {q['options'][k]}",
                key=f"radio_{done}",
                label_visibility="collapsed",
            )
            st.markdown("")
            if st.button("Submit Answer →", use_container_width=True):
                # Auto-submit on timer expiry too
                timed_out = (
                    session["timed"]
                    and (time.time() - (st.session_state.start_time or time.time())) >= 90
                )
                st.session_state.selected_answer = selected
                st.session_state.submitted = True
                st.rerun()

            # Auto-submit on timer
            if session["timed"] and st.session_state.start_time:
                elapsed = time.time() - st.session_state.start_time
                if elapsed >= 90 and not st.session_state.submitted:
                    st.session_state.selected_answer = list(q["options"].keys())[0]
                    st.session_state.submitted = True
                    st.rerun()

        else:
            # Show result
            sel = st.session_state.selected_answer
            correct = sel == q["answer"]

            for opt, text in q["options"].items():
                if opt == q["answer"]:
                    bg, border, col = "#0f2a1e", "#34d399", "#34d399"
                elif opt == sel and not correct:
                    bg, border, col = "#2a0f0f", "#f87171", "#f87171"
                else:
                    bg, border, col = "#1a1e28", "#252a38", "#6b7280"
                prefix = "✓ " if opt == q["answer"] else ("✗ " if opt == sel and not correct else "   ")
                st.markdown(f"""
                <div style="background:{bg};border:1px solid {border};border-radius:8px;
                            padding:12px 16px;margin:6px 0;color:{col};font-size:15px;">
                    <strong>{prefix}{opt}.</strong> {text}
                </div>
                """, unsafe_allow_html=True)

            # Explanation
            st.markdown(f"""
            <div style="background:#1a1e28;border-left:3px solid #06b6d4;padding:16px 20px;
                        border-radius:0 10px 10px 0;margin:16px 0;font-size:14px;line-height:1.7;">
                <p style="font-family:'DM Mono',monospace;font-size:10px;color:#6b7280;
                          text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Explanation</p>
                {q['explanation']}
            </div>
            """, unsafe_allow_html=True)

            if st.button("Next Question →", use_container_width=True):
                # Record result
                session["results"].append({
                    "question": q["question"],
                    "options": q["options"],
                    "answer": q["answer"],
                    "selected": sel,
                    "correct": correct,
                    "topic": q["topic"],
                    "explanation": q["explanation"],
                })
                session["idx"] += 1
                st.session_state.current_q = None
                st.session_state.selected_answer = None
                st.session_state.submitted = False
                st.session_state.start_time = None
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: STATS
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.page == "stats":
    st.markdown("""
    <h2 style="font-family:'Instrument Serif',serif;font-size:32px;font-weight:400;
               letter-spacing:-0.5px;margin-bottom:6px;">Performance</h2>
    <p style="color:#6b7280;font-size:14px;margin-bottom:28px;">Your MCQ history and topic breakdown.</p>
    """, unsafe_allow_html=True)

    total_q   = sum(v["total"] for v in stats["topic_totals"].values())
    total_c   = sum(v["correct"] for v in stats["topic_totals"].values())
    overall   = int(total_c / total_q * 100) if total_q else 0
    n_sessions = len(stats["sessions"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Questions Answered", total_q)
    c2.metric("Overall Score",      f"{overall}%")
    c3.metric("Sessions",           n_sessions)

    st.markdown("---")
    st.markdown("#### By Topic")

    for topic, meta in TOPICS.items():
        t = stats["topic_totals"].get(topic, {"correct": 0, "total": 0})
        pct = int(t["correct"] / t["total"] * 100) if t["total"] else 0
        c = meta["colour"]
        st.markdown(f"""
        <div style="background:#13161e;border:1px solid #252a38;border-radius:12px;
                    padding:16px 20px;margin-bottom:10px;border-left:4px solid {c};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="font-size:15px;font-weight:500;">{meta['emoji']} {topic}</span>
                <span style="font-family:'DM Mono',monospace;font-size:13px;color:{c};">
                    {t['correct']}/{t['total']} · {pct}%
                </span>
            </div>
            <div style="background:#252a38;border-radius:3px;height:6px;">
                <div style="width:{pct}%;height:6px;background:{c};border-radius:3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if stats["sessions"]:
        st.markdown("---")
        st.markdown("#### Session History")
        import pandas as pd
        rows = [
            {
                "Date":    datetime.fromisoformat(s["ts"]).strftime("%d %b %Y %H:%M"),
                "Topic":   s.get("topic", "All"),
                "Correct": s["correct"],
                "Total":   s["total"],
                "Score":   f"{int(s['correct']/s['total']*100)}%" if s["total"] else "—",
            }
            for s in reversed(stats["sessions"])
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

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
    <h2 style="font-family:\'Instrument Serif\',serif;font-size:32px;font-weight:400;
               letter-spacing:-0.5px;margin-bottom:6px;">Textbook Library</h2>
    <p style="color:#6b7280;font-size:14px;margin-bottom:28px;">
        Upload your revision PDFs and read them here. Stored securely in your database.
    </p>
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
            # ── PDF Viewer ────────────────────────────────────────────────────
            col_back, col_title = st.columns([1, 5])
            with col_back:
                if st.button("← Back", key="tb_back"):
                    st.session_state.open_doc_id = None
                    st.rerun()
            with col_title:
                topic_colour = TOPICS.get(open_doc.get("topic", ""), {}).get("colour", "#06b6d4")
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:12px;">
                    <h3 style="font-family:\'Instrument Serif\',serif;font-size:24px;font-weight:400;margin:0;">
                        {open_doc["name"]}
                    </h3>
                    <span style="background:rgba(6,182,212,0.1);color:{topic_colour};
                                 border:1px solid {topic_colour}44;border-radius:20px;
                                 padding:2px 10px;font-size:11px;font-family:\'DM Mono\',monospace;">
                        {open_doc.get("topic","Other")}
                    </span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("")

            # Render PDF inline
            b64 = open_doc["data"]
            pdf_display = f"""
            <div style="border:1px solid #252a38;border-radius:12px;overflow:hidden;background:#13161e;">
                <iframe
                    src="data:application/pdf;base64,{b64}"
                    width="100%"
                    height="900px"
                    style="border:none;display:block;"
                    type="application/pdf"
                ></iframe>
            </div>
            <p style="font-size:11px;color:#6b7280;margin-top:8px;font-family:\'DM Mono\',monospace;">
                If the PDF doesn\'t display, try a different browser. Works best on Chrome/Edge desktop.
                On mobile, use the download button below.
            </p>
            """
            st.markdown(pdf_display, unsafe_allow_html=True)

            # Download button as fallback
            st.markdown("")
            st.download_button(
                label="⬇ Download PDF",
                data=base64.b64decode(b64),
                file_name=f"{open_doc['name'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                key="tb_download"
            )

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
                <div style="display:flex;align-items:center;gap:10px;margin:24px 0 12px;">
                    <div style="width:3px;height:24px;background:{colour};border-radius:2px;"></div>
                    <h3 style="font-size:16px;font-weight:500;margin:0;">{emoji} {topic}</h3>
                    <span style="font-family:\'DM Mono\',monospace;font-size:11px;color:#6b7280;">
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
                        <div style="background:#13161e;border:1px solid #252a38;border-radius:10px;
                                    padding:14px 18px;border-left:3px solid {colour};">
                            <p style="font-size:15px;font-weight:500;margin:0 0 4px;">{doc["name"]}</p>
                            <p style="font-family:\'DM Mono\',monospace;font-size:11px;color:#6b7280;margin:0;">
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
