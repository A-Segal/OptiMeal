from sqlalchemy.orm import Session
from models.volunteer_request import VolunteerRequest


class VolunteerRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_volunteer_request(
        self,
        volunteer_id: int,
        location_lat: float,
        location_lng: float,
        available_time
    ) -> VolunteerRequest:
        request = VolunteerRequest(
            volunteer_id=volunteer_id,
            location_lat=location_lat,
            location_lng=location_lng,
            available_time=available_time
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def get_volunteer_request(self, request_id: int) -> VolunteerRequest | None:
        return self.db.query(VolunteerRequest).filter(VolunteerRequest.id == request_id).first()

    def get_all_volunteer_requests(self) -> list[VolunteerRequest]:
        return self.db.query(VolunteerRequest).all()

    def get_requests_by_volunteer(self, volunteer_id: int) -> list[VolunteerRequest]:
        return self.db.query(VolunteerRequest).filter(
            VolunteerRequest.volunteer_id == volunteer_id
        ).all()

    def update_volunteer_request(
        self,
        request_id: int,
        volunteer_id: int = None,
        location_lat: float = None,
        location_lng: float = None,
        available_time = None
    ) -> VolunteerRequest | None:
        request = self.get_volunteer_request(request_id)
        if request:
            if volunteer_id is not None:
                request.volunteer_id = volunteer_id
            if location_lat is not None:
                request.location_lat = location_lat
            if location_lng is not None:
                request.location_lng = location_lng
            if available_time is not None:
                request.available_time = available_time

            self.db.commit()
            self.db.refresh(request)

        return request

    def delete_volunteer_request(self, request_id: int) -> bool:
        request = self.get_volunteer_request(request_id)
        if request:
            self.db.delete(request)
            self.db.commit()
            return True
        return False

    def get_by_volunteer_id(self, volunteer_id: int) -> VolunteerRequest | None:
        return (
            self.db.query(VolunteerRequest)
            .filter(VolunteerRequest.volunteer_id == volunteer_id)
            .first()
        )