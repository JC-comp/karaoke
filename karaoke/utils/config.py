import io
import logging
import os
import requests
import tqdm

from configparser import ConfigParser

LOG_FORMAT = '%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s'

def get_logger(name: str, level: int=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.hasHandlers():
        return logger

    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

def get_task_logger(name: str, buffer: io.StringIO, event_handler: logging.Handler, level=logging.INFO) -> logging.Logger:
    logger = get_logger(name, level)
    # preserve the console stream handler
    if len(logger.handlers) > 1:
        logger.handlers.clear()
        logger = get_logger(name, level)
    
    buffer_handler = logging.StreamHandler(buffer)
    formatter = logging.Formatter(LOG_FORMAT)
    for handler in [buffer_handler, event_handler]:
        handler.setLevel(level)
        handler.setFormatter(formatter)    
        logger.addHandler(handler)
    return logger

def download(url: str, path: str, output: io.StringIO, overwrite: bool = False):
    """
    Download a file from a URL and save it to a local path.
    """
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024

    if os.path.exists(path):
        if total_size != 0:
            file_size = os.path.getsize(path)
            if file_size != total_size:
                output.write(f"File {path} exists but size does not match. Overwriting.\n")
                overwrite = True
        
        if overwrite:
            output.write(f"File {path} already exists. Overwriting.\n")
        else:
            output.write(f"File {path} already exists. Skipping download.\n")
            response.close()
            return

    with tqdm.tqdm(total=total_size, unit='iB', unit_scale=True, file=output) as pbar:
        with open(path, 'wb') as file:
            for data in response.iter_content(block_size):
                file.write(data)
                pbar.update(len(data))
    
    if total_size != 0 and pbar.n != total_size:
        raise ValueError(f"Downloaded file size {pbar.n} does not match expected size {total_size}.")


class Config:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            instance = super(Config, cls).__new__(cls)
            instance.static_init()
            cls.instance = instance
        return cls.instance
    
    def parse_mfa_models(self, config: ConfigParser) -> None:
        self.mfa_base = config.get('mfa', 'base', fallback=os.path.join(self.work_dir, 'model'))
        self.mfa_models = {
            'en': {
                'acoustic': 'https://github.com/MontrealCorpusTools/mfa-models/releases/download/acoustic-english_mfa-v3.1.0/english_mfa.zip',
                'dictionary': 'https://github.com/MontrealCorpusTools/mfa-models/releases/download/dictionary-english_us_mfa-v3.1.0/english_us_mfa.dict'
            },
            'zh': {
                'acoustic': 'https://github.com/MontrealCorpusTools/mfa-models/releases/download/acoustic-mandarin_mfa-v3.0.0/mandarin_mfa.zip',
                'dictionary': 'https://github.com/MontrealCorpusTools/mfa-models/releases/download/dictionary-mandarin_taiwan_mfa-v3.0.0/mandarin_taiwan_mfa.dict'
            },
        }
        if not config.has_section('mfa'):
            return
        model_paths = config.items('mfa')
        for key, link in model_paths:
            if '.' not in key and 'base' != key:
                self.logger.warning(f"Invalid model path {key}. Expected format: <lang>.<model_type>")
                continue
            lang, model_type = key.split('.')
            if lang not in self.mfa_models:
                self.mfa_models[lang] = {}
            self.mfa_models[lang][model_type] = link
    
    def get_mfa_model_path(self, lang: str, model_type: str) -> str:
        model_path = os.path.join(self.mfa_base, lang)
        if model_type == 'acoustic':
            model_path += '.zip'
        elif model_type == 'dictionary':
            model_path += '.dict'
        else:
            raise ValueError(f"Unknown model type {model_type}.")

        if os.path.exists(model_path):
            return model_path
        if lang not in self.mfa_models:
            raise ValueError(f"Language {lang} not found in MFA models.")
        if model_type not in self.mfa_models[lang]:
            raise ValueError(f"Model type {model_type} not found for language {lang}.")
        download(self.mfa_models[lang][model_type], model_path, output=None)
        return model_path

    def static_init(self):
        self.logger = get_logger(__name__)
        self.work_dir = os.path.abspath(os.curdir)
        config = self.read_config()

        self.log_level = config.get('logging', 'level', fallback='INFO')
        
        self.media_path = config.get('media', 'path', fallback=os.path.join(self.work_dir, 'media'))
        self.socketio_path = config.get('socketio', 'path', fallback='ws')
        self.min_job_response_time = config.getint('scheduler', 'min_job_response_time', fallback=60*5)
        self.scheduler_host = config.get('scheduler', 'host', fallback='0.0.0.0')
        self.scheduler_port = config.getint('scheduler', 'port', fallback=8201)
        self.max_daemon_jobs = config.getint('scheduler', 'max_daemon_jobs', fallback=10)

        self.parse_mfa_models(config)
        
        self.acoustid_enabled = config.getboolean('acoustid', 'enabled', fallback=False)
        self.acoustid_api_key = config.get('acoustid', 'api_key', fallback='xxxxxxxxx')

        self.gpt_enabled = config.getboolean('gpt', 'enabled', fallback=False)
        self.gpt_endpoint = config.get('gpt', 'endpoint', fallback='http://localhost:8080/api/chat/completions')
        self.gpt_token = config.get('gpt', 'token', fallback='xxxxxxxxx')

        self.whisper_cpu_model = config.get('transcription', 'cpu_model', fallback='large-v3-turbo')
        self.whisper_gpu_model = config.get('transcription', 'gpu_model', fallback='medium')
        self.whisper_initial_prompt = config.get('transcription', 'initial_prompt', fallback=None)

        self.export_font = config.get('export', 'font', fallback='Arial')


        self.post_init()
        
    def read_config(self):
        config_path = os.path.join(self.work_dir, 'config.ini')
        if not os.path.exists(config_path):
            self.logger.warning('Config file not found.')

        config = ConfigParser()
        config.read(config_path)

        return config
    
    def post_init(self):
        if not os.path.exists(self.media_path):
            self.logger.info(f'Media path {self.media_path} does not exist.')
            os.makedirs(self.media_path)