# API Spec

Local server: `http://127.0.0.1:5000`

- Requests with a body must send `Content-Type: application/json`.
- All responses are JSON, including errors.
- Errors always look like `{"error": "message"}`.

---

## `GET /health`

Check if the server is online.

**Response (200)**
```json
{"api": "ok", "queue": "ok"}
```

---

## `POST /api/v1/assess`

Check a URL and get a threat verdict.

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
  "explanations": ["Uses raw IP address", "Contains credential keywords"]
}
```

| Field          | Type         | Notes                                                                  |
|----------------|--------------|------------------------------------------------------------------------|
| `is_malicious` | bool         | `false` when category is `benign`                                      |
| `category`     | string       | One of: `benign`, `malicious`                                          |
| `confidence`   | float        | 0.0 to 1.0. How sure the model is of its own verdict, whichever class |
| `explanations` | list[string] | Reasons for the verdict. Can be empty                                  |

**Errors**

| Status | When                                                                              |
|--------|-----------------------------------------------------------------------------------|
| 400    | Body is not a JSON object (or wrong Content-Type), `url` missing, not a string, empty, or longer than 2048 characters |
| 502    | Invalid reply from the model                                |
| 503    | Queue unreachable                                |
| 504    | No reply withing the timeout                                |

On a 500 the extension decides whether to fail open or closed. The backend never
returns a made-up verdict.

---

## `POST /api/v1/feedback`

Report a wrong verdict (e.g. a false alarm).

**Request**
```json
{
  "url": "https://example.com/page",
  "shown_category": "malicious",
  "reported_category": "benign"
}
```

| Field               | Notes                                                    |
|---------------------|----------------------------------------------------------|
| `url`               | Must be an `http` or `https` URL                         |
| `shown_category`    | The category the user was shown                          |
| `reported_category` | The category the user says is correct                    |

**Response (200)**
```json
{"status": "saved"}
```
or `{"status": "duplicate"}` if the same report (host, shown, reported) was already stored.

**Errors**

| Status | When                                                              |
|--------|-------------------------------------------------------------------|
| 400    | Invalid body, `url`, or category                                  |
| 500    | The report could not be stored: `{"error": "Could not save feedback"}` |

**Privacy:** only `scheme://hostname` is stored (e.g. `https://example.com`).
The path, query, fragment, port, and any `user:pass@` are discarded before saving.

---

## Notes

- The model's `predict(url)` must return the same fields as the `/assess` response.
- Unknown routes and wrong methods (404, 405) also return `{"error": "..."}`.
- CORS is enabled so the browser extension can call the server.