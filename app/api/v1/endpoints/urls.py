from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.schemas import URLBase, URLInfo
from app.core import logging
from app.database import crud, get_db

import validators

router = APIRouter()

@router.get("/{url_key}")
async def forward_to_target_url(url_key: str, request: Request, db_session: Session = Depends(get_db)):

    if db_url := crud.get_db_url_by_key(db_session, url_key):
        return RedirectResponse(db_url.target_url)
    else:
        logging.raise_not_found(request)

@router.post("/url", response_model=URLInfo)
async def create_url(url: URLBase, db_session: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        logging.raise_bad_request(message="Your provided URL is not valid. **Must include http:// or https://**")

    db_url = crud.create_db_url(db_session, url)
    db_url.url = db_url.key

    db_url.admin_url = db_url.secret_key


    return db_url