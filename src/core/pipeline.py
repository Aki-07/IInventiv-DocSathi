from typing import Tuple, Dict, Any
from src.privacy.pii import mask_pii
from src.llm.client import LLMClient, LLMClientError
from src.core.schemas import StructuredNote
from src.validate.normalizers import normalize_structured
from src.validate.validators import run_validations
from src.export.fhir_bundle import build_fhir_bundle
from src.utils.logging import get_logger

logger = get_logger()


def run_pipeline(note_text: str, options: dict = None, llm_client: LLMClient = None) -> Dict[str, Any]:
    options = options or {}
    flags = []

    # 1. PII mask
    masked_note, pii_flags = mask_pii(note_text)
    if pii_flags:
        flags.extend(pii_flags)

    # 2. LLM extract
    if llm_client is None:
        llm_client = LLMClient(model=options.get("model"))

    try:
        llm_result = llm_client.extract_structured(masked_note, options=options)
    except LLMClientError as e:
        logger.exception("LLM client error")
        raise

    raw_llm = llm_result

    # 3. Pydantic validate -> model
    try:
        structured = StructuredNote(**raw_llm)
    except Exception as e:
        # Attempt repair
        try:
            repaired = llm_client.repair_json(masked_note, str(raw_llm), options=options)
            structured = StructuredNote(**repaired)
        except Exception:
            logger.exception("Failed to parse structured output")
            raise ValueError("Unable to parse LLM output into structured JSON")

    # 4. Deterministic normalize + validate -> add flags
    normalize_structured(structured)
    vflags = run_validations(structured, note_text)
    for f in vflags:
        if f not in flags:
            flags.append(f)

    structured.flags = flags

    # 5. Create FHIR bundle
    bundle = build_fhir_bundle(structured)

    return {"structured": structured, "bundle": bundle, "flags": flags, "masked_note": masked_note, "raw_llm_json": raw_llm}
