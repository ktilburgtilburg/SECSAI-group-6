import logging
from pathlib import Path

from flask import Flask, request
from flask_cors import CORS
from secsai_group_6.backend.db import StorageError, save_feedback
from secsai_group_6.backend.validation import (
    InvalidInput,
    clean_category,
    clean_url,
    json_object,
    redact_url,
)
from secsai_group_6.ml.predict import predict
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"

app = Flask(__name__)
CORS(app)
app.config.setdefault("DB_PATH", Path(__file__).with_name("feedback.db"))


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
    return {"status": "ok"}


@app.post(f"{API_PREFIX}/assess")
def assess():
    body = json_object(request.get_json(silent=True))
    url = clean_url(body.get("url"))

    try:
        return predict(url)
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
