from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import URLBase, URLInfo
from app.core import raise_bad_request
from app.database import get_db
from app.models import URL

import validators
import secrets

router = APIRouter()

@router.post("/url", response_model=URLInfo)
async def create_url(url: URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        print(url.target_url)
        raise_bad_request(message="Your provided URL is not valid.")

    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    key = "".join(secrets.choice(chars) for _ in range(5))

    secret_key = "".join(secrets.choice(chars) for _ in range(8))

    db_url = URL(

        target_url=url.target_url, key=key, secret_key=secret_key

    )

    db.add(db_url)

    db.commit()

    db.refresh(db_url)

    db_url.url = key

    db_url.admin_url = secret_key


    return db_url