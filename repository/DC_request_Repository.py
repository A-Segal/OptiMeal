from sqlalchemy.orm import Session
from models.DC_request import DC_Request
from datetime import datetime

class DCRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    # יצירת בקשה חדשה
    def create_request(
        self,
        distribution_center_id: int,
        amount_of_meals: int,
        type: int = 0,
        freshness_priority: int = 0,
        request_date: datetime = None
    ) -> DC_Request:
        if request_date is None:
            request_date = datetime.now()
        new_request = DC_Request(
            DistributionCenterID=distribution_center_id,
            amount_of_meals=amount_of_meals,
            type=type,
            freshness_priority=freshness_priority,
            request_date=request_date
        )
        self.db.add(new_request)
        self.db.commit()
        self.db.refresh(new_request)
        return new_request

    # קבלת בקשה לפי ID
    def get_request(self, request_id: int) -> DC_Request | None:
        return self.db.query(DC_Request).filter(DC_Request.id == request_id).first()

    # קבלת כל הבקשות
    def get_all_requests(self) -> list[DC_Request]:
        return self.db.query(DC_Request).all()

    # עדכון בקשה
    def update_request(
        self,
        request_id: int,
        amount_of_meals: int = None,
        type: int = None,
        freshness_priority: int = None,
        request_date: datetime = None
    ) -> DC_Request | None:
        request = self.get_request(request_id)
        if request:
            if amount_of_meals is not None:
                request.amount_of_meals = amount_of_meals
            if type is not None:
                request.type = type
            if freshness_priority is not None:
                request.freshness_priority = freshness_priority
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