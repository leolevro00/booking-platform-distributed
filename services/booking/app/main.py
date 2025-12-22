import os
import threading, json, pika
import time

from uuid import uuid4
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException

from shared.contracts.events import new_event
from shared.messaging.rabbitmq import publish_event

app = FastAPI(title="booking-service", version="0.2.0")

BOOKINGS = {}
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

    BOOKINGS[booking_id] = {
    "booking_id": booking_id,
    "status": "PENDING",
    "facility_id": req.facility_id,
    "date": req.date,
    "time": req.time,
    "user_id": req.user_id,
    }


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

@app.get("/bookings/{booking_id}")
def get_booking(booking_id: str):
    if booking_id not in BOOKINGS:
        raise HTTPException(status_code=404, detail="booking not found")
    return BOOKINGS[booking_id]


def start_slot_consumer():
    params = pika.URLParameters(RABBITMQ_URL)
    
    while True:
        try:
            connection = pika.BlockingConnection(params)
            break
        except pika.exceptions.AMQPConnectionError as e:
            print(f"⏳ booking: RabbitMQ non pronto ({e}), ritento tra 2s... URL={RABBITMQ_URL}", flush=True)
            time.sleep(2)

    channel = connection.channel()

    channel.exchange_declare(exchange=EVENTS_EXCHANGE, exchange_type="topic", durable=True)

    q = "booking.slot_events"
    channel.queue_declare(queue=q, durable=True)
    channel.queue_bind(exchange=EVENTS_EXCHANGE, queue=q, routing_key="slot.reserved")
    channel.queue_bind(exchange=EVENTS_EXCHANGE, queue=q, routing_key="slot.reserve_failed")

    def on_message(ch, method, properties, body: bytes):
        event = json.loads(body.decode("utf-8"))
        etype = event.get("type")
        payload = event.get("payload", {})
        booking_id = payload.get("booking_id")

        print(f"📥 booking received: {etype} for {booking_id}", flush=True)

        if booking_id in BOOKINGS:
            if etype == "slot.reserved":
                BOOKINGS[booking_id]["status"] = "CONFIRMED"
                BOOKINGS[booking_id]["reserved_slot"] = {
                    "resource_id": payload.get("resource_id"),
                    "date": payload.get("date"),
                    "time": payload.get("time"),
                }
            elif etype == "slot.reserve_failed":
                BOOKINGS[booking_id]["status"] = "CANCELLED"
                BOOKINGS[booking_id]["cancel_reason"] = payload.get("reason", "unknown")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=q, on_message_callback=on_message)
    print("📡 booking listening on slot.* ...", flush=True)
    channel.start_consuming()


@app.on_event("startup")
def startup():
    t = threading.Thread(target=start_slot_consumer, daemon=True)
    t.start()