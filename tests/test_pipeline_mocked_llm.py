from src.core.pipeline import run_pipeline
from src.core.schemas import StructuredNote


class DummyLLM:
    def __init__(self):
        pass

    def extract_structured(self, note_text, options=None):
        # return a minimal valid structure
        return {
            "complaints": ["cough"],
            "duration": "2 days",
            "vitals": {"bp_systolic": 120, "bp_diastolic": 80, "hr": 78, "spo2": 98, "temp": "37 C"},
            "findings": None,
            "diagnosis": None,
            "medications": [],
            "tests": [],
            "advice": None,
            "follow_up": None,
            "flags": []
        }

    def repair_json(self, note_text, bad_json, options=None):
        return self.extract_structured(note_text)


def test_pipeline_with_mocked_llm():
    note = "Patient with cough for 2 days."
    result = run_pipeline(note, options={}, llm_client=DummyLLM())
    structured = result['structured']
    assert isinstance(structured, StructuredNote)
    assert 'Diagnosis not documented' in ' '.join(result['flags']) or 'Diagnosis not documented' in (structured.flags or [])
