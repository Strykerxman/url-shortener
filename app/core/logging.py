# -------------------------------------------------------
# Logging and Error Handling Utilities
# -------------------------------------------------------
# This module provides centralized error handling and logging functions.
# All HTTP exceptions raised by the API are logged here, ensuring consistent
# error responses and audit trails for debugging and monitoring.
# -------------------------------------------------------

from fastapi import HTTPException, Request
import logging

# Get a logger instance for this module.
logger = logging.getLogger(__name__)

def raise_bad_request(message):
    # Log and raise a 400 Bad Request HTTP exception.
    # Used when the client sends invalid input data.
    logger.info(f"Bad request: {message}")
    raise HTTPException(status_code=400, detail=message)

def raise_not_found(request: Request):
    # Log and raise a 404 Not Found HTTP exception.
    # Used when a requested resource (URL key or secret key) does not exist.
    logger.info(f"Page not found: {request.url}")
    message = f"Page not found: {request.url}"
    raise HTTPException(status_code=404, detail=message)

def file_not_found(filepath):
    # Log and raise a FileNotFoundError.
    # Used when required configuration or resource files are missing.
    logger.error(f"Configuration file not found: {filepath}")
    raise FileNotFoundError(f"Configuration file not found: {filepath}")

def raise_cache_error(message):
    # Log and raise a 500 Internal Server Error for caching issues.
    # Used when there are problems interacting with the caching layer (e.g., Redis).
    logger.error(f"Caching error: {message}")
    raise HTTPException(status_code=500, detail=message)