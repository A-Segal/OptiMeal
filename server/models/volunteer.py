from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from .base import Base

class Volunteer(Base):
    __tablename__ = 'Volunteer'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fname = Column(String(50), nullable=False)
    lname = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    mail = Column(String(100))
    phone = Column(String(20))