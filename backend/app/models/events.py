from enum import Enum
from typing import Any

from pydantic import BaseModel


class EventType(str, Enum):
    RUN_STARTED = "run_started"
    FACT_PATTERN = "fact_pattern"
    WAVE1_STARTED = "wave1_started"
    STATUTE_PROGRESS = "statute_progress"
    STATUTE_FOUND = "statute_found"
    WAVE1_COMPLETE = "wave1_complete"
    WAVE2_STARTED = "wave2_started"
    CASELAW_PROGRESS = "caselaw_progress"
    CASELAW_FOUND = "caselaw_found"
    WAVE2_COMPLETE = "wave2_complete"
    RUN_COMPLETE = "run_complete"
    ERROR = "error"


class StreamEvent(BaseModel):
    type: EventType
    payload: dict[str, Any] = {}
