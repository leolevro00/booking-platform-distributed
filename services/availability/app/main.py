import json
import os
import time
import pika

from shared.contracts.events import new_event
from shared.messaging.rabbitmq import publish_event

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EVENTS_EXCHANGE = os.getenv("EVENTS_EXCHANGE", "events")


def try_reserve(payload: dict) -> bool:
    # regola semplice per test:
    # se facility_id termina con 'x' allora "non disponibile"
    facility_id = payload.get("facility_id", "")
    return not facility_id.endswith("x")


def on_message(ch, method, properties, body: bytes):
    event = json.loads(body.decode("utf-8"))
    etype = event.get("type")
    print(f"📥 availability received: {etype}", flush=True)


    if etype != "booking.created":
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    payload = event["payload"]
    booking_id = payload["booking_id"]

    # simuliamo lavoro
    time.sleep(0.5)

    if try_reserve(payload):
        out = new_event(
            event_type="slot.reserved",
            correlation_id=booking_id,
            payload={
                "booking_id": booking_id,
                "resource_id": payload["facility_id"],
                "date": payload["date"],
                "time": payload["time"],
            },
        )
        publish_event(RABBITMQ_URL, EVENTS_EXCHANGE, "slot.reserved", out.model_dump())
        print(f"✅ slot reserved for booking {booking_id}", flush=True)

    else:
        out = new_event(
            event_type="slot.reserve_failed",
            correlation_id=booking_id,
            payload={
                "booking_id": booking_id,
                "reason": "resource_unavailable",
            },
        )
        publish_event(RABBITMQ_URL, EVENTS_EXCHANGE, "slot.reserve_failed", out.model_dump())
        print(f"❌ slot reserve failed for booking {booking_id}", flush=True)


    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    params = pika.URLParameters(RABBITMQ_URL)

    # retry loop: RabbitMQ potrebbe non essere pronto subito
    while True:
        try:
            connection = pika.BlockingConnection(params)
            break
        except pika.exceptions.AMQPConnectionError as e:
            print("⏳ RabbitMQ non pronto, ritento tra 2s...")
            time.sleep(2)

    channel = connection.channel()


    channel.exchange_declare(exchange=EVENTS_EXCHANGE, exchange_type="topic", durable=True)

    queue_name = "availability.booking_created"
    channel.queue_declare(queue=queue_name, durable=True)
    channel.queue_bind(exchange=EVENTS_EXCHANGE, queue=queue_name, routing_key="booking.created")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=on_message)

    print("📡 availability-service listening on booking.created ...", flush=True)

    print(
    f"📡 availability listening on exchange='{EVENTS_EXCHANGE}' "
    f"queue='availability.booking_created'",
    flush=True
    )

    channel.start_consuming()


if __name__ == "__main__":
    main()
