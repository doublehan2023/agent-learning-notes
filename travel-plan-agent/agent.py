"""Core TravelPlanAgent implementation."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = PROJECT_DIR / "prompts" / "system.md"


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


class TravelPlanAgent:
    """A minimal LLM-powered travel planner without external actions."""

    def __init__(self) -> None:
        load_dotenv(PROJECT_DIR / ".env")
        api_key = os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_MODEL_ID")
        base_url = os.getenv("LLM_BASE_URL")

        if not api_key or not model:
            raise ValueError(
                "Set LLM_API_KEY and LLM_MODEL_ID in .env. "
                "Start by copying .env.example to .env."
            )

        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url or None)
        self.messages = [{"role": "system", "content": load_system_prompt()}]

    def respond(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.3,
        )
        content = response.choices[0].message.content or ""
        self.messages.append({"role": "assistant", "content": content})
        return content
