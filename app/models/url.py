from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean

class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    secret_key = Column(String, unique=True, index=True)
    target_url = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    clicks = Column(Integer, default=0)

    def __repr__(self):
        return f"<URL(key={self.key}, target_url={self.target_url}, is_active={self.is_active}, clicks={self.clicks})>"
    