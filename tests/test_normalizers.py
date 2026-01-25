from src.core.schemas import StructuredNote, Vitals
from src.validate.normalizers import normalize_structured


def test_split_bp_and_temp():
    s = StructuredNote(vitals=Vitals(bp_systolic='120/80', temp=37))
    normalize_structured(s)
    assert s.vitals.bp_systolic == 120
    assert s.vitals.bp_diastolic == 80
    assert isinstance(s.vitals.temp, str)
