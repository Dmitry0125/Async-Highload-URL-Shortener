from sqlalchemy import Column, Integer, String, ForeignKey
# from sqlalchemy.orm import relationship
from database import Base

class Links(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    body = Column(String, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)

