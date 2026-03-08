import argparse
import uuid
import logging.config
import json

from typing import Any
from .base import Task
from .utils.config import config

class CLI:
    def __init__(self, description: str, actionDesc: str):
        self.setup_logging()
        self.parser = argparse.ArgumentParser(description=description)
        self.subparsers = self.parser.add_subparsers(dest='command', required=True)

        self.local_parser = self.subparsers.add_parser('local', help=f'{actionDesc} locally')
        self.local_json_args = []
        self.cloud_parser = self.subparsers.add_parser('cloud', help=f'{actionDesc} from cloud request')
        self.cloud_parser.add_argument('--run_id', required=True, help='The id of airflow run')
        self.cloud_parser.add_argument('--file_ids', required=True, nargs='+', help='List of unique file IDs for args')
        self.args = None

    def setup_logging(self):
        logging.config.dictConfig({
            "version": 1,
            "formatters": {
                "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
                "detailed": {"format": "%(asctime)s [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d: %(message)s"},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": config.log_level,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["console"],
                    "level": config.log_level,
                },
            }
        })

    def add_local_arg(self, *args, **kargs):
        self.local_parser.add_argument(*args, **kargs)
    
    def add_local_json_arg(self, name, *args, **kargs):
        self.local_json_args.append(name)
        self.local_parser.add_argument(*args, **kargs)
    
    def add_common_args(self, *args, **kargs):
        self.local_parser.add_argument(*args, **kargs)
        self.cloud_parser.add_argument(*args, **kargs)

    def parse_args(self):
        if self.args is not None:
            return
        self.args = self.parser.parse_args()

    def get_run_id(self) -> str:
        self.parse_args()
        if self.args is None:
            raise RuntimeError('Arg is None')
        if self.args.command == 'local':
            return str(uuid.uuid4())
        elif self.args.command == 'cloud':
            return self.args.run_id
        else:
            raise NotImplementedError()
    
    def get(self, key: str) -> Any:
        self.parse_args()
        val = None
        if hasattr(self.args, key):
            val = getattr(self.args, key)
            if key in self.local_json_args:
                val = json.loads(val)
        return val
    
    def execute(self, task: Task):
        self.parse_args()
        if self.args is None:
            raise RuntimeError('Arg is None')
        run_type = self.get('command')
        if run_type == 'local':
            task.local_run(*[self.get(args) for args in task.arglist])
        elif run_type == 'cloud':
            next_arg_id = task.run(*self.args.file_ids)
            print(next_arg_id)
        else:
            raise NotImplementedError()
