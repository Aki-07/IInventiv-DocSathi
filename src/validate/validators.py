from typing import List
from src.core.schemas import StructuredNote


def run_validations(struct: StructuredNote, original_note: str) -> List[str]:
    flags = []
    # Diagnosis rule
    if not struct.diagnosis or len(struct.diagnosis) == 0:
        # check original note for explicit diagnosis markers
        if not any(k in (original_note or "").lower() for k in ["dx:", "diagnosis:", "diagnosis\b"]):
            flags.append("Diagnosis not documented (not inferred)")
        else:
            flags.append("Diagnosis section absent or empty")

    # Medication completeness
    if struct.medications:
        for m in struct.medications:
            missing = []
            if not m.dose:
                missing.append("dose")
            if not m.frequency:
                missing.append("frequency")
            if not m.duration:
                missing.append("duration")
            if missing:
                flags.append(f"Medication '{m.name}' missing: {', '.join(missing)}")

    # Vitals presence
    if struct.vitals:
        pass
    # ensure unique
    seen = set()
    unique_flags = []
    for f in flags:
        if f not in seen:
            unique_flags.append(f)
            seen.add(f)
    return unique_flags
