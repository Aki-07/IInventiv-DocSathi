import os
import json
from typing import Dict, Any
import openai
from src.llm.prompts import EXTRACTION_PROMPT, REPAIR_PROMPT
from src.llm.retry import retry
from src.utils.config import get_config
from src.utils.logging import get_logger

logger = get_logger()


class LLMClientError(Exception):
    pass


class LLMClient:
    def __init__(self, model: str = None, timeout: int = 30):
        cfg = get_config()
        self.api_key = cfg.api_key
        self.base_url = cfg.base_url
        self.model = model or cfg.model
        self.timeout = timeout

        if not self.api_key:
            raise LLMClientError("OPENAI_API_KEY missing. Set it in environment to enable LLM calls.")

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
                temperature=0.1,
                timeout=self.timeout,
            )
            content = resp.choices[0].message.content
        except Exception as e:
            logger.exception("LLM extraction failed")
            raise LLMClientError(str(e))

        try:
            parsed = json.loads(content)
        except Exception:
            # attempt one repair pass via the LLM repair prompt
            repaired = self.repair_json(note_text, content, options=options)
            return repaired

        return parsed

    @retry(max_attempts=2)
    def repair_json(self, note_text: str, bad_json: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = REPAIR_PROMPT.format(bad_json=bad_json)
        try:
            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                timeout=self.timeout,
            )
            content = resp.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.exception("LLM repair failed")
            raise LLMClientError(str(e))
