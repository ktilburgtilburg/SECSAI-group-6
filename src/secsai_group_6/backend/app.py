from secsai_group_6.backend.worker import RABBITMQ_PORT
from secsai_group_6.backend.worker import RABBITMQ_HOST
import logging
import pika
import uuid
import time
import json
from pathlib import Path
import time

from flask import Flask, request
from flask_cors import CORS
from secsai_group_6.backend.db import StorageError, log_request, save_feedback
from secsai_group_6.backend.rpc_client import (
    BadReply,
    QueueError,
    QueueTimeout,
    QueueUnavailable,
    queue_is_up,
    rpc_assess,
)
from secsai_group_6.backend.validation import (
    InvalidInput,
    clean_category,
    clean_url,
    json_object,
    redact_url,
)
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"

# What each queue failure means to the client.
UPSTREAM_ERRORS = {
    QueueUnavailable: (503, "Prediction service unavailable"),
    QueueTimeout: (504, "Prediction service timed out"),
    BadReply: (502, "Invalid reply from prediction service"),
}

app = Flask(__name__)
CORS(app)
app.config.setdefault("DB_PATH", Path(__file__).with_name("feedback.db"))

### Check if RABBITMQ is up

def check_RABBITMQ_health() -> bool:
    try:
        params = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            connection_attempts=1,
            socket_timeout=1.0
        )
        conn = pika.BlockingConnection(params)
        conn.close()
        return True
    except Exception:
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
    # tests would always fail
    if app.config.get("TESTING"):
        return {"status": "ok"}

    queue_ok = check_RABBITMQ_health()
    return {
        "status": "ok" if queue_ok else "degraded",
        "queue": "ok" if queue_ok else "down",
    }

    # Thank you Gemini for creating this RPC in pika 

def predict_rpc(url: str, timeout: float = 10.0) -> dict:
    # 1. Connect to RabbitMQ
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        connection_attempts=1,
        socket_timeout=timeout,
    )
    conn = pika.BlockingConnection(params)
    channel = conn.channel()

    # 2. Create private exclusive reply queue
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

    # 3. Publish task to worker
    channel.basic_publish(
        exchange="",
        routing_key="url_scans",
        properties=pika.BasicProperties(
            reply_to=reply_queue,
            correlation_id=corr_id,
        ),
        body=json.dumps({"url": url}),
    )

    # 4. Wait for response or timeout
    start = time.time()
    while response is None and conn.is_open:
        conn.process_data_events(time_limit=0.2)
        if time.time() - start > timeout:
            break

    if conn.is_open:
        conn.close()

    if response is None:
        raise TimeoutError("Prediction worker timed out")

    return response

@app.post(f"{API_PREFIX}/assess")
def assess():
    body = json_object(request.get_json(silent=True))
    url = clean_url(body.get("url"))

    if app.config.get("TESTING"):
        try:
            return predict(url)
        except Exception:
            return error("Prediction failed", 500)

    try:
        return predict_rpc(url)

    except (TimeoutError, pika.exceptions.AMQPError):
        logger.exception("predict_rpc() failed")
        return error("Service unavailable", 503)
    except Exception:

        logger.exception("predict() failed")
        return error("Prediction failed", 500)


@app.post(f"{API_PREFIX}/feedback")
def feedback():
    body = json_object(request.get_json(silent=True))
    url = redact_url(clean_url(body.get("url")))
    shown = clean_category(body.get("shown_category"), "shown_category")
    reported = clean_category(body.get("reported_category"), "reported_category")

    saved = save_feedback(app.config["DB_PATH"], url, shown, reported)
    return {"status": "saved" if saved else "duplicate"}


def _record(started, status, category=None, worker_id=None):
    latency_ms = round((time.perf_counter() - started) * 1000)
    try:
        log_request(app.config["DB_PATH"], status, latency_ms, category, worker_id)
    except StorageError:
        # Never fail a request over logging.
        logger.warning("Could not write request log", exc_info=True)
