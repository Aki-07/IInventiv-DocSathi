import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    api_key: Optional[str]
    base_url: Optional[str]
    model: str
    has_api_key: bool
    provider: str
    ollama_model: Optional[str]
    ollama_base_url: str


def get_config() -> Config:
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or None
    model = os.environ.get("OPENAI_MODEL") or "gpt-5-mini"
    ollama_model = os.environ.get("OLLAMA_MODEL") or None
    ollama_base_url = os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434"

    provider_env = os.environ.get("LLM_PROVIDER")
    if provider_env:
        provider = provider_env.strip().lower()
    else:
        if api_key:
            provider = "openai"
        elif ollama_model or os.environ.get("OLLAMA_BASE_URL"):
            provider = "ollama"
        else:
            provider = "openai"

    return Config(
        api_key=api_key,
        base_url=base_url,
        model=model,
        has_api_key=bool(api_key),
        provider=provider,
        ollama_model=ollama_model,
        ollama_base_url=ollama_base_url,
    )
