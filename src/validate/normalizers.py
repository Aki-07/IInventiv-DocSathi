import re
from src.core.schemas import StructuredNote


def split_bp_field(vitals):
    if not vitals or not getattr(vitals, 'bp_systolic', None):
        return
    # if bp_systolic is a string like '120/80'
    val = vitals.bp_systolic
    if isinstance(val, str) and '/' in val:
        parts = val.split('/')
        try:
            vitals.bp_systolic = int(parts[0])
            vitals.bp_diastolic = int(parts[1])
        except Exception:
            pass


_freq_map = {
    'OD': 'once daily',
    'BD': 'twice daily',
    'TID': 'three times daily',
    'SOS': 'as needed',
    'PRN': 'as needed',
}


def normalize_frequency(freq: str):
    if not freq:
        return freq
    f = freq.strip().upper()
    if f in _freq_map:
        return _freq_map[f]
    # common patterns like 'od' or 'once daily'
    return freq


def normalize_medications(meds):
    if not meds:
        return
    for m in meds:
        if m.dose is not None and not isinstance(m.dose, str):
            m.dose = str(m.dose)
        if m.frequency:
            m.frequency = normalize_frequency(m.frequency)


def normalize_structured(struct: StructuredNote):
    # BP split if needed
    if struct.vitals:
        # handle case where bp_systolic may be string '120/80'
        try:
            if isinstance(struct.vitals.bp_systolic, str) and '/' in struct.vitals.bp_systolic:
                parts = struct.vitals.bp_systolic.split('/')
                struct.vitals.bp_systolic = int(parts[0])
                struct.vitals.bp_diastolic = int(parts[1])
        except Exception:
            pass

    # normalize meds
    normalize_medications(struct.medications)

    # normalize temp formatting: just ensure string if present
    if struct.vitals and struct.vitals.temp is not None:
        struct.vitals.temp = str(struct.vitals.temp)
    # normalize spo2 to float if it is a string like "98%"
    if struct.vitals and struct.vitals.spo2 is not None:
        try:
            if isinstance(struct.vitals.spo2, str):
                val = struct.vitals.spo2.strip().replace("%", "")
                struct.vitals.spo2 = float(val)
        except Exception:
            pass
