def predict(url: str) -> dict:
    """Temporary stand-in for ml.predict; delete once the real model exists"""
    is_malicious = "login" in url.lower()

    return {
        "is_malicious": is_malicious,
        "category": "phishing" if is_malicious else "benign",
        "confidence": 0.85,
        "explanations": ["Contains credential keywords"] if is_malicious else [],
    }
