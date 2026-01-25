from typing import List, Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    evidence_text: Optional[str] = None
    confidence: Optional[str] = None  # high/medium/low


class Medication(BaseModel):
    name: str
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    prn: Optional[bool] = None
    evidence: Optional[Evidence] = None


class Vitals(BaseModel):
    bp_systolic: Optional[int | str] = None  # can be str like "120/80" before normalization
    bp_diastolic: Optional[int] = None
    hr: Optional[int] = None
    spo2: Optional[float] = None
    temp: Optional[str] = None
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
