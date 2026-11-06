from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Базовый декларативный класс для асинхронной SQLAlchemy 2.0"""
    pass

class Links(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    body = Column(String, nullable=False, index=True)
    clicks = Column(Integer, default=0, nullable=False)

