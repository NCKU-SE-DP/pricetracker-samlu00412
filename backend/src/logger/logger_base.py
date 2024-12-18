import logging
from logging.handlers import RotatingFileHandler
import json
from json import JSONDecodeError
from .config import LoggerConfig
from src.error_handlers.server_exception import InternalServerError

class LogMessageInterface:
    """Unified management of log message templates and content"""

    def __init__(self, message: str, **context):
        self.message = message
        self.context = {
            key: (str(value) if isinstance(value, Exception) else value)
            for key, value in context.items()
        }

    def format(self):
        messages = {"message": self.message, **self.context}
        try:
            return json.dumps(messages, ensure_ascii=False)
        except JSONDecodeError as e:
            InternalServerError(e)

class LoggerService:
    """"Log service, encapsulating unified logging behavior"""

    _loggers = {}

    def __new__(cls, name: str):
        if name in cls._loggers:
            return cls._loggers[name]

        instance = super().__new__(cls)
        instance._initialize_logger(name)
        cls._loggers[name] = instance
        return instance

    def _initialize_logger(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.hasHandlers():
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

            file_handler = logging.FileHandler(LoggerConfig.get_default_log_file())
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            rotating_file_handler = RotatingFileHandler(
                LoggerConfig.get_rotating_log_file(), maxBytes=5 * 1024 * 1024, backupCount=3
            )
            rotating_file_handler.setLevel(logging.ERROR)
            rotating_file_handler.setFormatter(formatter)
            self.logger.addHandler(rotating_file_handler)

    def log_info(self, message: LogMessageInterface):
        self.logger.info(message.format())

    def log_debug(self, message: LogMessageInterface):
        self.logger.debug(message.format())

    def log_warning(self, message: LogMessageInterface):
        self.logger.warning(message.format())

    def log_error(self, message: LogMessageInterface):
        self.logger.error(message.format())

    def log_critical(self, message: LogMessageInterface):
        self.logger.critical(message.format())