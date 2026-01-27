import re

PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\d{10}|\d{3}[-.\s]\d{3}[-.\s]\d{4})\b")
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
AADHAAR_RE = re.compile(r"\b\d{12}\b")
MRN_RE = re.compile(r"\bMRN[:#\s]*[A-Za-z0-9-]+\b", re.IGNORECASE)
NAME_RE = re.compile(
    r"\b(?:name|patient|pt|mr|mrs|ms|dr|doctor)[:\s]+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b",
    re.IGNORECASE,
)
