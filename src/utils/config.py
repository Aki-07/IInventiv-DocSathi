import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    api_key: str
    base_url: str
    model: str
    has_api_key: bool


def get_config() -> Config:
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or None
    model = os.environ.get("OPENAI_MODEL") or "gpt-5-mini"
    return Config(api_key=api_key, base_url=base_url, model=model, has_api_key=bool(api_key))
