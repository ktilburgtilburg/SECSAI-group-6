def predict(url: str) -> dict:
    is_malicious = "login" in url.lower()
    return {
        "is_malicious": is_malicious,
        "category": "malicious" if is_malicious else "benign",
        "confidence": 0.85,
        "explanations": ["Contains credential keywords"] if is_malicious else [],
    }