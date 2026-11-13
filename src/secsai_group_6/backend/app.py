import logging
import os
import time
from pathlib import Path

from flask import Flask, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

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
app.config.setdefault(
    "DB_PATH", os.environ.get("DB_PATH", Path(__file__).with_name("feedback.db"))
)


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
    return {"status": "ok", "queue": "ok" if queue_is_up() else "down"}


@app.post(f"{API_PREFIX}/assess")
def assess():
    body = json_object(request.get_json(silent=True))
    url = clean_url(body.get("url"))

    started = time.perf_counter()
    try:
        verdict, worker_id = rpc_assess(url)
    except QueueError as exc:
        status, message = UPSTREAM_ERRORS.get(
            type(exc), (502, "Prediciton service error")
        )
        logger.warning("assess failed: %s (%s)", type(exc).__name__, exc)
        _record(started, status)
        return error(message, status)
    _record(started, 200, verdict["category"], worker_id)
    return verdict


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
