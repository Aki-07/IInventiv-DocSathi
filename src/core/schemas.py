from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Evidence(BaseModel):
    evidence_text: Optional[str] = None
    confidence: Optional[str] = None  # high/medium/low


class Medication(BaseModel):
    name: str
    dose: Optional[str | int | float] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    prn: Optional[bool] = None
    evidence: Optional[Evidence] = None

    @field_validator('prn', mode='before')
    @classmethod
    def parse_prn(cls, v):
        """Convert string 'PRN' or similar to boolean."""
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            # Common PRN indicators
            if v.upper() in ('PRN', 'YES', 'TRUE', '1', 'Y'):
                return True
            if v.upper() in ('NO', 'FALSE', '0', 'N'):
                return False
        return v


class Vitals(BaseModel):
    bp_systolic: Optional[int | str] = None  # can be str like "120/80" before normalization
    bp_diastolic: Optional[int] = None
    hr: Optional[int] = None
    spo2: Optional[float | str] = None
    temp: Optional[float | str] = None  # accept float (e.g. 98.6) or string
    evidence: Optional[Evidence] = None


class StructuredNote(BaseModel):
    complaints: Optional[List[str]] = None
    duration: Optional[str] = None
    vitals: Optional[Vitals] = None
    findings: Optional[str] = None
    diagnosis: Optional[List[str]] = None
    medications: Optional[List[Medication]] = None
    tests: Optional[List[str]] = None
    advice: Optional[str] = None
    follow_up: Optional[str] = None
    flags: List[str] = Field(default_factory=list)
    # evidence: keep top-level references if needed
    complaint_evidence: Optional[Evidence] = None
    diagnosis_evidence: Optional[Evidence] = None
    meds_evidence: Optional[Evidence] = None
