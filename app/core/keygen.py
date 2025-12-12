import secrets
import string
from app.database import crud
from sqlalchemy.orm import Session

def create_key(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length)) 

def create_unique_key(db: Session) -> str:
    key = create_key()
    while crud.get_db_url_by_key(db, key):
        key = create_key()
    return key    