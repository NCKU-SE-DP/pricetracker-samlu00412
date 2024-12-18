import os

class LoggerConfig:
    """Logger configuration to manage file naming and paths"""

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    DEFAULT_LOG_FILE = "app.log"
    ROTATING_LOG_FILE = "app_rotating.log"

    @classmethod
    def get_log_file(cls, filename: str) -> str:
        """
        Get the full path of the log file and ensure the directory exists
        """
        log_dir = cls.LOG_DIR
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, filename)

    @classmethod
    def get_default_log_file(cls):
        return cls.get_log_file(cls.DEFAULT_LOG_FILE)

    @classmethod
    def get_rotating_log_file(cls):
        return cls.get_log_file(cls.ROTATING_LOG_FILE)