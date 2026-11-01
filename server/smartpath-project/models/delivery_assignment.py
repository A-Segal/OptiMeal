from sqlalchemy import Column, Integer, ForeignKey
from .base import Base

class DeliveryAssignment(Base):
    __tablename__ = 'DeliveryAssignment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    DistributionCenterID = Column(Integer, ForeignKey('DistributionCenter.id'), nullable=False)
    RecipientID = Column(Integer, ForeignKey('Recipient.id'), nullable=False)
    VolunteerID = Column(Integer, ForeignKey('Volunteer.id'), nullable=True)
    amount_of_meals = Column(Integer)
    freshness_priority = Column(Integer, nullable=False)
