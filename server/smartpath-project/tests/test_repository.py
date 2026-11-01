from models.base import Base
from repository.VehicleRepository import VehicleRepository
from repository.VolunteerRepository import VolunteerRepository
from db_connection import SessionLocal, engine

# ---- הגדרות חיבור ----

Base.metadata.create_all(engine)
db_session=SessionLocal()

repo = VolunteerRepository(db_session)

vehicle_repo = VehicleRepository(db_session)
volunteer_repo = VolunteerRepository(db_session)
volunteer_repo.vehicle_repo = vehicle_repo

# # ---- CREATE ----
new_volunteer = volunteer_repo.create_volunteer(
    fname="ddddddddd",
    lname="dddddd",
    username="ddd",
    password="333",
    vehicle_capacity=7,
    mail="as@example.com",
    phone="2222222"
)
print(f"נוצר Volunteer עם ID: {new_volunteer.id}, שם: {new_volunteer.fname} {new_volunteer.lname}")

# ---- READ ----
fetched_volunteer = volunteer_repo.get_volunteer(new_volunteer.id)
print(f"נשלף Volunteer עם שם משתמש: {fetched_volunteer.username}")

# ---- UPDATE ----
updated_volunteer = volunteer_repo.update_volunteer(
    volunteerID=new_volunteer.id,
    fname="Johnny",
    phone="0527654321"
)
print(f"עודכן Volunteer: {updated_volunteer.fname}, טלפון: {updated_volunteer.phone}")

# ---- GET ALL ----
all_volunteers = volunteer_repo.get_all_volunteers()
print(f"מספר כל המתנדבים: {len(all_volunteers)}")

# ---- בדיקת Vehicle אוטומטי ----
vehicles = vehicle_repo.get_all_vehicles()
for v in vehicles:
    print(f"Vehicle ID: {v.id}, VolunteerID: {v.VolunteerID}, Capacity: {v.capacity}")

# ---- DELETE ----
deleted = volunteer_repo.delete_volunteer(new_volunteer.id)
print(f"נמחק Volunteer: {deleted}")












# ---- CLOSE SESSION ----
db_session.close()