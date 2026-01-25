from src.core.schemas import StructuredNote, Medication
from src.validate.validators import run_validations


def test_medication_completeness():
    m = Medication(name='TestMed')
    s = StructuredNote(medications=[m])
    flags = run_validations(s, original_note='')
    assert any('missing' in f.lower() for f in flags)

def test_diagnosis_flag():
    s = StructuredNote(diagnosis=None)
    flags = run_validations(s, original_note='no diagnosis')
    assert any('diagnosis not documented' in f.lower() or 'diagnosis' in f.lower() for f in flags)
