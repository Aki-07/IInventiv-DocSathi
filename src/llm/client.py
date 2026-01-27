import json
from typing import Dict, Any, Optional

import requests

try:
    import openai
except Exception:  # pragma: no cover - optional dependency for local Ollama use
    openai = None

from src.llm.prompts import EXTRACTION_PROMPT, REPAIR_PROMPT, QUESTIONS_PROMPT
from src.llm.retry import retry
from src.utils.config import get_config
from src.utils.logging import get_logger

logger = get_logger()


class LLMClientError(Exception):
    pass


class LLMClient:
    def __init__(
        self,
        model: Optional[str] = None,
        timeout: int = 30,
        provider: Optional[str] = None,
        base_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
    ):
        cfg = get_config()
        self.api_key = cfg.api_key
        self.base_url = base_url or cfg.base_url
        self.model = model or cfg.model
        self.timeout = timeout
        self.provider = (provider or cfg.provider or "openai").lower()
        self.ollama_model = ollama_model or cfg.ollama_model
        self.ollama_base_url = (ollama_base_url or cfg.ollama_base_url or "http://localhost:11434").rstrip("/")
        self._openai_client = None

        if self.provider == "openai":
            if not self.api_key:
                raise LLMClientError("OPENAI_API_KEY missing. Set it in environment to enable OpenAI calls.")
            if openai is None:
                raise LLMClientError("openai package not installed. Install it or switch to Ollama.")

            # Support both legacy and v1+ OpenAI SDKs.
            if hasattr(openai, "ChatCompletion"):
                openai.api_key = self.api_key
                if self.base_url:
                    openai.api_base = self.base_url
            else:
                from openai import OpenAI  # type: ignore

                self._openai_client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        elif self.provider == "ollama":
            if not self.ollama_model:
                raise LLMClientError("OLLAMA_MODEL missing. Set it in environment to enable Ollama calls.")
        else:
            raise LLMClientError(f"Unknown LLM provider: {self.provider}")

    def _openai_chat(self, prompt: str, temperature: float) -> str:
        if self._openai_client is None:
            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                # temperature=temperature,
                timeout=self.timeout,
            )
            return resp.choices[0].message.content

        resp = self._openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            # temperature=temperature,
            timeout=self.timeout,
        )
        return resp.choices[0].message.content

    def _extract_json_candidate(self, text: str) -> Optional[str]:
        if not text:
            return None
        # Prefer fenced json blocks if present.
        if "```" in text:
            parts = text.split("```")
            for i in range(len(parts) - 1):
                fence_header = parts[i].strip().lower()
                block = parts[i + 1]
                if "json" in fence_header or fence_header == "":
                    candidate = block.strip()
                    if candidate:
                        return candidate
        # Fallback to first {...} span.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1].strip()
        return None

    def _safe_json_load(self, content: str) -> Dict[str, Any]:
        if content is None or not str(content).strip():
            raise LLMClientError("LLM returned empty response.")
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
            raise LLMClientError("LLM response JSON is not an object.")
        except Exception:
            candidate = self._extract_json_candidate(str(content))
            if candidate:
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass
        raise LLMClientError("LLM response is not valid JSON.")

    def _ollama_call(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.ollama_base_url}/{endpoint.lstrip('/')}"
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
        except Exception as e:
            raise LLMClientError(f"Ollama request failed: {e}")
        if resp.status_code >= 400:
            raise LLMClientError(f"Ollama error {resp.status_code}: {resp.text}")
        return resp.json()

    def _ollama_chat(self, prompt: str) -> str:
        data = self._ollama_call(
            "api/chat",
            {
                "model": self.ollama_model,
                "messages": [
                    {"role": "system", "content": "Return ONLY valid JSON. No markdown, no commentary."},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
            },
        )
        content = (data.get("message") or {}).get("content")
        if content and str(content).strip():
            return content

        data = self._ollama_call(
            "api/generate",
            {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
            },
        )
        content = data.get("response")
        if not content or not str(content).strip():
            raise LLMClientError("Ollama response missing content.")
        return content

    @retry(max_attempts=3)
    def extract_structured(self, note_text: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = EXTRACTION_PROMPT.format(note_text=note_text)
        try:
            if self.provider == "openai":
                content = self._openai_chat(prompt, temperature=0.1)
            else:
                content = self._ollama_chat(prompt)
        except Exception as e:
            logger.exception("LLM extraction failed")
            raise LLMClientError(str(e))

        try:
            return self._safe_json_load(content)
        except Exception:
            return self.repair_json(note_text, content, options=options)

    @retry(max_attempts=2)
    def repair_json(self, note_text: str, bad_json: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = REPAIR_PROMPT.format(bad_json=bad_json)
        try:
            if self.provider == "openai":
                content = self._openai_chat(prompt, temperature=0.0)
            else:
                content = self._ollama_chat(prompt)
            return self._safe_json_load(content)
        except Exception as e:
            logger.exception("LLM repair failed")
            raise LLMClientError(str(e))

    @retry(max_attempts=2)
    def generate_followup_questions(
        self,
        note_text: str,
        structured_json: Dict[str, Any],
        flags: Optional[list] = None,
    ) -> Dict[str, Any]:
        prompt = QUESTIONS_PROMPT.format(
            note_text=note_text,
            structured_json=json.dumps(structured_json, ensure_ascii=False),
            flags_json=json.dumps(flags or [], ensure_ascii=False),
        )
        try:
            if self.provider == "openai":
                content = self._openai_chat(prompt, temperature=0.2)
            else:
                content = self._ollama_chat(prompt)
            data = self._safe_json_load(content)
            if "questions" not in data or not isinstance(data.get("questions"), list):
                return {"questions": []}
            questions = [str(q).strip() for q in data.get("questions", []) if str(q).strip()]
            return {"questions": questions}
        except Exception as e:
            logger.exception("LLM follow-up questions failed")
            raise LLMClientError(str(e))
