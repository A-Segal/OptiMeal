from sqlalchemy import Column, Integer, String, DECIMAL
from .base import Base

class DistributionCenter(Base):
    __tablename__ = 'DistributionCenter'
    id = Column(Integer, primary_key=True)
    fname = Column(String(50), nullable=False)
    lname = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    mail = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    location_lat = Column(DECIMAL(10, 7), nullable=False)
    location_lng = Column(DECIMAL(10, 7), nullable=False)

