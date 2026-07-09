from sqlalchemy.orm import Session
from models.staff_member import StaffMember
from services.utils.auth_utils import hash_password, verify_password

class StaffMemberRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_staff_member(
        self,
        fname: str,
        lname: str,
        username: str,
        password: str,
        PermissionID: int,
        mail: str = None,
        phone: str = None
    ) -> StaffMember:
        staff_member = StaffMember(
            fname=fname,
            lname=lname,
            username=username,
            password=hash_password(password),
            PermissionID=PermissionID,
            mail=mail,
            phone=phone
        )
        self.db.add(staff_member)
        self.db.commit()
        self.db.refresh(staff_member)
        return staff_member

    def get_staff_member(self, staffID: int) -> StaffMember | None:
        return self.db.query(StaffMember).filter(StaffMember.id == staffID).first()

    def get_by_username(self, username: str) -> StaffMember | None:
        """מוצא איש צוות לפי שם משתמש."""
        return self.db.query(StaffMember).filter(StaffMember.username == username).first()

    def get_all_staff_members(self) -> list[StaffMember]:
        return self.db.query(StaffMember).all()

    def update_staff_member(
        self,
        staffID: int,
        fname: str = None,
        lname: str = None,
        username: str = None,
        password: str = None,
        PermissionID: int = None,
        mail: str = None,
        phone: str = None
    ) -> StaffMember | None:
        staff_member = self.get_staff_member(staffID)
        if staff_member:
            if fname is not None:
                staff_member.fname = fname
            if lname is not None:
                staff_member.lname = lname
            if username is not None:
                staff_member.username = username
            if password is not None:
                staff_member.password = hash_password(password)
            if PermissionID is not None:
                staff_member.PermissionID = PermissionID
            if mail is not None:
                staff_member.mail = mail
            if phone is not None:
                staff_member.phone = phone
            self.db.commit()
            self.db.refresh(staff_member)
        return staff_member

    def delete_staff_member(self, staffID: int) -> bool:
        staff_member = self.get_staff_member(staffID)
        if staff_member:
            self.db.delete(staff_member)
            self.db.commit()
            return True
        return False