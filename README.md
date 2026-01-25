# DocSathi: ABDM-Ready Clinical Note Structuring Assistant

A clinician-facing documentation assistant that converts **free-text OPD/clinic notes** into a **standardized visit summary** and an **ABDM-aligned, interoperable structured export**. It is designed for **documentation support only** (not diagnosis): missing or uncertain details are **flagged for clinician confirmation** instead of being guessed.

## What this project does
Given a free-text note (synthetic / de-identified), the app:
- Extracts structured fields (complaints, duration, vitals, meds, tests, follow-up, etc.)
- Runs deterministic validation + normalization (e.g., BP split, frequency normalization)
- Produces a compact **Flags** list for missing/ambiguous items
- Exports a minimal **FHIR-like bundle** shaped for downstream ABDM-style workflows (mapping-ready; not claiming certification)

## Safety & scope
- **Not for diagnosis.** The system never infers diagnoses. It only captures a diagnosis/problem if explicitly present in the note.
- **No hallucination policy.** If a value is not present, it stays `null` and is flagged.
- **Use only synthetic/de-identified text** in demo mode. A PII detector masks common identifiers before LLM calls.

---

## Quickstart

### 1) Install
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Configure environment

Copy `.env.example` to `.env` and fill values:

```bash
cp .env.example .env
```

Required:

* `OPENAI_API_KEY`

Optional:

* `OPENAI_MODEL` (defaults to `gpt-5-mini`)
* `OPENAI_BASE_URL` (if using an OpenAI-compatible gateway)

### 3) Run the Streamlit app

```bash
streamlit run app/streamlit_app.py
```

The UI includes:

* Sample note picker
* “Structure Note” action
* Tabs: Structured Summary / Flags / FHIR Export / Raw JSON (Debug)
* Export download button

If `OPENAI_API_KEY` is missing, the app should show a clear message and disable live extraction (or run in mock mode, depending on configuration).

---

## Project structure

```
IInventiv-DocSathi/
├─ app/                         # Streamlit UI
│  ├─ streamlit_app.py
│  ├─ ui_components.py
│  └─ sample_notes.py
│
├─ src/                         # Core logic
│  ├─ core/                     # Schemas + pipeline orchestration
│  ├─ llm/                      # GPT-5-mini client + prompts + parsing
│  ├─ privacy/                  # PII detection + masking
│  ├─ validate/                 # Deterministic validators/normalizers + flag rules
│  ├─ export/                   # Minimal FHIR-like (ABDM-aligned) bundle builder
│  ├─ data/                     # Synthetic dataset + loader
│  └─ utils/                    # Config, logging, timers
│
├─ eval/                        # Evaluation runner + metrics
└─ tests/                       # Unit tests + mocked pipeline tests
```

---

## How the pipeline works (high-level)

1. **PII guard** masks common identifiers (phone/email/ID patterns)
2. **LLM extraction** (GPT-5-mini) returns strict JSON (no inference)
3. **Schema validation** ensures output conforms to the `StructuredNote` model
4. **Deterministic checks** normalize formats and add flags (missing/ambiguous)
5. **FHIR-like export** builds a minimal bundle for downstream systems

---

## Example: expected behavior

* If the note does **not** include a diagnosis, the output will show:

	* Diagnosis set to `null` / empty
	* Flag: `Diagnosis not documented (not inferred)`
* If a medication is missing **dose/frequency/duration**, it will be flagged rather than filled in.

---

## Evaluation (optional)

Run the lightweight evaluation on the included synthetic dataset:

```bash
python eval/run_eval.py
```

Outputs (CSV/JSON) are written to `eval/outputs/` and can be used for poster metrics such as:

* Field presence accuracy
* Medication completeness flag rate
* “Time saved” proxy (if you record timings during demo)

---

## Testing

Run unit tests:

```bash
pytest -q
```

Tests focus on:

* Normalizers and validators (deterministic logic)
* FHIR-like exporter shape
* Pipeline behavior with **mocked** LLM responses (no network calls)

---

## Configuration reference

Environment variables:

* `OPENAI_API_KEY` (required)
* `OPENAI_MODEL` (default: `gpt-5-mini`)
* `OPENAI_BASE_URL` (optional)
* `APP_DEBUG` (optional: show raw JSON and traces)
* `STRICT_MODE` (optional: stricter missing-field flags)

---

## License / usage

This repository is intended for R&D fair demonstration and prototyping. Do not use with real patient data without appropriate approvals, security controls, and compliance review.

```
::contentReference[oaicite:0]{index=0}
```

