from sqlalchemy import Column, Integer, ForeignKey
from .base import Base

class Vehicle(Base):
    __tablename__ = 'Vehicle'
    id = Column(Integer, primary_key=True, autoincrement=True)
    VolunteerID = Column(Integer, ForeignKey('Volunteer.id'), nullable=False)
    capacity = Column(Integer, nullable=False)