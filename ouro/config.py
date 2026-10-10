from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _flag(name: str) -> bool:
    return os.environ.get(name, "0").strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    neatlogs_api_key: str
    crustdata_api_key: str
    model: str
    workflow: str
    fault_inject: bool
    mock_mode: bool

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            neatlogs_api_key=os.environ.get("NEATLOGS_API_KEY", ""),
            crustdata_api_key=os.environ.get("CRUSTDATA_API_KEY", "") or os.environ.get("CRUSTDATA_API_TOKEN", ""),
            model=os.environ.get("OURO_MODEL", "gpt-4o"),
            workflow=os.environ.get("OURO_WORKFLOW", "ouroboros-worker"),
            fault_inject=_flag("OURO_FAULT_INJECT"),
            mock_mode=_flag("OURO_MOCK"),
        )


settings = Settings.from_env()
