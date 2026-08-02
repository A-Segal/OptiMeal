from sqlalchemy import Column, Integer, String, ForeignKey
from .base import Base

class StaffMember(Base):
    __tablename__ = 'StaffMember'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fname = Column(String(50), nullable=False)
    lname = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    mail = Column(String(100))
    phone = Column(String(20))
    PermissionID = Column(Integer, ForeignKey('Permission.id'), nullable=False)