"""
Centralized configuration.

Loads environment variables once and exposes get_model_client(), the single
factory every agent uses to obtain an LLM client. Centralizing this means
switching providers or models is a one-line .env change, not a multi-file edit.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model_name: str


def _load_settings() -> Settings:
    api_key = os.getenv("OPENAI_API_KEY", "ollama")
    base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    model_name = os.getenv("MODEL_NAME", "qwen3:4b")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    return Settings(api_key=api_key, base_url=base_url, model_name=model_name)


_settings = _load_settings()


# app/config.py — updated get_model_client()

def get_model_client() -> OpenAIChatCompletionClient:
    return OpenAIChatCompletionClient(
        model=_settings.model_name,
        api_key=_settings.api_key,
        base_url=_settings.base_url,
        max_retries=5,       # retries transient errors like 429s with backoff
        timeout=400,          # avoid hanging indefinitely on a slow free-tier response
        model_info={
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "family": "unknown",
            "structured_output": False,
        },
        default_headers={
            "HTTP-Referer": "https://github.com/your-username/ai-product-strategy-workspace",
            "X-Title": "AI Product Strategy Workspace",
        },
    )
