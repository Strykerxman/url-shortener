from fastapi import HTTPException
import logging
logger = logging.getLogger(__name__)

def raise_bad_request(message):
    logger.info(f"Bad request: {message}")
    raise HTTPException(status_code=400, detail=message)

def raise_not_found(message):
    logger.info(f"Not found: {message}")
    raise HTTPException(status_code=404, detail=message)

def file_not_found(filepath):
    logger.error(f"Configuration file not found: {filepath}")
    raise FileNotFoundError(f"Configuration file not found: {filepath}")
    