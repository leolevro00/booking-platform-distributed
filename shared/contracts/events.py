from pydantic import BaseModel
from datetime import datetime, timezone
from uuid import uuid4

class EventEnvelope(BaseModel):
    event_id: str
    type: str
    timestamp: str
    correlation_id: str
    payload: dict

def new_event(event_type: str, correlation_id: str, payload: dict) -> EventEnvelope:
    return EventEnvelope(
        event_id=str(uuid4()),
        type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        correlation_id=correlation_id,
        payload=payload,
    )
