import json
import logging
import os
import time

import pika
import pika.exceptions

from secsai_group_6.ml.predict import predict

QUEUE_NAME = os.environ.get(
    "REQUEST_QUEUE", os.environ.get("QUEUE_NAME", "assess_requests")
)


def _get_pika_params():
    url = os.environ.get("RABBITMQ_URL")
    if url:
        return pika.URLParameters(url)
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", 5672))
    return pika.ConnectionParameters(
        host=host,
        port=port,
        heartbeat=10,
        blocked_connection_timeout=30,
    )


def retry_connection(max_tries=30, delay=2):
    params = _get_pika_params()

    for attempt in range(max_tries):
        try:
            return pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            if attempt < max_tries - 1:
                time.sleep(delay)
            else:
                raise


def on_request(ch, method, props, body):
    try:
        data = json.loads(body)
        url = data.get("url")
        verdict = predict(url)
    except Exception as e:
        verdict = {
            "error": "Prediction failed",
            "is_malicious": False,
            "category": "unknown",
            "confidence": 0.0,
            "explanations": ["Model error: " + str(e)],
        }

    ch.basic_publish(
        exchange="",
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=json.dumps(verdict),
    )

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    print("[*] Warming up ML model...", flush=True)
    try:
        predict("https://example.com/")
        print("[*] Model warmed up successfully.", flush=True)
    except Exception as e:
        print(f"[*] Model warm-up notice: {e}", flush=True)

    while True:
        try:
            connection = retry_connection()
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_request)
            print(
                f"[*] Worker ready. Waiting for requests on '{QUEUE_NAME}'...",
                flush=True,
            )
            channel.start_consuming()
        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.StreamLostError,
            pika.exceptions.ChannelClosed,
            pika.exceptions.ConnectionClosed,
        ):
            print(
                "[*] RabbitMQ connection lost. Reconnecting in 3s...",
                flush=True,
            )
            time.sleep(3)
        except KeyboardInterrupt:
            print("[*] Worker stopped by user.", flush=True)
            break


if __name__ == "__main__":
    main()
