from sqlalchemy.orm import Session
from models.volunteer import Volunteer
from repository.VehicleRepository import VehicleRepository
from services.utils.auth_utils import hash_password, verify_password


class VolunteerRepository:
    def __init__(self, db: Session):
        self.db = db
        self.vehicle_repo = VehicleRepository(db)

    def create_volunteer(
        self,
        fname: str,
        lname: str,
        username: str,
        password: str,
        vehicle_capacity: int,
        mail: str = None,
        phone: str = None
    ) -> Volunteer:
        volunteer = Volunteer(
            fname=fname,
            lname=lname,
            username=username,
            password=hash_password(password),
            mail=mail,
            phone=phone
        )
        self.db.add(volunteer)
        self.db.commit()
        self.db.refresh(volunteer)

        # צור רכב למתנדב
        self.vehicle_repo.create_vehicle(
            VolunteerID=volunteer.id,
            capacity=vehicle_capacity
        )

        return volunteer

    def get_volunteer(self, volunteerID: int) -> Volunteer | None:
        return self.db.query(Volunteer).filter(Volunteer.id == volunteerID).first()

    def get_by_username_password(self, username, password):
        """מחזיר מתנדב אם הסיסמה תואמת, אחרת None"""
        volunteer = self.db.query(Volunteer).filter_by(username=username).first()
        if volunteer and verify_password(password, volunteer.password):
            return volunteer
        return None

    def get_all_volunteers(self) -> list[Volunteer]:
        return self.db.query(Volunteer).all()

    def update_volunteer(
        self,
        volunteerID: int,
        fname: str = None,
        lname: str = None,
        username: str = None,
        password: str = None,
        mail: str = None,
        phone: str = None
    ) -> Volunteer | None:
        volunteer = self.get_volunteer(volunteerID)
        if volunteer:
            if fname is not None:
                volunteer.fname = fname
            if lname is not None:
                volunteer.lname = lname
            if username is not None:
                volunteer.username = username
            if password is not None:
                volunteer.password = hash_password(password)
            if mail is not None:
                volunteer.mail = mail
            if phone is not None:
                volunteer.phone = phone
            self.db.commit()
            self.db.refresh(volunteer)
        return volunteer

    def delete_volunteer(self, volunteerID: int) -> bool:
        volunteer = self.get_volunteer(volunteerID)
        if volunteer:
            # מחיקת רכבים קשורים
            self.vehicle_repo.delete_vehicle_by_volunteer(volunteerID)

            # מחיקת המתנדב
            self.db.delete(volunteer)
            self.db.commit()
            return True
        return False

    def get_by_id(self, volunteerID: int) -> Volunteer | None:
        return self.get_volunteer(volunteerID)