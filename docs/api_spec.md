# API Spec

Local server: `http://127.0.0.1:5000`

- Requests with a body must send `Content-Type: application/json`.
- All responses are JSON, including errors.
- Errors always look like `{"error": "message"}`.
- The interface server does **not** run ML inference in-process; it dispatches URLs over RabbitMQ (`assess_requests` queue) to background worker containers with a **2-second RPC timeout**.

---

## `GET /health`

Check if the API server and RabbitMQ broker are reachable.

**Response (200 — healthy)**
```json
{"status": "ok", "queue": "ok"}
```

**Response (200 — broker unreachable)**
```json
{"status": "degraded", "queue": "down"}
```

---

## `POST /api/v1/assess`

Check a URL and get a binary threat verdict (`benign` or `malicious`) from a background ML worker.

**Request**
```json
{"url": "https://example.com"}
```

**Response (200)**
```json
{
  "is_malicious": true,
  "category": "malicious",
  "confidence": 0.85,
  "explanations": [
    "hosted on a domain with elevated abuse rate (risk score 0.70)"
  ]
}
```

| Field          | Type         | Notes                                                                  |
|----------------|--------------|------------------------------------------------------------------------|
<<<<<<< Updated upstream
| `is_malicious` | bool         | `false` when category is `benign`                                      |
| `category`     | string       | One of: `benign`, `malicious`                                          |
| `confidence`   | float        | 0.0 to 1.0. How sure the model is of its own verdict, whichever class |
| `explanations` | list[string] | Reasons for the verdict. Can be empty                                  |
=======
| `is_malicious` | bool         | `false` when category is `benign`, `true` when `malicious`             |
| `category`     | string       | Binary verdict: `benign` or `malicious`                                |
| `confidence`   | float        | 0.0 to 1.0. How sure the model is of its own verdict                   |
| `explanations` | list[string] | Human-readable reasons for a malicious verdict (empty for `benign`)    |
>>>>>>> Stashed changes

**Errors**

| Status | Response Body                                          | When                                                                                              |
|--------|--------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| 400    | `{"error": "..."}`                                     | Body is not a JSON object (or wrong `Content-Type`), `url` missing, not a string, empty, or >2048 chars |
| 500    | `{"error": "Prediction failed"}`                       | Unexpected internal error while handling the request                                              |
| 502    | `{"error": "Invalid reply from prediction service"}`   | Worker returned a malformed or contract-violating reply                                           |
| 503    | `{"error": "Prediction service unavailable"}`          | RabbitMQ broker is unreachable or disconnected                                                    |
| 504    | `{"error": "Prediction service timed out"}`            | No worker replied within the **2-second** RPC timeout                                             |

On 5xx errors, the backend never returns a guessed verdict. The browser extension fails open (displays a neutral `?` badge and allows navigation to continue).

---

## `POST /api/v1/feedback`

Report a wrong verdict (e.g., a false alarm or missed threat).

**Request**
```json
{
  "url": "https://example.com/page",
  "shown_category": "malicious",
  "reported_category": "benign"
}
```

| Field               | Notes                                       |
|---------------------|---------------------------------------------|
| `url`               | Must be an `http` or `https` URL            |
| `shown_category`    | The category shown to the user              |
| `reported_category` | The category the user says is correct       |

<<<<<<< Updated upstream
=======
Both categories must be one of: `benign`, `malicious`.

>>>>>>> Stashed changes
**Response (200)**
```json
{"status": "saved"}
```
or `{"status": "duplicate"}` if the same report `(host, shown_category, reported_category)` was already stored.

**Errors**

| Status | When                                                                   |
|--------|------------------------------------------------------------------------|
| 400    | Invalid body, `url`, or category                                       |
| 500    | The report could not be stored: `{"error": "Could not save feedback"}` |

**Privacy:** Only `scheme://hostname` is stored (e.g., `https://example.com`). The path, query, fragment, port, and any `user:pass@` credentials are discarded before saving.

---

## Notes

- Workers include `worker_id` on the internal RabbitMQ reply for request logging; the interface server strips `worker_id` before returning the HTTP JSON response.
- Unknown routes and wrong methods (`404`, `405`) also return `{"error": "..."}`.
- CORS is enabled so the browser extension can call the server.
