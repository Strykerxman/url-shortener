from fastapi import HTTPException, Request
import logging
logger = logging.getLogger(__name__)

def raise_bad_request(message):
    logger.info(f"Bad request: {message}")
    raise HTTPException(status_code=400, detail=message)

def raise_not_found(request: Request):
    logger.info(f"Page not found: {request.url}")
    raise HTTPException(status_code=404, detail=request)

def file_not_found(filepath):
    logger.error(f"Configuration file not found: {filepath}")
    raise FileNotFoundError(f"Configuration file not found: {filepath}")
    