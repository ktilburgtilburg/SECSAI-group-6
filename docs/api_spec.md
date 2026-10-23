# API Spec

Local server: `http://127.0.0.1:5000`
All requests and responses use JSON.

---

## `GET /health`

Check if the server is online.

**Response (200)**
```json
{"status": "ok"}
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
  "category": "phishing",
  "confidence": 0.85,
  "explanations": ["Uses raw IP address", "Contains credential keywords"]
}
```

| Field          | Type         | Notes                                                 |
|----------------|--------------|-------------------------------------------------------|
| `is_malicious` | bool         | `false` when category is `benign`                     |
| `category`     | string       | One of: `benign`, `phishing`, `malware`, `defacement` |
| `confidence`   | float        | 0.0 to 1.0                                            |
| `explanations` | list[string] | Reasons for the verdict. Can be empty                 |

**Error (400)**: missing body, missing/empty `url`, or `url` is not a string
```json
{"error": "url is required"}
```

---

## `POST /api/v1/feedback`

Report a wrong verdict (e.g. a false alarm). No personal data is stored.

**Request**
```json
{"url": "https://example.com", "reported_category": "benign"}
```

**Response (200)**
```json
{"status": "saved"}
```

**Error (400)**: same format as above.

---

## Notes

- Errors always look like `{"error": "message"}`.
- The model's `predict(url)` must return the same fields as the `/assess` response.
- CORS is enabled so the browser extension can call the server.