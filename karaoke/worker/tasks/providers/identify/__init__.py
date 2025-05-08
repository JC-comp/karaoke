from .base import BaseIdentifier
from .fingerprint import FingerprintIdentifier
from .shazam import ShazamIdentifier

PROVIDERS: list[type[BaseIdentifier]] = [FingerprintIdentifier, ShazamIdentifier]

__all__ = [
    "PROVIDERS",
]