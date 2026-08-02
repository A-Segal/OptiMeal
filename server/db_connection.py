from models.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.delivery_assignment import DeliveryAssignment
from models.distribution_center import DistributionCenter
from models.DC_request import DC_Request
from models.recipient_request import RecipientRequest
from models.recipient import Recipient
from models.volunteer import Volunteer
from models.permission import Permission
from models.staff_member import StaffMember
from models.vehicle import Vehicle

SERVER = 'localhost'
DATABASE = 'deliveryDB'
DRIVER = 'ODBC Driver 17 for SQL Server'

# חיבור ל-SQL Server דרך SQLAlchemy
connection_string = f"mssql+pyodbc://@{SERVER}/{DATABASE}?driver={DRIVER.replace(' ', '+')}&trusted_connection=yes"
engine = create_engine(connection_string, echo=True)
Base.metadata.create_all(bind=engine)
# יצירת סשן
SessionLocal = sessionmaker(bind=engine)


def get_session():
    return SessionLocal()
