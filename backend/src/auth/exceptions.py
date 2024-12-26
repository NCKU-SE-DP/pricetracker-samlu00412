import logging
from sentry_sdk import capture_exception
from fastapi import HTTPException

def handle_exception(e: Exception, detail: str, status_code: int = 401):
    
    logging.error(f"{detail}: {e}")
    capture_exception(e)
    raise HTTPException(status_code=status_code, detail=detail)