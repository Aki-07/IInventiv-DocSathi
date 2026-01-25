EXTRACTION_PROMPT = '''
You are an assistant that extracts structured JSON only from a free-text outpatient note.
Return JSON only and strictly follow the schema keys. Do NOT add or invent any facts.
If a field cannot be found, set it to null or empty list as appropriate.

Schema keys expected (top-level):
- complaints: list of short strings or null
- duration: string or null
- vitals: object with bp_systolic, bp_diastolic, hr, spo2, temp (use null if absent)
- findings: string or null
- diagnosis: list of strings or null (ONLY include if explicitly documented in note)
- medications: list of objects {name,dose,route,frequency,duration,prn}
- tests: list of strings or null
- advice: string or null
- follow_up: string or null
- flags: list (LLM may leave empty; deterministic checks will add flags)

HARD RULES:
1) Never infer diagnosis. Only record diagnosis/problems if explicitly written in the note. If not present, set diagnosis to null and do NOT infer.
2) Never invent missing values. If a field is absent, set null. Do not guess units, durations, doses, etc.
3) Output valid JSON only. Do not include commentary, explanation, or markdown. Strict JSON only.

Provide evidence fields only as short text when present (e.g., evidence_text and confidence). Keep confidence one of: high/medium/low when possible.

Now extract from the following NOTE and output JSON only:
"""
{note_text}
"""
'''

REPAIR_PROMPT = '''
You are given a broken or partially incorrect JSON string. Your job: return valid JSON that matches the expected schema keys for the structured note, do not add clinical facts that are not present in the original broken JSON, only correct formatting, ensure all required keys are present (use null or empty lists where appropriate), and do not add new factual content.

Return JSON only.

Broken JSON:
{bad_json}
'''
