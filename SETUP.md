# DocSathi Setup & Run Guide

## Environment Status ✓

The virtual environment `doc_sathi_venv` has been created and all dependencies are installed.

**Installed packages:**
- streamlit (1.53.1)
- openai (2.15.0)
- pydantic (2.12.5)
- python-dotenv (1.2.1)
- pytest (9.0.2)
- requests (2.32.5)

**All unit tests pass:** 5/5 ✓

---

## Quick Start

### 1. Activate the virtual environment

```bash
cd /Users/arindamc/Projects/Personal/iinventiv_2026/IInventiv-Opd
source doc_sathi_venv/bin/activate
```

### 2. Set up your `.env` file

```bash
cp .env.example .env
```

Then edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-mini
```

### Optional: Run without OpenAI using Ollama

If you have Ollama running locally:

```
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Run the Streamlit app

```bash
(doc_sathi_venv) $ streamlit run app/streamlit_app.py
```

The app will launch at `http://localhost:8501`

### 4. Run tests

```bash
(doc_sathi_venv) $ pytest -q
```

---

## Project Structure

```
IInventiv-Opd/
├─ app/                          # Streamlit UI
│  ├─ streamlit_app.py          # Main app entry
│  ├─ sample_notes.py           # 5 sample clinical notes
│  └─ ui_components.py          # (placeholder)
│
├─ src/                          # Core modules
│  ├─ core/
│  │  ├─ schemas.py             # Pydantic models (StructuredNote, Vitals, Medication, etc.)
│  │  ├─ pipeline.py            # Main orchestration (extraction → normalization → export)
│  │  ├─ constants.py           # (placeholder)
│  │  └─ types.py               # (placeholder)
│  ├─ llm/
│  │  ├─ client.py              # OpenAI-compatible LLM client
│  │  ├─ prompts.py             # Extraction & repair prompts
│  │  ├─ response_parsing.py     # (placeholder)
│  │  └─ retry.py               # Retry decorator with exponential backoff
│  ├─ privacy/
│  │  ├─ pii.py                 # PII masking utilities
│  │  └─ patterns.py            # Regex patterns for PII detection
│  ├─ validate/
│  │  ├─ normalizers.py         # Deterministic normalization (BP split, frequency map, etc.)
│  │  ├─ validators.py          # Flag generation (missing diagnosis, incomplete meds, etc.)
│  │  └─ rules.py               # (placeholder)
│  ├─ export/
│  │  ├─ fhir_bundle.py         # FHIR-like minimal bundle builder
│  │  └─ mappings.py            # (placeholder)
│  ├─ data/
│  │  ├─ synthetic_notes.jsonl  # Sample dataset
│  │  ├─ load_dataset.py        # Dataset loader
│  │  └─ label_schema.json      # (placeholder)
│  └─ utils/
│     ├─ config.py              # Environment config reader
│     ├─ logging.py             # Logger setup
│     └─ timers.py              # Simple timer context
│
├─ tests/                        # Unit tests
│  ├─ test_normalizers.py       # Normalizer tests
│  ├─ test_validators.py        # Validator tests
│  ├─ test_fhir_export.py       # FHIR export tests
│  └─ test_pipeline_mocked_llm.py # End-to-end pipeline (mocked LLM)
│
├─ eval/                         # Evaluation
│  ├─ run_eval.py               # Evaluation runner
│  └─ metrics.py                # Metrics computation
│
├─ .env.example                 # Environment template
├─ requirements.txt             # Python dependencies
├─ README.md                    # Project documentation
└─ SETUP.md                     # This file

```

---

## Features Implemented

✓ **Streamlit UI** with tabs: Structured Summary | Flags | FHIR Export | Raw JSON (Debug)
✓ **LLM Integration** (GPT-5-mini via OpenAI SDK) with strict JSON-only prompts
✓ **PII Masking** (phone, email, Aadhaar, MRN patterns detected and redacted before LLM calls)
✓ **Deterministic Validation & Normalization** (BP split, frequency mapping, temperature formatting)
✓ **FHIR-like Export** (minimal bundle: Patient, Encounter, Observations, Conditions, MedicationStatements, ServiceRequests)
✓ **Hard Safety Rules** (no diagnosis inference, no value invention, all missing fields flagged)
✓ **Unit Tests** (normalizers, validators, FHIR exporter, mocked pipeline)
✓ **Evaluation Runner** (field presence accuracy metrics)

---

## Known Limitations (MVP)

- FHIR bundle is generic/placeholder (no official codes, not certified)
- LLM calls are non-streaming (simple ChatCompletion)
- Minimal evidence extraction (just text + confidence level)
- No user authentication or audit logging
- No database backend (all in-memory)

---

## Troubleshooting

### "OPENAI_API_KEY not set" error
- Copy `.env.example` to `.env` and add your key
- Or set directly: `export OPENAI_API_KEY=sk-...`

### Import errors after activating venv
- Ensure you're inside the virtual environment: `which python` should show `doc_sathi_venv/bin/python`
- Re-install: `pip install -r requirements.txt`

### Tests fail
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Run with verbose output: `pytest -vv`

---

## Next Steps

1. Test the Streamlit app with sample notes (no API key needed in mock mode)
2. Add your OPENAI_API_KEY to `.env` and test live extraction
3. Review the generated flags and FHIR bundle outputs
4. Adapt sample notes or add your own synthetic examples in `app/sample_notes.py`
