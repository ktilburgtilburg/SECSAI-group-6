"""Request/reply (RPC) client for the prediction workers over RabbitMQ.

The rest of the backend only sees rpc_assess() and queue_is_up(). pika,
queue names, correlation ids and timeouts stay in this module.
"""

import json
import os
import time
import uuid

import pika
import pika.exceptions

from secsai_group_6.categories import Category

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
REQUEST_QUEUE = "assess_requests"
TIMEOUT_S = 2.0


class QueueError(Exception):
    """The prediction service could not give an answer."""


class QueueUnavailable(QueueError):
    """Cannot reach (or talk to) the broker."""


class QueueTimeout(QueueError):
    """No worker replied in time."""


class BadReply(QueueError):
    """A worker replied, but now with a valid verdict."""


def _connect(timeout: float) -> pika.BlockingConnection:
    params = pika.URLParameters(RABBITMQ_URL)
    params.socket_timeout = timeout
    params.stack_timeout = timeout
    params.connection_attempts = 1
    params.retry_delay = 0
    return pika.BlockingConnection(params)


def queue_is_up() -> bool:
    """For /health: can we open a connection right now?"""
    try:
        conn = _connect(timeout=1.0)
    except (pika.exceptions.AMQPError, OSError):
        return False
    conn.close()
    return True


def rpc_assess(url: str, timeout: float = TIMEOUT_S) -> tuple[dict, str | None]:
    """Ask a worker to assess `url`. Returns (verdict, worker_id).

    Raises QueueUnavailable, QueueTimeout or BadReply. Never returns a guess.
    """
    deadline = time.monotonic() + timeout  # one budget for connect + publish + wait
    correlation_id = str(uuid.uuid4())
    reply = None

    def on_reply(_channel, _method, props, body):
        nonlocal reply
        if props.correlation_id == correlation_id:  # ignore stray messages
            reply = body

    try:
        conn = _connect(timeout)
    except (pika.exceptions.AMQPError, OSError) as exc:
        raise QueueUnavailable("cannot connect to RabbitMQ") from exc

    try:
        channel = conn.channel()
        channel.queue_declare(queue=REQUEST_QUEUE)
        # Server-named, exclusive queue: deleted automatically when we disconnect.
        reply_queue = channel.queue_declare(queue="", exclusive=True).method.queue
        channel.basic_consume(
            queue=reply_queue, on_message_callback=on_reply, auto_ack=True
        )
        channel.basic_publish(
            exchange="",
            routing_key=REQUEST_QUEUE,
            body=json.dumps({"url": url}),
            properties=pika.BasicProperties(
                reply_to=reply_queue,
                correlation_id=correlation_id,
                content_type="application/json",
                expiration=str(
                    int(timeout * 1000)
                ),  # broker drops it if nobody picks it up
            ),
        )
        while reply is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise QueueTimeout(f"no reply within {timeout}s")
            conn.process_data_events(time_limit=remaining)
    except pika.exceptions.AMQPError as exc:
        raise QueueUnavailable("RabbitMQ error during request") from exc
    finally:
        if conn.is_open:
            conn.close()

    return _parse_reply(reply)


def _parse_reply(body: bytes) -> tuple[dict, str | None]:
    """Check the worker's reply at the process boundary before trusting it."""
    try:
        data = json.loads(body)
        is_malicious = data["is_malicious"]
        if not isinstance(is_malicious, bool):
            raise TypeError("is_malicious must be a bool")
        category = Category(data["category"])
        if is_malicious != (category is not Category.BENIGN):
            raise ValueError("is_malicious contradicts category")
        confidence = float(data["confidence"])
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence out of range")
        verdict = {
            "is_malicious": is_malicious,
            "category": category.value,
            "confidence": confidence,
            "explanations": [str(e) for e in data["explanations"]],
        }
        return verdict, data.get("worker_id")
    except (ValueError, KeyError, TypeError) as exc:  # include JSONDecodeError
        raise BadReply("worker reply does not match the contract") from exc
