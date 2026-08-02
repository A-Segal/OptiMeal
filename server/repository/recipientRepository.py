from sqlalchemy.orm import Session
from models.recipient import Recipient
from services.utils.auth_utils import hash_password, verify_password

class RecipientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_recipient(
        self,
        fname: str,
        lname: str,
        username: str,
        password: str,
        mail: str = None,
        phone: str = None,
        location_lat: float = None,
        location_lng: float = None,

    ) -> Recipient:
        recipient = Recipient(
            fname=fname,
            lname=lname,
            username=username,
            password=hash_password(password),
            mail=mail,
            phone=phone,
            location_lat=location_lat,
            location_lng=location_lng,
        )
        self.db.add(recipient)
        self.db.commit()
        self.db.refresh(recipient)
        return recipient

    def get_recipient(self, recipientID: int) -> Recipient | None:
        return self.db.query(Recipient).filter(Recipient.id == recipientID).first()

    def get_by_username(self, username: str) -> Recipient | None:
        return self.db.query(Recipient).filter(Recipient.username == username).first()

    def get_by_username_password(self, username, password):
        """מחזיר recipient אם הסיסמה תואמת, אחרת None"""
        recipient = self.db.query(Recipient).filter_by(username=username).first()
        if recipient and verify_password(password, recipient.password):
            return recipient
        return None
    def get_all_recipients(self) -> list[Recipient]:
        return self.db.query(Recipient).all()

    def update_recipient(
        self,
        recipientID: int,
        fname: str = None,
        lname: str = None,
        username: str = None,
        password: str = None,
        mail: str = None,
        phone: str = None,
        location_lat: float = None,
        location_lng: float = None,
    ) -> Recipient | None:
        recipient = self.get_recipient(recipientID)
        if recipient:
            if fname is not None: recipient.fname = fname
            if lname is not None: recipient.lname = lname
            if username is not None: recipient.username = username
            if password is not None: recipient.password = hash_password(password)
            if mail is not None: recipient.mail = mail
            if phone is not None: recipient.phone = phone
            if location_lat is not None: recipient.location_lat = location_lat
            if location_lng is not None: recipient.location_lng = location_lng
            self.db.commit()
            self.db.refresh(recipient)
        return recipient

    def delete_recipient(self, recipientID: int) -> bool:
        recipient = self.get_recipient(recipientID)
        if recipient:
            self.db.delete(recipient)
            self.db.commit()
            return True
        return False