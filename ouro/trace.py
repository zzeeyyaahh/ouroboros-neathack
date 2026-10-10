from __future__ import annotations

from .config import settings


def init_tracing(run_id: str):
    if not settings.neatlogs_api_key:
        return None
    import neatlogs

    return neatlogs.init(api_key=settings.neatlogs_api_key, tags=[settings.workflow, f"run:{run_id}"])


def shutdown_tracing(tracker) -> None:
    if tracker is not None:
        tracker.shutdown()
