
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from .base import Base

class DC_Request(Base):
    __tablename__ = 'DC_Request'

    id = Column(Integer, primary_key=True, autoincrement=True)
    DistributionCenterID = Column(Integer, ForeignKey('DistributionCenter.id'), nullable=False)
    amount_of_meals = Column(Integer, nullable=False)
    request_date = Column(DateTime, nullable=False)
    type = Column(Integer, default=0)
    freshness_priority = Column(Integer, default=0)