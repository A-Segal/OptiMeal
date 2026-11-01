from sqlalchemy import Column, Integer, String, DECIMAL, DateTime
from .base import Base

class Recipient(Base):
    __tablename__ = 'Recipient'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fname = Column(String(50), nullable=False)
    lname = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    mail = Column(String(100))
    phone = Column(String(20))
    location_lat = Column(DECIMAL(9,6))
    location_lng = Column(DECIMAL(9,6))






