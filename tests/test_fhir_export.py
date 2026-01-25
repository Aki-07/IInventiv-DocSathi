from src.core.schemas import StructuredNote, Vitals, Medication
from src.export.fhir_bundle import build_fhir_bundle


def test_fhir_bundle_contains_patient_and_entries():
    s = StructuredNote(vitals=Vitals(bp_systolic=120, bp_diastolic=80, hr=70), medications=[Medication(name='Paracetamol', dose='500 mg')])
    bundle = build_fhir_bundle(s)
    assert bundle['resourceType'] == 'Bundle'
    assert any(e['resource']['resourceType'] == 'Patient' for e in bundle['entry'])
    assert any(e['resource']['resourceType'] == 'Observation' for e in bundle['entry'])
