import logging

from abc import ABC, abstractmethod
from ..utils.config import AppConfig

class BaseProvider(ABC):
    """
    Base class for all providers.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """The child class MUST provide a name."""
        pass

    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(self.name)