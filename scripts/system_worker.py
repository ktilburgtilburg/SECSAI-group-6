"""Queue-contract worker; stub by default, PREDICTOR=model for real artifacts."""

import json
import os
import socket
import time

import pika

if os.environ.get("PREDICTOR", "stub") == "model":
    from secsai_group_6.ml.predict import predict
else:
    from secsai_group_6.backend.stub_model import predict


def _connect(max_tries: int = 30, delay: float = 1.0) -> pika.BlockingConnection:
    params = pika.URLParameters(os.environ["RABBITMQ_URL"])
    for attempt in range(max_tries):
        try:
            return pika.BlockingConnection(params)
        except (pika.exceptions.AMQPError, OSError):
            if attempt == max_tries - 1:
                raise
            time.sleep(delay)
    raise RuntimeError("Could not connect to RabbitMQ")


def serve():
    conn = _connect()
    channel = conn.channel()
    channel.queue_declare(queue="assess_requests")
    channel.basic_qos(prefetch_count=1)

    def handle(ch, method, props, body):
        print(
            json.dumps(
                {
                    "event": "received",
                    "id": props.correlation_id,
                    "redelivered": method.redelivered,
                }
            ),
            flush=True,
        )
        time.sleep(float(os.environ.get("WORKER_DELAY", "0")))
        try:
            reply = predict(json.loads(body)["url"])
            reply["worker_id"] = socket.gethostname()
        except Exception as exc:  # noqa: BLE001 - return model failures through the queue contract
            reply = {"error": str(exc)}
        ch.basic_publish(
            exchange="",
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=json.dumps(reply),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue="assess_requests", on_message_callback=handle)
    channel.start_consuming()


if __name__ == "__main__":
    serve()
