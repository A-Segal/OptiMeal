from sqlalchemy import Column, Integer, Float, Time, ForeignKey
from .base import Base


class VolunteerRequest(Base):
    __tablename__ = 'volunteer_request'

    id = Column(Integer, primary_key=True, autoincrement=True)
    volunteer_id = Column(Integer, ForeignKey('Volunteer.id'), nullable=False)
    location_lat = Column(Float)
    location_lng = Column(Float)
    available_time = Column(Float)