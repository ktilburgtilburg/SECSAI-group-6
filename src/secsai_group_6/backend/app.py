import json
import logging
import os
import time
import uuid
from pathlib import Path

import pika
import pika.exceptions
from flask import Flask, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from secsai_group_6.backend.db import StorageError, log_request, save_feedback
from secsai_group_6.backend.rpc_client import (
    BadReply,
    QueueTimeout,
    QueueUnavailable,
)
from secsai_group_6.backend.validation import (
    InvalidInput,
    clean_category,
    clean_url,
    json_object,
    redact_url,
)

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"

app = Flask(__name__)
CORS(app)
app.config.setdefault(
    "DB_PATH", os.environ.get("DB_PATH", Path(__file__).with_name("feedback.db"))
)


def _get_pika_params(timeout: float = 1.0):
    """Resolve RabbitMQ connection parameters from RABBITMQ_URL or HOST/PORT."""
    url = os.environ.get("RABBITMQ_URL")
    if url:
        params = pika.URLParameters(url)
    else:
        host = os.environ.get("RABBITMQ_HOST", "localhost")
        port = int(os.environ.get("RABBITMQ_PORT", "5672"))
        params = pika.ConnectionParameters(host=host, port=port)
    params.socket_timeout = timeout
    params.connection_attempts = 1
    params.retry_delay = 0
    return params


def queue_is_up() -> bool:
    """Return True if a short-lived RabbitMQ connection succeeds."""
    try:
        conn = pika.BlockingConnection(_get_pika_params(timeout=1.0))
        conn.close()
        return True
    except (pika.exceptions.AMQPError, OSError):
        return False


def error(message: str, status: int) -> tuple[dict, int]:
    """Build the error response used by every failure path."""
    return ({"error": message}, status)


@app.errorhandler(InvalidInput)
def handle_invalid_input(exc: InvalidInput):
    return error(str(exc), 400)


@app.errorhandler(StorageError)
def handle_storage_error(exc: StorageError):
    logger.error("Feedback storage failed", exc_info=exc)
    return error("Could not save feedback", 500)


@app.errorhandler(HTTPException)
def handle_http_exception(exc: HTTPException):
    return error(exc.description or exc.name, exc.code or 500)


@app.get("/health")
def health():
    """Report API and RabbitMQ broker health status."""
    queue_ok = queue_is_up()
    return {
        "status": "ok" if queue_ok else "degraded",
        "queue": "ok" if queue_ok else "down",
    }


def predict_rpc(url: str, timeout: float = 10.0) -> dict:
    """Send a URL assessment job over RabbitMQ and wait for the worker reply."""
    conn = pika.BlockingConnection(_get_pika_params(timeout=timeout))
    try:
        channel = conn.channel()

        queue_name = os.environ.get(
            "REQUEST_QUEUE", os.environ.get("QUEUE_NAME", "assess_requests")
        )
        channel.queue_declare(queue=queue_name)

        result = channel.queue_declare(queue="", exclusive=True, auto_delete=True)
        reply_queue = result.method.queue

        response = None
        corr_id = str(uuid.uuid4())

        def on_reply(ch, method, props, body):
            nonlocal response
            if props.correlation_id == corr_id:
                response = json.loads(body)

        channel.basic_consume(
            queue=reply_queue,
            on_message_callback=on_reply,
            auto_ack=True,
        )

        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            properties=pika.BasicProperties(
                reply_to=reply_queue,
                correlation_id=corr_id,
            ),
            body=json.dumps({"url": url}),
        )

        start = time.time()
        while response is None and conn.is_open:
            conn.process_data_events(time_limit=0.2)
            if time.time() - start > timeout:
                break
    finally:
        if conn.is_open:
            conn.close()

    if response is None:
        raise QueueTimeout("Prediction worker timed out")

    return response


@app.post(f"{API_PREFIX}/assess")
def assess():
    """Validate a URL and dispatch it to a background worker for threat assessment."""
    started = time.perf_counter()
    body = json_object(request.get_json(silent=True))
    url = clean_url(body.get("url"))

    try:
        res = predict_rpc(url)
        worker_id = res.pop("worker_id", None)
        _record(started, 200, res.get("category"), worker_id)
        return res
    except (QueueUnavailable, pika.exceptions.AMQPError, OSError):
        logger.warning("RabbitMQ broker unavailable")
        _record(started, 503)
        return error("Prediction service unavailable", 503)
    except (QueueTimeout, TimeoutError):
        logger.warning("Worker prediction timed out")
        _record(started, 504)
        return error("Prediction service timed out", 504)
    except BadReply:
        logger.warning("Invalid reply from prediction service")
        _record(started, 502)
        return error("Invalid reply from prediction service", 502)
    except Exception:
        logger.exception("predict_rpc() failed")
        _record(started, 500)
        return error("Prediction failed", 500)


@app.post(f"{API_PREFIX}/feedback")
def feedback():
    """Store user feedback on a URL verdict after redacting private URL parts."""
    body = json_object(request.get_json(silent=True))
    url = redact_url(clean_url(body.get("url")))
    shown = clean_category(body.get("shown_category"), "shown_category")
    reported = clean_category(body.get("reported_category"), "reported_category")

    saved = save_feedback(app.config["DB_PATH"], url, shown, reported)
    return {"status": "saved" if saved else "duplicate"}


def _record(started, status, category=None, worker_id=None):
    """Log request latency and outcome without failing the HTTP response."""
    latency_ms = round((time.perf_counter() - started) * 1000)
    try:
        log_request(app.config["DB_PATH"], status, latency_ms, category, worker_id)
    except StorageError:
        logger.warning("Could not write request log", exc_info=True)
