import logging

from ...tasks.task import Execution

class LoggerWrapper:
    """
    A wrapper for the logger to provide a consistent interface.
    """

    def __init__(self, name: str, logger: logging.Logger):
        self.name = name
        self.logger = logger

    def wrap_message(self, message: str) -> str:
        return f"[{self.name}] {message}"
    
    def __getattr__(self, name):
        attr = getattr(self.logger, name)
        if callable(attr):
            def wrapper(*args, **kwargs):
                wrapped_args = [self.wrap_message(arg) if isinstance(arg, str) else arg for arg in args]
                wrapped_kwargs = {k: self.wrap_message(v) if isinstance(v, str) else v for k, v in kwargs.items()}
                return attr(*wrapped_args, **wrapped_kwargs)
            return wrapper

class BaseProvider:
    """
    Base class for all providers.
    """
    name = "BaseProvider"
    def __init__(self, execution: Execution):
        if self.name == "BaseProvider":
            raise NotImplementedError("name must be set in the subclass")
        self.execution = execution
        self.config = execution.config
        self.logger = LoggerWrapper(self.name, execution.logger)

    def update(self, **kwargs):
        self.execution.update(**kwargs)
