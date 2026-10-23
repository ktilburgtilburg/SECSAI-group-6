import logging

from flask import Flask, request
from flask_cors import CORS
from secsai_group_6.backend.stub_model import predict
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

API_PREFIX = "/api/v1"


def error(message: str, status: int) -> tuple[dict, int]:
    """Build the error response used by every failure path."""
    return ({"error": message}, status)


@app.errorhandler(HTTPException)
def handle_http_exception(exc: HTTPException):
    return error(exc.description or exc.name, exc.code or 500)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(f"{API_PREFIX}/assess")
def assess():
    body = request.get_json(silent=True)

    # Guard 1: body must be a JSON object
    if not isinstance(body, dict):
        return error("Body must be a JSON object (Content-Type: application/json)", 400)

    url = body.get("url")

    # Guard 2: url must be a string
    if url is None:
        return error("Field 'url' is required", 400)
    if not isinstance(url, str):
        return error("Field 'url' must be a string", 400)

    url = url.strip()

    # Guard 3: url must be non-empty
    if not url:
        return error("Field 'url' must be non-empty", 400)

    # Happy path
    try:
        return predict(url)
    except Exception:
        logger.exception("predict() failed")
        return error("Prediction failed", 500)
