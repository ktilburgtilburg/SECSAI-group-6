from enum import StrEnum


class Category(StrEnum):
    """The only verdicts the system knows."""

    BENIGN = "benign"
    PHISHING = "phishing"
    MALWARE = "malware"
    DEFACEMENT = "defacement"
