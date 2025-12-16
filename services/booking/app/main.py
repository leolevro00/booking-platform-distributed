import os
from uuid import uuid4
from fastapi import FastAPI
from pydantic import BaseModel

from shared.contracts.events import new_event
from shared.messaging.rabbitmq import publish_event

app = FastAPI(title="booking-service", version="0.2.0")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EVENTS_EXCHANGE = os.getenv("EVENTS_EXCHANGE", "events")

class CreateBookingRequest(BaseModel):
    facility_id: str
    date: str        # es: "2025-12-20"
    time: str        # es: "18:00"
    user_id: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "booking"}

@app.post("/bookings")
def create_booking(req: CreateBookingRequest):
    booking_id = str(uuid4())

    event = new_event(
        event_type="booking.created",
        correlation_id=booking_id,
        payload={
            "booking_id": booking_id,
            "facility_id": req.facility_id,
            "date": req.date,
            "time": req.time,
            "user_id": req.user_id,
        },
    )

    publish_event(
        rabbitmq_url=RABBITMQ_URL,
        exchange=EVENTS_EXCHANGE,
        routing_key="booking.created",
        message=event.model_dump(),
    )

    return {"booking_id": booking_id, "status": "PENDING"}
