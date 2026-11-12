Request queue: assess_requests (both sides declare it with default args, non-durable)
Request body (JSON):  {"url": "..."}
Message properties:   reply_to, correlation_id (set by the gateway), expiration 2000 ms
Reply body (JSON):    {"is_malicious": bool, "category": str, "confidence": float,
                       "explanations": [str], "worker_id": str}
Worker publishes the reply to `reply_to` with the SAME correlation_id, then acks the request.
On failure the worker still replies, with {"error": "..."}, so the gateway fails fast (502)
instead of waiting for the timeout (504).