from .base import BaseIdentifier
from .fingerprint import FingerprintIdentifier
from .shazam import ShazamIdentifier

PROVIDERS: list[type[BaseIdentifier]] = [ShazamIdentifier, FingerprintIdentifier]

__all__ = [
    "PROVIDERS",
]