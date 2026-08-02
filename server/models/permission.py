from sqlalchemy import Column, Integer, String
from .base import Base

class Permission(Base):
    __tablename__ = 'Permission'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)