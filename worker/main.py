import json
import os
import socket
import time

import pika

from secsai_group_6.backend.validation import InvalidInput, clean_url
from secsai_group_6.ml.predict import _load, predict

QUEUE_NAME = "assess_requests"
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
WORKER_ID = socket.gethostname()

def connect_with_retry() -> pika.BlockingConnection:
    """Retry connecting until the RabbitMQ broker is ready."""
    while True:
        try:
            params = pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600)
            return pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            print(f"[{WORKER_ID}] Waiting for RabbitMQ at {RABBITMQ_HOST}...")
            time.sleep(2)

def parse_url(body: bytes) -> str:
    """Accept either JSON {"url": "..."} or a raw URL string, then validate."""
    raw = body.decode("utf-8").strip()
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return clean_url(payload.get("url"))
    except json.JSONDecodeError:
        pass
    return clean_url(raw)

def on_request(ch, method, properties, body):
    try:
        url = parse_url(body)
        print(f"[{WORKER_ID}] Assessing: {url}")
        response = predict(url)
    except InvalidInput as exc:
        response = {"error": str(exc)}
    except Exception as exc:
        print(f"[{WORKER_ID}] Prediction error: {exc}")
        response = {"error": "Prediction failed"}

    response["worker_id"] = WORKER_ID

    if properties.reply_to:
        ch.basic_publish(
            exchange="",
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id,
                content_type="application/json",
            ),
            body=json.dumps(response),
        )

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    print(f"[{WORKER_ID}] Loading model into memory...")
    _load()
    print(f"[{WORKER_ID}] Model ready.")

    connection = connect_with_retry()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_request)
    print(f"[{WORKER_ID}] Listening on '{QUEUE_NAME}'...")
    channel.start_consuming()

if __name__ == "__main__":
    main()