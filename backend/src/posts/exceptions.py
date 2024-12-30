import logging
from sentry_sdk import capture_exception


def handle_exception(e: Exception, detail: str):
    
    logging.error(f"{detail}: {e}")
    capture_exception(e)
    return detail