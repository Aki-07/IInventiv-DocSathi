"""LLM client for the legacy openai SDK (v0.28.x with ChatCompletion).

This is a simplified client that works with the currently-installed openai==0.28.0.
It handles extraction and repair of JSON outputs from the LLM.
"""
import json
from typing import Dict, Any
import re

import openai

from src.llm.prompts import EXTRACTION_PROMPT, REPAIR_PROMPT
from src.llm.retry import retry
from src.utils.config import get_config
from src.utils.logging import get_logger

logger = get_logger()


class LLMClientError(Exception):
    pass


class LLMClient:
    """LLM client using legacy openai (v0.28.x) ChatCompletion API."""

    def __init__(self, model: str = None, timeout: int = 30):
        cfg = get_config()
        self.api_key = cfg.api_key
        self.base_url = cfg.base_url
        self.model = model or cfg.model
        self.timeout = timeout

        if not self.api_key:
            raise LLMClientError("OPENAI_API_KEY missing. Set it in environment to enable LLM calls.")

        # Validate base URL early
        if self.base_url:
            if not (self.base_url.startswith("http://") or self.base_url.startswith("https://")):
                raise LLMClientError(
                    "OPENAI_BASE_URL is set but does not include a protocol (http:// or https://).\n"
                    f"Current value: {self.base_url!r}\n"
                    "Set it to a full URL such as 'https://api.openai.com/v1' or unset it to use the default official endpoint."
                )

        # Configure the legacy openai module
        openai.api_key = self.api_key
        if self.base_url:
            openai.api_base = self.base_url

    @retry(max_attempts=3)
    def extract_structured(self, note_text: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = EXTRACTION_PROMPT.format(note_text=note_text)
        try:
            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                top_p=1.0,
                timeout=self.timeout,
            )
            content = resp.choices[0].message.content
            logger.info("LLM raw response captured")
        except Exception as e:
            logger.exception("LLM extraction failed")
            raise LLMClientError(str(e))

        try:
            parsed = self._extract_json_block(content)
            if parsed is None:
                raise ValueError("No valid JSON found in response")
            return json.loads(parsed)
        except Exception:
            # attempt one repair pass via the LLM repair prompt
            repaired = self.repair_json(note_text, content, options=options)
            return repaired

    @retry(max_attempts=2)
    def repair_json(self, note_text: str, bad_json: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = REPAIR_PROMPT.format(bad_json=bad_json)
        try:
            # Omit temperature to avoid model-specific restrictions
            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                top_p=1.0,
                timeout=self.timeout,
            )
            content = resp.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.exception("LLM repair failed")
            raise LLMClientError(str(e))

    def _extract_json_block(self, text: str):
        """Try to extract a JSON substring from free text.
        1. Check for ```json ... ``` or ``` ... ``` fences
        2. Find largest {...} or [...] block
        3. Return the substring or None
        """
        if not text:
            return None
        # fenced code blocks
        m = re.search(r"```(?:json\s*)?(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # try to find the first { ... } block that is balanced
        starts = [i for i, ch in enumerate(text) if ch == '{']
        ends = [i for i, ch in enumerate(text) if ch == '}']
        if starts and ends:
            for s in starts:
                for e in reversed(ends):
                    if e > s:
                        candidate = text[s : e + 1]
                        if ':' in candidate:
                            return candidate.strip()
        # try array style
        starts = [i for i, ch in enumerate(text) if ch == '[']
        ends = [i for i, ch in enumerate(text) if ch == ']']
        if starts and ends:
            for s in starts:
                for e in reversed(ends):
                    if e > s:
                        candidate = text[s : e + 1]
                        if '{' in candidate or ':' in candidate:
                            return candidate.strip()
        return None
