from datetime import datetime
from typing import Dict, Any


def _obs_resource(code: str, value: Any, unit: str = None):
    res = {"resourceType": "Observation", "code": {"text": code}, "value": value, "timestamp": datetime.utcnow().isoformat()}
    if unit:
        res["unit"] = unit
    return res


def build_fhir_bundle(structured) -> Dict[str, Any]:
    # Minimal FHIR-like bundle
    bundle = {"resourceType": "Bundle", "type": "document", "timestamp": datetime.utcnow().isoformat(), "entry": []}

    # Patient placeholder
    bundle["entry"].append({"resource": {"resourceType": "Patient", "id": "deidentified", "meta": {"note": "de-identified placeholder"}}})

    # Encounter
    bundle["entry"].append({"resource": {"resourceType": "Encounter", "status": "finished", "period": {"start": datetime.utcnow().isoformat()}}})

    # Vitals
    v = structured.vitals
    if v:
        if v.bp_systolic is not None:
            bundle["entry"].append({"resource": _obs_resource("blood pressure systolic", v.bp_systolic, "mmHg")})
        if v.bp_diastolic is not None:
            bundle["entry"].append({"resource": _obs_resource("blood pressure diastolic", v.bp_diastolic, "mmHg")})
        if v.hr is not None:
            bundle["entry"].append({"resource": _obs_resource("heart rate", v.hr, "bpm")})
        if v.spo2 is not None:
            bundle["entry"].append({"resource": _obs_resource("spo2", v.spo2, "%")})
        if v.temp is not None:
            bundle["entry"].append({"resource": _obs_resource("temperature", v.temp)})

    # Conditions (diagnosis) - only if present
    if structured.diagnosis:
        for d in structured.diagnosis:
            bundle["entry"].append({"resource": {"resourceType": "Condition", "code": {"text": d}}})

    # Medications
    if structured.medications:
        for m in structured.medications:
            med = {"resourceType": "MedicationStatement", "medication": {"text": m.name}}
            if m.dose:
                med["dosage"] = {"dose": m.dose, "route": m.route, "frequency": m.frequency, "duration": m.duration}
            bundle["entry"].append({"resource": med})

    # ServiceRequests for tests
    if structured.tests:
        for t in structured.tests:
            bundle["entry"].append({"resource": {"resourceType": "ServiceRequest", "code": {"text": t}}})

    return bundle
