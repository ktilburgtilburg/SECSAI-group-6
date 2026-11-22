from enum import StrEnum


class Category(StrEnum):
    """The only verdicts the system knows."""

    BENIGN = "benign"
    MALICIOUS = "malicious"
    PHISHING = "phishing"
    MALWARE = "malware"
    DEFACEMENT = "defacement"