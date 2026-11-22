from enum import StrEnum


class Category(StrEnum):
    """Binary verdict categories supported by the system."""

    BENIGN = "benign"
    MALICIOUS = "malicious"
