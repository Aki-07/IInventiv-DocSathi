import streamlit as st
from dotenv import load_dotenv
import os
import json
from src.core.pipeline import run_pipeline
from src.utils.config import get_config
from app.sample_notes import SAMPLE_NOTES
from src.utils.logging import get_logger

load_dotenv()
logger = get_logger()
cfg = get_config()

st.set_page_config(page_title="ABDM Note Assistant", layout="wide")
st.title("ABDM Note Assistant — Documentation Support Only")
st.markdown('<small>Banner: Documentation support only. Not for diagnosis.</small>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    note_text = st.text_area("Paste OPD note (de-identified or synthetic):", height=300)
with col2:
    sample = st.selectbox("Or choose a sample note:", ["-- none --"] + list(SAMPLE_NOTES.keys()))
    if sample != "-- none --":
        if st.button("Load sample"):
            note_text = SAMPLE_NOTES[sample]

run_button = st.button("Structure Note")

if not cfg.has_api_key:
    st.warning("OPENAI_API_KEY not set. The app can still show sample notes but live LLM calls are disabled.")

if run_button:
    if not note_text.strip():
        st.error("Please paste a note or load a sample.")
    else:
        try:
            # If API key missing, allow mock run only for sample notes
            llm_client = None
            if not cfg.has_api_key:
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

            result = run_pipeline(note_text, options={"model": cfg.model, "base_url": cfg.base_url}, llm_client=llm_client)
        except Exception as e:
            logger.exception("Pipeline failed")
            st.error(f"Pipeline error: {e}")
        else:
            summary = result["structured"]
            bundle = result["bundle"]
            flags = result["flags"]
            masked = result.get("masked_note")
            raw = result.get("raw_llm_json")

            tabs = st.tabs(["Structured Summary", "Flags", "FHIR Export", "Raw JSON (Debug)"])

            with tabs[0]:
                st.subheader("Structured Summary")
                st.json(summary.dict())
            with tabs[1]:
                st.subheader("Flags")
                st.write(flags)
                if masked and masked != note_text:
                    st.info("PII was detected and masked before sending to LLM.")
                    st.text_area("Masked note", value=masked, height=120)
            with tabs[2]:
                st.subheader("FHIR-like Export (preview)")
                st.json(bundle)
                st.download_button("Download FHIR JSON", data=json.dumps(bundle, default=str, indent=2), file_name="abdm_bundle.json", mime="application/json")
            with tabs[3]:
                st.subheader("Raw LLM JSON (debug)")
                st.json(raw)
