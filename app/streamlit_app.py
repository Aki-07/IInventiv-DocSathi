import json
import streamlit as st
from dotenv import load_dotenv

from src.core.pipeline import run_pipeline
from src.utils.config import get_config
from app.sample_notes import SAMPLE_NOTES

load_dotenv()
cfg = get_config()

# ---------------------------
# Page config + styling
# ---------------------------
st.set_page_config(page_title="DocSathi — ABDM Note Structuring", layout="wide")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Mulish:wght@400;600;700;800&display=swap');
      html, body, [class*="css"] { font-family: 'Mulish', sans-serif !important; }

      .ds-top {
        display:flex; align-items:flex-start; justify-content:space-between;
        gap:18px; margin-bottom: 10px;
      }
      .ds-title { font-size: 34px; font-weight: 800; line-height: 1.05; margin: 0; }
      .ds-sub { color: rgba(0,0,0,0.65); font-size: 14px; margin-top: 6px; }

      .ds-safety {
        padding: 10px 12px; border-radius: 12px;
        background: rgba(255, 193, 7, 0.18);
        border: 1px solid rgba(255, 193, 7, 0.35);
        margin: 10px 0 14px 0;
      }
      .ds-safety b { font-weight: 800; }

      .ds-card {
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 14px;
        padding: 12px 14px;
        background: white;
      }
      .ds-muted { color: rgba(0,0,0,0.65); font-size: 13px; }

      .pill {
        display:inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        border: 1px solid rgba(0,0,0,0.08);
        background: rgba(11, 83, 148, 0.10);
        margin: 0 6px 6px 0;
      }

      .kv { display:flex; gap:10px; flex-wrap:wrap; }
      .k { color: rgba(0,0,0,0.55); font-size: 12px; font-weight: 700; }
      .v { font-size: 14px; font-weight: 700; }

      hr { border:none; border-top:1px solid rgba(0,0,0,0.08); margin: 10px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Session state
# ---------------------------
if "note_text" not in st.session_state:
    st.session_state.note_text = ""
if "sample_key" not in st.session_state:
    st.session_state.sample_key = "-- none --"
if "result" not in st.session_state:
    st.session_state.result = None

# ---------------------------
# Helpers (schema-robust rendering)
# ---------------------------
def model_to_dict(obj):
    """Works for Pydantic v1/v2 + plain dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):  # pydantic v2
        return obj.model_dump()
    if hasattr(obj, "dict"):  # pydantic v1
        return obj.dict()
    return dict(obj)

def first_present(d, keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, "", [], {}, "null"):
            return d[k]
    return default

def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def fmt_bp(bp):
    if not bp:
        return None
    if isinstance(bp, dict):
        s = bp.get("systolic") or bp.get("sys")
        di = bp.get("diastolic") or bp.get("dia")
        if s and di:
            return f"{s}/{di}"
    if isinstance(bp, str):
        return bp
    return None

def render_flags(flags):
    if not flags:
        st.success("No flags detected. Output looks complete based on the note.")
        return
    st.markdown("".join([f'<span class="pill">⚠️ {f}</span>' for f in flags[:14]]), unsafe_allow_html=True)
    with st.expander("View all flags", expanded=True):
        for f in flags:
            st.warning(f)

def render_summary(structured_dict):
    # Try common key variants (robust across schema changes)
    complaints = first_present(structured_dict, ["complaints", "complaint_s", "complaint", "chief_complaint"], default=[])
    duration = first_present(structured_dict, ["duration", "complaint_duration"], default=None)
    findings = first_present(structured_dict, ["findings", "exam", "observations"], default=None)
    advice = first_present(structured_dict, ["advice", "plan", "counselling", "instructions"], default=None)
    follow_up = first_present(structured_dict, ["follow_up", "followup", "fu"], default=None)

    # Diagnosis/problems: only show what is present; otherwise show "not inferred"
    diagnosis = first_present(structured_dict, ["diagnosis", "problems", "problem_list", "assessment"], default=[])
    meds = first_present(structured_dict, ["medications", "meds", "rx"], default=[])
    tests = first_present(structured_dict, ["tests", "tests_advised", "investigations"], default=[])

    vitals = first_present(structured_dict, ["vitals"], default={})
    if not isinstance(vitals, dict):
        vitals = {}

    # Derive compact vitals line
    bp = fmt_bp(vitals.get("bp") or vitals.get("blood_pressure"))
    hr = vitals.get("hr") or vitals.get("heart_rate")
    spo2 = vitals.get("spo2") or vitals.get("spO2") or vitals.get("oxygen_saturation")
    temp = vitals.get("temp") or vitals.get("temperature")

    vit_parts = []
    if bp: vit_parts.append(f"BP {bp}")
    if hr: vit_parts.append(f"HR {hr}")
    if spo2: vit_parts.append(f"SpO₂ {spo2}")
    if temp: vit_parts.append(f"Temp {temp}")
    vit_line = " • ".join(vit_parts) if vit_parts else "—"

    # Top metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Medications", len(as_list(meds)))
    m2.metric("Tests", len(as_list(tests)))
    m3.metric("Vitals", len(vit_parts))
    m4.metric("Fields captured", sum([
        1 if as_list(complaints) else 0,
        1 if duration else 0,
        1 if vit_parts else 0,
        1 if as_list(diagnosis) else 0,
        1 if as_list(meds) else 0,
        1 if as_list(tests) else 0,
        1 if follow_up else 0,
    ]))

    st.divider()

    left, right = st.columns([1.2, 1.0], gap="large")

    with left:
        st.subheader("Structured Visit Summary")

        st.markdown("**Complaint(s)**")
        st.write(", ".join([str(x) for x in as_list(complaints)]) if as_list(complaints) else "—")

        st.markdown("**Duration**")
        st.write(duration or "—")

        st.markdown("**Vitals**")
        st.write(vit_line)

        st.markdown("**Findings**")
        st.write(findings or "—")

        st.markdown("**Diagnosis / Problems**")
        if as_list(diagnosis):
            st.write(", ".join([str(x) for x in as_list(diagnosis)]))
        else:
            st.write("Not stated (not inferred)")

        st.markdown("**Advice / Plan**")
        st.write(advice or "—")

        st.markdown("**Follow-up**")
        st.write(follow_up or "—")

    with right:
        st.subheader("Medications & Tests")

        st.markdown("**Medications**")
        meds_list = as_list(meds)
        if meds_list:
            rows = []
            for m in meds_list:
                if isinstance(m, dict):
                    rows.append({
                        "Name": m.get("name", ""),
                        "Dose": m.get("dose", ""),
                        "Route": m.get("route", ""),
                        "Frequency": m.get("frequency", ""),
                        "Duration": m.get("duration", ""),
                        "PRN": m.get("prn", ""),
                    })
                else:
                    rows.append({"Name": str(m), "Dose": "", "Route": "", "Frequency": "", "Duration": "", "PRN": ""})
            st.dataframe(rows, width=True, hide_index=True)
        else:
            st.write("—")

        st.markdown("**Tests advised**")
        st.write(", ".join([str(x) for x in as_list(tests)]) if as_list(tests) else "—")


# ---------------------------
# Header
# ---------------------------
st.markdown(
    """
    <div class="ds-top">
      <div>
        <div class="ds-title">DocSathi</div>
        <div class="ds-sub">ABDM-ready note structuring • Free-text → Structured Summary → Interoperable Export</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ds-safety">
      <b>Documentation support only.</b> Not for diagnosis. Missing/uncertain details are flagged for clinician confirmation.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.header("Demo Controls")

    sample = st.selectbox(
        "Load a sample note",
        ["-- none --"] + list(SAMPLE_NOTES.keys()),
        index=(["-- none --"] + list(SAMPLE_NOTES.keys())).index(st.session_state.sample_key)
        if st.session_state.sample_key in (["-- none --"] + list(SAMPLE_NOTES.keys()))
        else 0,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Load", use_container_width=True):
            if sample != "-- none --":
                st.session_state.sample_key = sample
                st.session_state.note_text = SAMPLE_NOTES[sample]
            else:
                st.toast("Pick a sample first.", icon="⚠️")
    with col2:
        if st.button("Clear", use_container_width=True):
            st.session_state.sample_key = "-- none --"
            st.session_state.note_text = ""
            st.session_state.result = None

    st.divider()
    st.subheader("Settings")
    strict_mode = st.toggle("Strict mode (more flags)", value=True)
    show_debug = st.toggle("Show debug tab", value=False)

    st.divider()
    st.subheader("LLM status")
    if getattr(cfg, "has_api_key", False):
        st.success(f"Enabled: {getattr(cfg, 'model', 'gpt-5-mini')}")
    else:
        st.warning("Disabled: OPENAI_API_KEY not set")

# ---------------------------
# Main input
# ---------------------------
colL, colR = st.columns([2.15, 1.0], gap="large")

with colL:
    st.subheader("Clinical Note Input")
    st.caption("Use synthetic / de-identified notes only.")
    st.text_area(
        label="Note Input",
        key="note_text",
        height=260,
        placeholder="Paste a synthetic/de-identified OPD note here…",
        label_visibility="collapsed",
    )

with colR:
    st.subheader("Output Preview")
    st.markdown(
        """
        <div class="ds-card">
          <div class="ds-muted">
            <b>You’ll get:</b><br>
            • Structured visit summary<br>
            • Missing/uncertain items flagged<br>
            • ABDM-aligned export (FHIR-like JSON)
          </div>
          <hr>
          <div class="ds-muted">
            <b>Best demo:</b> Load a sample note and click <b>Structure Note</b>.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

run_disabled = not bool(st.session_state.note_text.strip())
run_btn = st.button("Structure Note", type="primary", disabled=run_disabled, use_container_width=False)

if run_btn:
    try:
        with st.spinner("Structuring… validating… preparing export…"):
            # Pass options through; pipeline can ignore unknown keys safely.
            st.session_state.result = run_pipeline(
                st.session_state.note_text.strip(),
                options={
                    "model": getattr(cfg, "model", "gpt-5-mini"),
                    "base_url": getattr(cfg, "base_url", None),
                    "strict_mode": strict_mode,
                },
            )
    except Exception as e:
        st.error(f"Pipeline error: {e}")
        st.session_state.result = None

# ---------------------------
# Results
# ---------------------------
result = st.session_state.result
if result:
    structured = result.get("structured")
    bundle = result.get("bundle")
    flags = result.get("flags") or []
    masked_note = result.get("masked_note")
    raw_llm = result.get("raw_llm_json")

    tabs = ["Structured Summary", "Flags", "Export"]
    if show_debug:
        tabs.append("Debug")

    t = st.tabs(tabs)

    with t[0]:
        sdict = model_to_dict(structured)
        render_summary(sdict)

    with t[1]:
        st.subheader("Flags & Confirmation")
        render_flags(flags)
        if masked_note and masked_note != st.session_state.note_text.strip():
            st.info("PII was detected and masked before LLM processing.")
            with st.expander("View masked note"):
                st.text_area("Masked note", value=masked_note, height=140)

    with t[2]:
        st.subheader("ABDM-aligned export (FHIR-like bundle)")
        st.caption("Mapping-ready output for downstream systems (not claiming official compliance).")
        st.json(bundle)
        st.download_button(
            "Download Export JSON",
            data=json.dumps(bundle, default=str, indent=2),
            file_name="abdm_fhir_like_bundle.json",
            mime="application/json",
            use_container_width=True,
        )

    if show_debug:
        with t[3]:
            st.subheader("Debug")
            st.markdown("**Raw LLM JSON**")
            st.json(raw_llm)
