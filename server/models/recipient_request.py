from sqlalchemy import Column, Integer, DateTime, ForeignKey
from .base import Base


class RecipientRequest(Base):
    __tablename__ = 'Recipient_Request'  # שם הטבלה בדיוק כמו ב-SQL

    id = Column(Integer, primary_key=True, autoincrement=True)  # עמודת מפתח ראשי
    RecipientID = Column(Integer, ForeignKey('Recipient.id'), nullable=False)  # מפתח זר לטבלת Recipient
    amount_of_meals = Column(Integer, nullable=False)  # מספר הארוחות
    request_date = Column(DateTime, nullable=False)  # תאריך הבקשה