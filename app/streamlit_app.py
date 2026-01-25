import base64
import json
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Ensure repo root is on sys.path so `src` imports work when running via Streamlit.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.pipeline import run_pipeline
from src.utils.config import get_config
from app.sample_notes import SAMPLE_NOTES
from src.utils.logging import get_logger

load_dotenv()
logger = get_logger()
cfg = get_config()

st.set_page_config(page_title="DocSathi — Clinical Atlas", layout="wide", page_icon="🩺")

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
  padding-top: 1.5rem;
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
  margin-bottom: 14px;
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
  color: var(--atlas-teal);
  background: rgba(15,107,103,0.12);
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
</style>
""",
    unsafe_allow_html=True,
)

if "note_text" not in st.session_state:
    st.session_state.note_text = ""
if "sample_choice" not in st.session_state:
    st.session_state.sample_choice = "-- none --"
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None

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
      <div class="navbar-title">DocSathi — Clinical Atlas</div>
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
    with action_cols[1]:
        if st.button("Clear"):
            st.session_state.note_text = ""
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
        ["-- none --"] + list(SAMPLE_NOTES.keys()),
        key="sample_choice",
        label_visibility="collapsed",
    )
    if sample != "-- none --":
        if st.button("Load sample"):
            st.session_state.note_text = SAMPLE_NOTES[sample]
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="card">
  <div class="card-title">Safety Guardrails</div>
  <div>• No diagnosis inference</div>
  <div>• Missing fields are flagged</div>
  <div>• PII masked before LLM call</div>
</div>
""",
        unsafe_allow_html=True,
    )

if cfg.provider == "openai" and not cfg.has_api_key:
    st.warning("OPENAI_API_KEY not set. The app can still show sample notes but live LLM calls are disabled.")
if cfg.provider == "ollama" and not cfg.ollama_model:
    st.warning("OLLAMA_MODEL not set. Add it in .env to run with Ollama.")

if run_button:
    if not note_text.strip():
        st.error("Please paste a note or load a sample.")
    else:
        try:
            # If API key missing, allow mock run only for sample notes
            llm_client = None
            if cfg.provider == "openai" and not cfg.has_api_key:
                if sample != "-- none --":
                    class DummyLLM:
                        def extract_structured(self, note_text, options=None):
                            return {"complaints": ["sample"], "duration": None, "vitals": None, "findings": None, "diagnosis": None, "medications": [], "tests": [], "advice": None, "follow_up": None, "flags": []}
                        def repair_json(self, note_text, bad_json, options=None):
                            return self.extract_structured(note_text)
                    llm_client = DummyLLM()
                else:
                    st.error("OPENAI_API_KEY not set. Please set it to structure arbitrary notes or load a sample note to run in mock mode.")
                    llm_client = None

            st.session_state.last_error = None
            with st.spinner("Structuring note..."):
                result = run_pipeline(
                    note_text,
                    options={"model": cfg.model, "base_url": cfg.base_url},
                    llm_client=llm_client,
                )
            st.session_state.last_result = result
        except Exception as e:
            logger.exception("Pipeline failed")
            st.session_state.last_result = None
            st.session_state.last_error = str(e)
            st.error(f"Pipeline error: {e}")

if st.session_state.last_error:
    st.error(st.session_state.last_error)

if st.session_state.last_result:
    result = st.session_state.last_result
    summary = result["structured"]
    bundle = result["bundle"]
    flags = result["flags"]
    masked = result.get("masked_note")
    raw = result.get("raw_llm_json")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
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

    tabs = st.tabs(["Structured Summary", "Flags", "FHIR Export", "Raw JSON (Debug)"])

    with tabs[0]:
        st.subheader("Structured Summary")
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

        with st.expander("Full structured JSON"):
            st.json(summary.dict())
    with tabs[1]:
        st.subheader("Flags")
        if flags:
            for f in flags:
                st.markdown(f'<span class="flag-pill">⚠ {f}</span>', unsafe_allow_html=True)
        else:
            st.success("No flags detected.")
        if masked and masked != note_text:
            st.info("PII was detected and masked before sending to LLM.")
            st.text_area("Masked note", value=masked, height=120)
    with tabs[2]:
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
    with tabs[3]:
        st.subheader("Raw LLM JSON (debug)")
        with st.expander("Raw JSON response"):
            st.json(raw)
