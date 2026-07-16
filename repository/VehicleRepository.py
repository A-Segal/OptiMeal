from sqlalchemy.orm import Session
from models.vehicle import Vehicle

class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_vehicle(self, VolunteerID: int, capacity: int) -> Vehicle:
        vehicle = Vehicle(VolunteerID=VolunteerID, capacity=capacity)
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def get_vehicle(self, vehicleID: int) -> Vehicle | None:
        return self.db.query(Vehicle).filter(Vehicle.id == vehicleID).first()

    def get_all_vehicles(self) -> list[Vehicle]:
        return self.db.query(Vehicle).all()

    def update_vehicle(self, vehicleID: int, capacity: int) -> Vehicle | None:
        vehicle = self.get_vehicle(vehicleID)
        if vehicle:
            vehicle.capacity = capacity
            self.db.commit()
            self.db.refresh(vehicle)
        return vehicle

    def delete_vehicle(self, vehicleID: int) -> bool:
        vehicle = self.get_vehicle(vehicleID)
        if vehicle:
            self.db.delete(vehicle)
            self.db.commit()
            return True
        return False
    def delete_vehicle_by_volunteer(self, volunteerID: int):
        vehicles = self.db.query(Vehicle).filter(Vehicle.VolunteerID == volunteerID).all()
        for vehicle in vehicles:
            self.db.delete(vehicle)
        self.db.commit()

    def get_by_volunteer_id(self, volunteer_id: int):
        return (
            self.db.query(Vehicle)
            .filter(Vehicle.VolunteerID == volunteer_id)
            .order_by(Vehicle.id.desc())
            .first()
        )