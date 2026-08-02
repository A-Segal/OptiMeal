from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from .base import Base


class AssignmentNotification(Base):
    __tablename__ = "AssignmentNotification"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_key = Column(String(255), unique=True, nullable=False)

    assignment_id = Column(Integer, nullable=True)
    recipient_id = Column(Integer, nullable=True)
    center_id = Column(Integer, nullable=False)

    notification_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")

    payload_json = Column(Text, nullable=False)
    external_system_name = Column(String(100), nullable=False)
    external_message_id = Column(String(255), nullable=True)

    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    last_error = Column(Text, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)

    scheduled_date = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
