from typing import Tuple, List
from src.privacy.patterns import PHONE_RE, EMAIL_RE, AADHAAR_RE, MRN_RE


def mask_pattern(text: str, regex, label: str):
    flags = []
    def _repl(m):
        flags.append(f"PII detected: {label}")
        return f"[{label} REDACTED]"
    new_text = regex.sub(_repl, text)
    return new_text, flags


def mask_pii(note: str) -> Tuple[str, List[str]]:
    flags = []
    masked = note
    for regex, label in [(PHONE_RE, "PHONE"), (EMAIL_RE, "EMAIL"), (AADHAAR_RE, "AADHAAR"), (MRN_RE, "MRN")]:
        masked, new_flags = mask_pattern(masked, regex, label)
        flags.extend(new_flags)
    # unique
    flags = list(dict.fromkeys(flags))
    return masked, flags
