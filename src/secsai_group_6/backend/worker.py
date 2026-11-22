"""Background ML worker consuming URL assessment jobs from RabbitMQ."""

import json
import logging
import os
import time

import pika
import pika.exceptions

from secsai_group_6.ml.predict import predict

logger = logging.getLogger(__name__)

QUEUE_NAME = os.environ.get(
    "REQUEST_QUEUE", os.environ.get("QUEUE_NAME", "assess_requests")
)


def _get_pika_params():
    """Resolve RabbitMQ connection parameters from RABBITMQ_URL or HOST/PORT."""
    url = os.environ.get("RABBITMQ_URL")
    if url:
        return pika.URLParameters(url)
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    return pika.ConnectionParameters(
        host=host,
        port=port,
        heartbeat=10,
        blocked_connection_timeout=30,
    )


def retry_connection(max_tries: int = 30, delay: float = 2):
    """Attempt to connect to RabbitMQ with fixed-delay retries."""
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
    """Score a queued URL and publish the verdict back to the caller's reply queue."""
    try:
        data = json.loads(body)
        url = data.get("url")
        verdict = predict(url)
    except Exception as exc:
        logger.exception("Worker prediction failed")
        verdict = {
            "error": "Prediction failed",
            "is_malicious": False,
            "category": "unknown",
            "confidence": 0.0,
            "explanations": ["Model error: " + str(exc)],
        }

    ch.basic_publish(
        exchange="",
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=json.dumps(verdict),
    )

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    """Warm up the classifier and run an auto-reconnecting RabbitMQ consumer loop."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    logger.info("Warming up ML model...")
    try:
        predict("https://example.com/")
        logger.info("Model warmed up successfully.")
    except Exception as exc:  # noqa: BLE001 - continue starting even if warm-up fails
        logger.warning("Model warm-up notice: %s", exc)

    while True:
        try:
            connection = retry_connection()
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_request)
            logger.info("Worker ready. Waiting for requests on '%s'...", QUEUE_NAME)
            channel.start_consuming()
        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.StreamLostError,
            pika.exceptions.ChannelClosed,
            pika.exceptions.ConnectionClosed,
        ):
            logger.warning("RabbitMQ connection lost. Reconnecting in 3s...")
            time.sleep(3)
        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
            break


if __name__ == "__main__":
    main()
