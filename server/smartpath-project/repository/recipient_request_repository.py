from sqlalchemy.orm import Session
from models.recipient_request import RecipientRequest
from datetime import datetime

class RecipientRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    # יצירת בקשה חדשה
    def create_request(self, recipient_id: int, amount_of_meals: int, request_date: datetime = None) -> RecipientRequest:
        if request_date is None:
            request_date = datetime.now()
        new_request = RecipientRequest(
            RecipientID=recipient_id,
            amount_of_meals=amount_of_meals,
            request_date=request_date
        )
        self.db.add(new_request)
        self.db.commit()
        self.db.refresh(new_request)
        return new_request

    # קבלת בקשה לפי ID
    def get_request(self, request_id: int) -> RecipientRequest | None:
        return self.db.query(RecipientRequest).filter(RecipientRequest.id == request_id).first()

    # קבלת כל הבקשות
    def get_all_requests(self) -> list[RecipientRequest]:
        return self.db.query(RecipientRequest).all()

    # עדכון בקשה
    def update_request(self, request_id: int, amount_of_meals: int = None, request_date: datetime = None) -> RecipientRequest | None:
        request = self.get_request(request_id)
        if request:
            if amount_of_meals is not None:
                request.amount_of_meals = amount_of_meals
            if request_date is not None:
                request.request_date = request_date
            self.db.commit()
            self.db.refresh(request)
        return request

    # מחיקת בקשה
    def delete_request(self, request_id: int) -> bool:
        request = self.get_request(request_id)
        if request:
            self.db.delete(request)
            self.db.commit()
            return True
        return False