import base64
import json
import re
import sys
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# Ensure repo root is on sys.path so `src` imports work when running via Streamlit.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.pipeline import run_pipeline
from src.llm.client import LLMClient, LLMClientError
from src.utils.config import get_config
from app.sample_notes import SAMPLE_NOTES
from src.utils.logging import get_logger
from src.export.fhir_bundle import build_fhir_bundle
from src.privacy.patterns import PHONE_RE, EMAIL_RE, AADHAAR_RE, MRN_RE
from src.validate.normalizers import normalize_structured
from src.validate.validators import run_validations

load_dotenv()
logger = get_logger()
cfg = get_config()

st.set_page_config(page_title="DocSathi", layout="wide", page_icon="🩺")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700;900&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --atlas-ivory: #f6f1e7;
  --atlas-ink: #152726;
  --atlas-teal: #0f6b67;
  --atlas-ochre: #c7882a;
  --atlas-card: #fffdf7;
  --atlas-muted: #4f605d;
  --atlas-border: #e2d7c4;
  --atlas-shadow: 0 18px 44px rgba(21, 39, 38, 0.08);
}

html, body, .stApp, [class*="css"] {
  font-family: 'Merriweather', serif;
  color: var(--atlas-ink) !important;
  background-color: var(--atlas-ivory) !important;
}

section[data-testid="stAppViewContainer"] {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.7), rgba(255,255,255,0)),
    radial-gradient(1100px 520px at 8% -15%, rgba(15,107,103,0.12), transparent 55%),
    radial-gradient(900px 520px at 92% -10%, rgba(199,136,42,0.12), transparent 55%),
    var(--atlas-ivory) !important;
}

div[data-testid="stAppViewBlockContainer"] {
  padding-top: 0 !important;
  margin-top: 0 !important;
}
.block-container {
  padding-top: 0 !important;
}

[data-testid="stSidebar"] {
  background: #f6efe4;
  border-right: 1px solid var(--atlas-border);
}

.hero {
  background: var(--atlas-card);
  border: 1px solid var(--atlas-border);
  border-radius: 18px;
  padding: 22px 28px;
  box-shadow: var(--atlas-shadow);
  margin-bottom: 18px;
}
.hero-title {
  font-size: 2.1rem;
  font-weight: 900;
  letter-spacing: 0.3px;
  color: var(--atlas-ink);
}
.hero-subtitle {
  color: var(--atlas-muted);
  margin-top: 6px;
  font-size: 1rem;
}
.hero-badges {
  margin-top: 14px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.badge {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--atlas-border);
  background: #f0f5f4;
  color: var(--atlas-teal);
  font-size: 0.85rem;
  font-weight: 700;
}
.badge-ochre {
  background: rgba(199, 136, 42, 0.12);
  color: var(--atlas-ochre);
}
.navbar {
  background: var(--atlas-card);
  border: 1px solid var(--atlas-border);
  border-radius: 20px;
  padding: 18px 22px;
  box-shadow: var(--atlas-shadow);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  margin-top: 12px;
  margin-bottom: 12px;
}
.navbar-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.navbar-logo {
  width: 62px;
  height: 62px;
  border-radius: 14px;
  border: 1px solid var(--atlas-border);
  background: #fff;
  object-fit: contain;
}
.navbar-logo-fallback {
  width: 62px;
  height: 62px;
  border-radius: 14px;
  border: 1px solid var(--atlas-border);
  background: rgba(15, 107, 103, 0.12);
  color: var(--atlas-teal);
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}
.navbar-title {
  font-size: 1.7rem;
  font-weight: 900;
  color: var(--atlas-ink);
}
.navbar-subtitle {
  font-size: 0.95rem;
  color: var(--atlas-muted);
}
.navbar-badges {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.card {
  background: var(--atlas-card);
  border: 1px solid var(--atlas-border);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: var(--atlas-shadow);
}
.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--atlas-border);
  font-size: 0.82rem;
  margin: 6px 6px 0 0;
}
.status-ok {
  background: rgba(15, 107, 103, 0.12);
  color: #0f6b67;
  border-color: rgba(15, 107, 103, 0.35);
}
.status-warn {
  background: rgba(199, 136, 42, 0.15);
  color: #7a4d12;
  border-color: rgba(199, 136, 42, 0.45);
}
.status-info {
  background: rgba(21, 39, 38, 0.08);
  color: var(--atlas-ink);
}
.navbar {
  animation: fadeUp 0.6s ease both;
}
.stepper {
  animation: fadeUp 0.7s ease both;
}
.card,
.highlight-card {
  animation: fadeUp 0.65s ease both;
}
.status-chip,
.flag-pill,
.chip {
  animation: fadeUp 0.5s ease both;
}
.status-chip:nth-child(1) { animation-delay: 0.05s; }
.status-chip:nth-child(2) { animation-delay: 0.10s; }
.status-chip:nth-child(3) { animation-delay: 0.15s; }
.status-chip:nth-child(4) { animation-delay: 0.20s; }
.chip:nth-child(1) { animation-delay: 0.05s; }
.chip:nth-child(2) { animation-delay: 0.10s; }
.chip:nth-child(3) { animation-delay: 0.15s; }
.chip:nth-child(4) { animation-delay: 0.20s; }
.chip:nth-child(5) { animation-delay: 0.25s; }
.chip:nth-child(6) { animation-delay: 0.30s; }
.chip:nth-child(7) { animation-delay: 0.35s; }
.chip:nth-child(8) { animation-delay: 0.40s; }
.chip:nth-child(9) { animation-delay: 0.45s; }
.chip:nth-child(10) { animation-delay: 0.50s; }
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.card-title {
  font-size: 0.95rem;
  color: var(--atlas-muted);
  margin-bottom: 6px;
}
.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
}
.section-title {
  font-size: 1.05rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--atlas-ink);
}
.muted {
  color: var(--atlas-muted);
  font-size: 0.9rem;
  margin-bottom: 8px;
}
.mono, code, pre {
  font-family: 'JetBrains Mono', monospace !important;
}
.stButton > button {
  background: linear-gradient(120deg, #0f6b67, #0b5a57);
  color: #fff;
  border: 1px solid rgba(15, 107, 103, 0.4);
  padding: 0.7rem 1.2rem;
  border-radius: 12px;
  font-weight: 700;
  transition: transform 0.15s ease, box-shadow 0.2s ease;
  box-shadow: 0 14px 26px rgba(15, 107, 103, 0.18);
}
.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 30px rgba(15, 107, 103, 0.25);
}
.stButton > button:disabled {
  background: #9fb8b6;
  box-shadow: none;
}
.stDownloadButton > button {
  background: #f5efe4 !important;
  color: var(--atlas-ink) !important;
  border: 1px solid var(--atlas-border) !important;
  box-shadow: none !important;
}
.stDownloadButton > button:hover {
  background: #efe6d6 !important;
  color: var(--atlas-ink) !important;
}
[data-testid="stFormSubmitButton"] > button {
  background: linear-gradient(120deg, #0f6b67, #0b5a57) !important;
  color: #fff !important;
  border: 1px solid rgba(15, 107, 103, 0.4) !important;
}
.stTextArea textarea {
  border-radius: 14px;
  border: 1px solid var(--atlas-border);
  background: #fffdf8;
  color: var(--atlas-ink);
  caret-color: var(--atlas-teal);
}
.stTextArea textarea::placeholder {
  color: #8a7f6a;
}
.stTextArea label, .stSelectbox label, .stTextInput label {
  color: var(--atlas-ink) !important;
}
[data-testid="stWidgetLabel"] > div > span,
[data-testid="stWidgetLabel"] > label,
[data-testid="stWidgetLabel"] span {
  color: var(--atlas-ink) !important;
  opacity: 1 !important;
}
.stSelectbox div[data-baseweb="select"] {
  border-radius: 12px;
  border: 1px solid var(--atlas-border);
  background: #fffdf8;
}
.stTabs [data-baseweb="tab"] {
  font-weight: 700;
  color: var(--atlas-ink) !important;
}
.stTabs [data-baseweb="tab"] * {
  color: var(--atlas-ink) !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary svg {
  color: var(--atlas-ink) !important;
}
[data-testid="stExpander"] {
  border-color: var(--atlas-border) !important;
}
.stSpinner > div > div,
.stSpinner div[role="status"],
.stSpinner svg {
  color: var(--atlas-ink) !important;
  fill: var(--atlas-ink) !important;
}
[data-testid="stToggle"] *,
.stToggle label,
.stToggle span,
.stToggle p {
  color: var(--atlas-ink) !important;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5 {
  color: var(--atlas-ink);
}
.stMarkdown, .stTextArea, .stSelectbox, .stTextInput, .stButton {
  color: var(--atlas-ink);
}
.stMarkdown p, .stMarkdown span, .stMarkdown div {
  color: var(--atlas-ink);
}
.stMarkdown small {
  color: var(--atlas-muted);
}
.stTextArea textarea {
  color: var(--atlas-ink);
  caret-color: var(--atlas-teal);
}
.stTextArea textarea::placeholder {
  color: #8a7f6a;
}
.stTextArea label, .stSelectbox label, .stTextInput label {
  color: var(--atlas-ink);
}
[data-testid="stDataFrame"] {
  background: #fffdf8 !important;
  border-radius: 12px !important;
  border: 1px solid var(--atlas-border) !important;
  padding: 6px !important;
}
[data-testid="stDataFrame"] [data-testid="stTable"] {
  color: var(--atlas-ink) !important;
  background: #fffdf8 !important;
}
[data-testid="stDataFrame"] * {
  color: var(--atlas-ink) !important;
}
[data-testid="stDataFrame"] .dataframe,
[data-testid="stDataFrame"] table,
[data-testid="stDataFrame"] thead,
[data-testid="stDataFrame"] tbody,
[data-testid="stDataFrame"] tr,
[data-testid="stDataFrame"] th,
[data-testid="stDataFrame"] td {
  background-color: #fffdf8 !important;
  color: var(--atlas-ink) !important;
}

/* Hide Streamlit chrome (Deploy button, menu, footer) */
header[data-testid="stHeader"],
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
#MainMenu,
footer {
  visibility: hidden;
  height: 0;
}
.divider {
  height: 1px;
  background: var(--atlas-border);
  margin: 12px 0 16px;
}
.stepper {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 10px;
  margin-bottom: 18px;
}
.step {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--atlas-border);
  font-size: 0.85rem;
  color: var(--atlas-muted);
  background: #f3f0e8;
}
.step-active {
  border-style: solid;
  color: var(--atlas-ink);
  background: #f3f0e8;
}
.flag-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid rgba(199, 136, 42, 0.4);
  background: rgba(199, 136, 42, 0.12);
  margin: 6px 6px 0 0;
  font-size: 0.9rem;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--atlas-border);
  background: #f6efe4;
  font-size: 0.82rem;
  margin: 6px 6px 0 0;
}
.chip-missing {
  border-color: rgba(199, 136, 42, 0.5);
  background: rgba(199, 136, 42, 0.12);
  color: #7a4d12;
}
.chip-present {
  border-color: rgba(15, 107, 103, 0.4);
  background: rgba(15, 107, 103, 0.12);
  color: #0f6b67;
}
.score-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.score-value {
  font-size: 2rem;
  font-weight: 900;
}
.progress-track {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: #ece4d6;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(120deg, #0f6b67, #0b5a57);
}
.inline-spinner {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--atlas-ink);
  margin-top: 6px;
}
.spinner-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid rgba(15, 107, 103, 0.35);
  border-top-color: var(--atlas-teal);
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.hl-complaint {
  background: rgba(15, 107, 103, 0.18);
  padding: 0 4px;
  border-radius: 6px;
}
.hl-med {
  background: rgba(199, 136, 42, 0.22);
  padding: 0 4px;
  border-radius: 6px;
}
.hl-dx {
  background: rgba(21, 39, 38, 0.15);
  padding: 0 4px;
  border-radius: 6px;
}
.hl-test {
  background: rgba(79, 96, 93, 0.2);
  padding: 0 4px;
  border-radius: 6px;
}
.highlight-card {
  background: #fffdfa;
  border: 1px dashed var(--atlas-border);
  border-radius: 16px;
  padding: 14px 16px;
  line-height: 1.7;
}
.hl-pii {
  background: rgba(196, 55, 55, 0.2);
  padding: 0 4px;
  border-radius: 6px;
  color: #7a1f1f;
}
</style>
""",
    unsafe_allow_html=True,
)


def highlight_note(text: str, summary) -> str:
    if not text:
        return ""
    highlights = []
    for item in (summary.complaints or []):
        highlights.append((item, "hl-complaint"))
    for item in (summary.medications or []):
        if item and getattr(item, "name", None):
            highlights.append((item.name, "hl-med"))
    for item in (summary.diagnosis or []):
        highlights.append((item, "hl-dx"))
    for item in (summary.tests or []):
        highlights.append((item, "hl-test"))

    # Sort longest first to reduce nested replacements.
    highlights = sorted(
        {h for h in highlights if h[0]},
        key=lambda x: len(x[0]),
        reverse=True,
    )

    def _wrap(match, cls):
        return f'<span class="{cls}">{match.group(0)}</span>'

    out = text
    for phrase, cls in highlights:
        try:
            pattern = re.compile(re.escape(phrase), flags=re.IGNORECASE)
            out = pattern.sub(lambda m: _wrap(m, cls), out)
        except re.error:
            continue
    return out


def highlight_pii(text: str) -> str:
    if not text:
        return ""
    out = text
    for regex in (PHONE_RE, EMAIL_RE, AADHAAR_RE, MRN_RE):
        try:
            out = regex.sub(lambda m: f'<span class="hl-pii">{m.group(0)}</span>', out)
        except re.error:
            continue
    return out


def compute_completeness(summary) -> tuple[int, list[str], list[str]]:
    present = []
    missing = []

    if summary.complaints:
        present.append("complaints")
    else:
        missing.append("complaints")

    if summary.duration:
        present.append("duration")
    else:
        missing.append("duration")

    if summary.vitals:
        vitals_fields = [
            ("bp_systolic", summary.vitals.bp_systolic),
            ("bp_diastolic", summary.vitals.bp_diastolic),
            ("hr", summary.vitals.hr),
            ("spo2", summary.vitals.spo2),
            ("temp", summary.vitals.temp),
        ]
        if any(v for _, v in vitals_fields):
            present.append("vitals")
        else:
            missing.append("vitals")
    else:
        missing.append("vitals")

    if summary.diagnosis:
        present.append("diagnosis")
    else:
        missing.append("diagnosis")

    if summary.medications:
        present.append("medications")
    else:
        missing.append("medications")

    if summary.tests:
        present.append("tests")
    else:
        missing.append("tests")

    if summary.advice:
        present.append("advice")
    else:
        missing.append("advice")

    if summary.follow_up:
        present.append("follow_up")
    else:
        missing.append("follow_up")

    total = len(present) + len(missing)
    score = int(round((len(present) / total) * 100)) if total else 0
    return score, present, missing


def apply_edits(summary, note_text: str, base_flags):
    normalize_structured(summary)
    vflags = run_validations(summary, note_text)
    flags = list(base_flags or [])
    for f in vflags:
        if f not in flags:
            flags.append(f)
    summary.flags = flags
    bundle = build_fhir_bundle(summary)
    return summary, flags, bundle

if "note_text" not in st.session_state:
    st.session_state.note_text = ""
SAMPLE_PLACEHOLDER = "Select a sample…"

if "sample_choice" not in st.session_state:
    st.session_state.sample_choice = SAMPLE_PLACEHOLDER
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None
if "last_run_note" not in st.session_state:
    st.session_state.last_run_note = ""
if "last_run_time" not in st.session_state:
    st.session_state.last_run_time = 0.0
if "edit_payload" not in st.session_state:
    st.session_state.edit_payload = {}
if "followup_questions" not in st.session_state:
    st.session_state.followup_questions = []
if "followup_error" not in st.session_state:
    st.session_state.followup_error = None

provider_label = "OpenAI" if cfg.provider == "openai" else "Ollama"
model_label = cfg.model if cfg.provider == "openai" else (cfg.ollama_model or "local model")

asset_dir = REPO_ROOT / "app" / "assets"
logo_b64 = None
logo_mime = None
for ext, mime in (("png", "image/png"), ("webp", "image/webp"), ("jpg", "image/jpeg"), ("jpeg", "image/jpeg")):
    candidate = asset_dir / f"docsathi.{ext}"
    if candidate.exists():
        logo_b64 = base64.b64encode(candidate.read_bytes()).decode("utf-8")
        logo_mime = mime
        break

logo_html = (
    f'<img class="navbar-logo" src="data:{logo_mime};base64,{logo_b64}" alt="DocSathi mascot" />'
    if logo_b64 and logo_mime
    else '<div class="navbar-logo-fallback">DS</div>'
)

st.markdown(
    f"""
<div class="navbar">
  <div class="navbar-left">
    {logo_html}
    <div>
      <div class="navbar-title">DocSathi</div>
      <div class="navbar-subtitle">ABDM-ready clinical note structuring assistant for documentation support only.</div>
    </div>
  </div>
  <div class="navbar-badges">
    <span class="badge">Documentation Support Only</span>
    <span class="badge badge-ochre">No Diagnosis Inference</span>
    <span class="badge">{provider_label} · {model_label}</span>
  </div>
</div>
<div class="stepper">
  <span class="step step-active">1 · Mask PII</span>
  <span class="step">2 · Extract</span>
  <span class="step">3 · Validate</span>
  <span class="step">4 · Export</span>
</div>
""",
    unsafe_allow_html=True,
)


def trigger_pipeline(note_text: str, sample_choice: str):
    if not note_text.strip():
        st.session_state.last_result = None
        st.session_state.last_error = "Please paste a note or load a sample."
        return
    try:
        llm_client = None
        if cfg.provider == "openai" and not cfg.has_api_key:
            if sample_choice != SAMPLE_PLACEHOLDER:
                class DummyLLM:
                    def extract_structured(self, note_text, options=None):
                        return {
                            "complaints": ["sample"],
                            "duration": None,
                            "vitals": None,
                            "findings": None,
                            "diagnosis": None,
                            "medications": [],
                            "tests": [],
                            "advice": None,
                            "follow_up": None,
                            "flags": [],
                        }

                    def repair_json(self, note_text, bad_json, options=None):
                        return self.extract_structured(note_text)

                llm_client = DummyLLM()
            else:
                st.session_state.last_result = None
                st.session_state.last_error = (
                    "OPENAI_API_KEY not set. Please set it to structure arbitrary notes or load a sample note."
                )
                return

        st.session_state.last_error = None
        result = run_pipeline(
            note_text,
            options={"model": cfg.model, "base_url": cfg.base_url},
            llm_client=llm_client,
        )
        st.session_state.last_result = result
        st.session_state.last_run_note = note_text
        st.session_state.last_run_time = time.time()
    except Exception as e:
        logger.exception("Pipeline failed")
        st.session_state.last_result = None
        st.session_state.last_error = str(e)


def load_sample_note():
    sample_key = st.session_state.get("sample_choice", SAMPLE_PLACEHOLDER)
    if sample_key != SAMPLE_PLACEHOLDER:
        st.session_state.note_text = SAMPLE_NOTES[sample_key]
    else:
        st.session_state.last_error = "Pick a sample note first."


def clear_note():
    st.session_state.note_text = ""
    st.session_state.last_result = None
    st.session_state.last_error = None


def generate_followups(note_text: str, summary, flags):
    try:
        llm = LLMClient(
            model=cfg.model,
            provider=cfg.provider,
            base_url=cfg.base_url,
            ollama_model=cfg.ollama_model,
            ollama_base_url=cfg.ollama_base_url,
        )
        structured_payload = summary.model_dump() if hasattr(summary, "model_dump") else summary.dict()
        data = llm.generate_followup_questions(
            note_text=note_text,
            structured_json=structured_payload,
            flags=flags or [],
        )
        st.session_state.followup_questions = data.get("questions", [])
        st.session_state.followup_error = None
    except LLMClientError as e:
        st.session_state.followup_questions = []
        st.session_state.followup_error = str(e)

col1, col2 = st.columns([2.1, 1])
with col1:
    st.markdown('<div class="section-title">Clinical Note</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Paste OPD note (de-identified or synthetic).</div>', unsafe_allow_html=True)
    note_text = st.text_area(
        "Paste OPD note (de-identified or synthetic):",
        height=320,
        key="note_text",
        label_visibility="collapsed",
        placeholder="Example: 45/M chest pain for 2 days, BP 130/80, HR 84. No diabetes. Given Paracetamol...",
    )
    action_cols = st.columns([1, 1, 2])
    with action_cols[0]:
        run_button = st.button("Structure Note")
        run_spinner_slot = st.empty()
    with action_cols[1]:
        st.button("Clear", on_click=clear_note)
    with action_cols[2]:
        st.markdown(
            '<span class="mono">Tip:</span> Use short, focused sentences for best extraction.',
            unsafe_allow_html=True,
        )
with col2:
    st.markdown('<div class="section-title">Sample Notes</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Pick a pre-filled example note.</div>', unsafe_allow_html=True)
    sample = st.selectbox(
        "Choose a sample note:",
        [SAMPLE_PLACEHOLDER] + list(SAMPLE_NOTES.keys()),
        key="sample_choice",
        label_visibility="collapsed",
    )
    if sample != SAMPLE_PLACEHOLDER:
        st.button("Load sample", on_click=load_sample_note)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    guardrails = []
    guardrails.append(("No diagnosis inference", "status-ok", "Always on"))

    last_result = st.session_state.last_result
    if last_result:
        flags = last_result.get("flags", []) or []
        masked_note = last_result.get("masked_note")
        pii_detected = any(f.startswith("PII detected") for f in flags) or (masked_note and masked_note != note_text)
        if pii_detected:
            guardrails.append(("PII masked", "status-warn", "PII detected & redacted"))
        else:
            guardrails.append(("PII masked", "status-ok", "No PII detected"))

        missing_flags = [f for f in flags if "missing" in f.lower() or "not documented" in f.lower()]
        if missing_flags:
            guardrails.append(("Missing fields flagged", "status-warn", f"{len(missing_flags)} flags"))
        else:
            guardrails.append(("Missing fields flagged", "status-ok", "No missing fields"))
    else:
        guardrails.append(("PII masked", "status-info", "Awaiting note"))
        guardrails.append(("Missing fields flagged", "status-info", "Awaiting analysis"))

    guardrails_html = "".join(
        [f'<span class="status-chip {cls}">• {label}: {detail}</span>' for label, cls, detail in guardrails]
    )
    st.markdown(
        f"""
<div class="card">
  <div class="card-title">Safety Guardrails</div>
  <div>{guardrails_html}</div>
</div>
""",
        unsafe_allow_html=True,
    )

if cfg.provider == "openai" and not cfg.has_api_key:
    st.warning("OPENAI_API_KEY not set. The app can still show sample notes but live LLM calls are disabled.")
if cfg.provider == "ollama" and not cfg.ollama_model:
    st.warning("OLLAMA_MODEL not set. Add it in .env to run with Ollama.")

if run_button:
    if "run_spinner_slot" in locals():
        run_spinner_slot.markdown(
            '<div class="inline-spinner"><span class="spinner-dot"></span>Structuring...</div>',
            unsafe_allow_html=True,
        )
    trigger_pipeline(note_text, sample)
    if "run_spinner_slot" in locals():
        run_spinner_slot.empty()


if st.session_state.last_error:
    st.error(st.session_state.last_error)

if st.session_state.last_result:
    st.markdown('<div id="results-anchor"></div>', unsafe_allow_html=True)
    components.html(
        """
<script>
  const anchor = window.parent.document.querySelector('#results-anchor');
  if (anchor) {
    anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
</script>
""",
        height=0,
    )
    result = st.session_state.last_result
    summary = result["structured"]
    bundle = result["bundle"]
    flags = result["flags"]
    masked = result.get("masked_note")
    raw = result.get("raw_llm_json")
    base_flags = [f for f in (flags or []) if f.startswith("PII detected")]

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Live Atlas — Evidence Highlights</div>', unsafe_allow_html=True)
    highlighted = highlight_note(note_text, summary)
    if highlighted:
        st.markdown(f'<div class="highlight-card">{highlighted}</div>', unsafe_allow_html=True)
    else:
        st.info("No highlights available yet. Add a few symptoms or medications in the note.")

    st.markdown('<div class="section-title">Completeness Score</div>', unsafe_allow_html=True)
    score, present_fields, missing_fields = compute_completeness(summary)
    score_cols = st.columns([1, 2])
    score_cols[0].markdown(
        f"""
<div class="card score-card">
  <div class="card-title">Documentation completeness</div>
  <div class="score-value">{score}%</div>
  <div class="mono">Score = % of key sections captured</div>
  <div class="progress-track"><div class="progress-fill" style="width:{score}%"></div></div>
</div>
""",
        unsafe_allow_html=True,
    )
    missing_html = (
        "".join([f'<span class="chip chip-missing">• {m}</span>' for m in missing_fields])
        if missing_fields
        else '<span class="chip chip-present">✓ All key sections present</span>'
    )
    score_cols[1].markdown(
        f"""
<div class="card score-card">
  <div class="card-title">Missing sections</div>
  <div>{missing_html}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">PII Heatmap</div>', unsafe_allow_html=True)
    pii_highlight = highlight_pii(note_text)
    if pii_highlight != note_text:
        st.markdown(f'<div class="highlight-card">{pii_highlight}</div>', unsafe_allow_html=True)
    else:
        st.success("No PII patterns detected in the note.")

    st.markdown('<div class="section-title">At a Glance</div>', unsafe_allow_html=True)
    metric_cols = st.columns(4)
    metric_cols[0].markdown(
        f"""
<div class="card">
  <div class="card-title">Complaints</div>
  <div class="metric-value">{len(summary.complaints or [])}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    metric_cols[1].markdown(
        f"""
<div class="card">
  <div class="card-title">Medications</div>
  <div class="metric-value">{len(summary.medications or [])}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    metric_cols[2].markdown(
        f"""
<div class="card">
  <div class="card-title">Tests</div>
  <div class="metric-value">{len(summary.tests or [])}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    metric_cols[3].markdown(
        f"""
<div class="card">
  <div class="card-title">Flags</div>
  <div class="metric-value">{len(flags or [])}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Structured Summary", "Clarifying Questions", "Flags", "FHIR Export", "Raw JSON (Debug)"])

    with tabs[0]:
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.subheader("Structured Summary")
        with header_cols[1]:
            summary_json = summary.model_dump() if hasattr(summary, "model_dump") else summary.dict()
            st.download_button(
                "Download Summary JSON",
                data=json.dumps(summary_json, default=str, indent=2),
                file_name="structured_summary.json",
                mime="application/json",
            )
        with st.expander("Quick edits (update structured fields & FHIR)", expanded=False):
            with st.form("edit_structured"):
                complaints_val = ", ".join(summary.complaints or [])
                diagnosis_val = ", ".join(summary.diagnosis or [])
                advice_val = summary.advice or ""
                follow_up_val = summary.follow_up or ""

                complaints_in = st.text_input("Complaints (comma-separated)", value=complaints_val)
                diagnosis_in = st.text_input("Diagnosis (comma-separated)", value=diagnosis_val)
                advice_in = st.text_input("Advice", value=advice_val)
                follow_up_in = st.text_input("Follow-up", value=follow_up_val)

                meds_inputs = []
                for idx, med in enumerate(summary.medications or []):
                    st.markdown(f"<div class='section-title'>Medication {idx+1}: {med.name}</div>", unsafe_allow_html=True)
                    dose = st.text_input(f"Dose", value=med.dose or "", key=f"med_{idx}_dose")
                    freq = st.text_input(f"Frequency", value=med.frequency or "", key=f"med_{idx}_freq")
                    dur = st.text_input(f"Duration", value=med.duration or "", key=f"med_{idx}_dur")
                    meds_inputs.append((idx, dose, freq, dur))

                if st.form_submit_button("Apply edits"):
                    summary.complaints = [c.strip() for c in complaints_in.split(",") if c.strip()] or None
                    summary.diagnosis = [d.strip() for d in diagnosis_in.split(",") if d.strip()] or None
                    summary.advice = advice_in.strip() or None
                    summary.follow_up = follow_up_in.strip() or None
                    for idx, dose, freq, dur in meds_inputs:
                        if summary.medications and idx < len(summary.medications):
                            summary.medications[idx].dose = dose.strip() or None
                            summary.medications[idx].frequency = freq.strip() or None
                            summary.medications[idx].duration = dur.strip() or None

                    summary, flags, bundle = apply_edits(summary, note_text, base_flags)
                    st.session_state.last_result = {
                        "structured": summary,
                        "bundle": bundle,
                        "flags": flags,
                        "masked_note": masked,
                        "raw_llm_json": raw,
                    }
                    st.success("Edits applied.")
                    st.rerun()

        summary_cols = st.columns(2)
        with summary_cols[0]:
            st.markdown(
                f"""
<div class="card">
  <div class="card-title">Chief Complaints</div>
  <div class="mono">{', '.join(summary.complaints or ['—'])}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
<div class="card" style="margin-top:12px;">
  <div class="card-title">Duration</div>
  <div class="mono">{summary.duration or '—'}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with summary_cols[1]:
            st.markdown(
                f"""
<div class="card">
  <div class="card-title">Diagnosis</div>
  <div class="mono">{', '.join(summary.diagnosis or ['—'])}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
<div class="card" style="margin-top:12px;">
  <div class="card-title">Findings</div>
  <div class="mono">{summary.findings or '—'}</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-title" style="margin-top:18px;">Vitals</div>', unsafe_allow_html=True)
        vitals_cols = st.columns(5)
        vitals = summary.vitals
        vitals_data = [
            ("BP Sys", vitals.bp_systolic if vitals else None, "mmHg"),
            ("BP Dia", vitals.bp_diastolic if vitals else None, "mmHg"),
            ("HR", vitals.hr if vitals else None, "bpm"),
            ("SpO2", vitals.spo2 if vitals else None, "%"),
            ("Temp", vitals.temp if vitals else None, ""),
        ]
        for idx, (label, value, unit) in enumerate(vitals_data):
            vitals_cols[idx].markdown(
                f"""
<div class="card">
  <div class="card-title">{label}</div>
  <div class="metric-value">{value if value is not None else '—'}</div>
  <div class="mono">{unit}</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-title" style="margin-top:18px;">Medications</div>', unsafe_allow_html=True)
        meds_rows = []
        for med in summary.medications or []:
            meds_rows.append(
                {
                    "Name": med.name,
                    "Dose": med.dose or "",
                    "Route": med.route or "",
                    "Frequency": med.frequency or "",
                    "Duration": med.duration or "",
                    "PRN": "Yes" if med.prn else "",
                }
            )
        if meds_rows:
            headers = ["Name", "Dose", "Route", "Frequency", "Duration", "PRN"]
            rows_html = "".join(
                [
                    "<tr>"
                    + "".join([f"<td style='padding:8px 10px;border:1px solid #e2d7c4;'>{m.get(h,'')}</td>" for h in headers])
                    + "</tr>"
                    for m in meds_rows
                ]
            )
            table_html = f"""
<div class="card" style="padding:0;">
  <table style="width:100%; border-collapse:collapse; background:#fffdf8; color:#152726; border-radius:12px; overflow:hidden;">
    <thead>
      <tr>
        {''.join([f"<th style='text-align:left;padding:10px;border:1px solid #e2d7c4;background:#f6efe4;'>{h}</th>" for h in headers])}
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>
"""
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><div class="mono">—</div></div>', unsafe_allow_html=True)

        with st.expander("Full structured JSON"):
            st.json(summary.model_dump() if hasattr(summary, "model_dump") else summary.dict())
    with tabs[1]:
        st.subheader("Clarifying Questions")
        info_cols = st.columns([1.2, 2])
        with info_cols[0]:
            can_run = True
            if cfg.provider == "openai" and not cfg.has_api_key:
                can_run = False
            if cfg.provider == "ollama" and not cfg.ollama_model:
                can_run = False
            if st.button("Generate questions", disabled=not can_run):
                generate_followups(note_text, summary, flags)
        with info_cols[1]:
            st.markdown(
                "<div class='muted'>Auto‑suggested questions to complete missing fields. Uses a second LLM call.</div>",
                unsafe_allow_html=True,
            )

        if st.session_state.followup_error:
            st.error(st.session_state.followup_error)
        elif st.session_state.followup_questions:
            for idx, q in enumerate(st.session_state.followup_questions, start=1):
                st.markdown(f"<div class='card'>Q{idx}. {q}</div>", unsafe_allow_html=True)
        else:
            st.info("No questions generated yet.")

    with tabs[2]:
        st.subheader("Flags")
        if flags:
            for f in flags:
                st.markdown(f'<span class="flag-pill">⚠ {f}</span>', unsafe_allow_html=True)
        else:
            st.success("No flags detected.")
        if masked and masked != note_text:
            st.info("PII was detected and masked before sending to LLM.")
            st.text_area("Masked note", value=masked, height=120)
    with tabs[3]:
        st.subheader("FHIR-like Export (preview)")
        st.markdown(
            """
<div class="card">
  <div class="card-title">Bundle Preview</div>
  <div class="mono">FHIR-like minimal bundle (ABDM-aligned, not certified)</div>
</div>
""",
            unsafe_allow_html=True,
        )
        with st.expander("FHIR JSON"):
            st.json(bundle)
        st.download_button("Download FHIR JSON", data=json.dumps(bundle, default=str, indent=2), file_name="abdm_bundle.json", mime="application/json")
    with tabs[4]:
        st.subheader("Raw LLM JSON (debug)")
        with st.expander("Raw JSON response"):
            st.json(raw)
