

from flask import Blueprint, request, jsonify
from repository.VehicleRepository import VehicleRepository
from db_connection import SessionLocal
from dto.vehicleDTO import VehicleDTO

# Blueprint עבור Vehicles
vehicle_bp = Blueprint('vehicle_bp', __name__, url_prefix='/vehicles')

# ===================== רכב לפי מתנדב — GET via POST =====================
@vehicle_bp.route('/volunteer/<int:volunteer_id>/fetch', methods=['POST'])
def fetch_vehicle_by_volunteer(volunteer_id):
    db_session = SessionLocal()
    try:
        vehicle_repo = VehicleRepository(db_session)
        vehicle = vehicle_repo.get_by_volunteer_id(volunteer_id)
        if vehicle is None:
            return jsonify(None)
        vehicle_dto = VehicleDTO(
            id=vehicle.id,
            VolunteerID=vehicle.VolunteerID,
            capacity=vehicle.capacity
        )
        return jsonify(vehicle_dto.__dict__)
    finally:
        db_session.close()


# ===================== רכב לפי מתנדב — DELETE =====================
@vehicle_bp.route('/volunteer/<int:volunteer_id>', methods=['DELETE'])
def delete_vehicle_by_volunteer(volunteer_id):
    db_session = SessionLocal()
    try:
        vehicle_repo = VehicleRepository(db_session)

        if request.method == 'GET':
            vehicle = vehicle_repo.get_by_volunteer_id(volunteer_id)
            if vehicle is None:
                return jsonify({'error': 'Vehicle not found for this volunteer'}), 404
            vehicle_dto = VehicleDTO(
                id=vehicle.id,
                VolunteerID=vehicle.VolunteerID,
                capacity=vehicle.capacity
            )
            return jsonify(vehicle_dto.__dict__)

        if request.method == 'DELETE':
            vehicle_repo.delete_vehicle_by_volunteer(volunteer_id)
            return jsonify({'message': f'All vehicles for volunteer {volunteer_id} deleted successfully'})

    finally:
        db_session.close()


# ===================== Upsert רכב לפי מתנדב — PUT =====================
@vehicle_bp.route('/volunteer/<int:volunteer_id>/upsert', methods=['PUT'])
def upsert_vehicle_by_volunteer(volunteer_id):
    db_session = SessionLocal()
    try:
        vehicle_repo = VehicleRepository(db_session)
        data = request.get_json()
        capacity = data['capacity']
        existing = vehicle_repo.get_by_volunteer_id(volunteer_id)
        if existing:
            updated = vehicle_repo.update_vehicle(existing.id, capacity)
            vehicle_dto = VehicleDTO(
                id=updated.id,
                VolunteerID=updated.VolunteerID,
                capacity=updated.capacity
            )
        else:
            new_vehicle = vehicle_repo.create_vehicle(volunteer_id, capacity)
            vehicle_dto = VehicleDTO(
                id=new_vehicle.id,
                VolunteerID=new_vehicle.VolunteerID,
                capacity=new_vehicle.capacity
            )
        return jsonify(vehicle_dto.__dict__)
    finally:
        db_session.close()


# ===================== רכב לפי ID — GET, PUT, DELETE =====================
@vehicle_bp.route('/id/<int:vehicle_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_vehicle_by_id(vehicle_id):
    db_session = SessionLocal()
    try:
        vehicle_repo = VehicleRepository(db_session)

        if request.method == 'GET':
            vehicle = vehicle_repo.get_vehicle(vehicle_id)
            if vehicle is None:
                return jsonify({'error': 'Vehicle not found'}), 404
            vehicle_dto = VehicleDTO(
                id=vehicle.id,
                VolunteerID=vehicle.VolunteerID,
                capacity=vehicle.capacity
            )
            return jsonify(vehicle_dto.__dict__)

        if request.method == 'PUT':
            data = request.get_json()
            updated_vehicle = vehicle_repo.update_vehicle(
                vehicle_id,
                capacity=data['capacity']
            )
            if updated_vehicle is None:
                return jsonify({'error': 'Vehicle not found'}), 404
            vehicle_dto = VehicleDTO(
                id=updated_vehicle.id,
                VolunteerID=updated_vehicle.VolunteerID,
                capacity=updated_vehicle.capacity
            )
            return jsonify(vehicle_dto.__dict__)

        if request.method == 'DELETE':
            success = vehicle_repo.delete_vehicle(vehicle_id)
            if not success:
                return jsonify({'error': 'Vehicle not found'}), 404
            return jsonify({'message': 'Vehicle deleted successfully'})

    finally:
        db_session.close()


# ===================== כל הרכבים + יצירת רכב — GET, POST =====================
@vehicle_bp.route('', methods=['GET', 'POST'])
def handle_all_vehicles():
    db_session = SessionLocal()
    try:
        vehicle_repo = VehicleRepository(db_session)

        if request.method == 'GET':
            vehicles = vehicle_repo.get_all_vehicles()
            vehicles_dto = [
                VehicleDTO(
                    id=v.id,
                    VolunteerID=v.VolunteerID,
                    capacity=v.capacity
                ).__dict__ for v in vehicles
            ]
            return jsonify(vehicles_dto)

        if request.method == 'POST':
            data = request.get_json()
            new_vehicle = vehicle_repo.create_vehicle(
                VolunteerID=data['VolunteerID'],
                capacity=data['capacity']
            )
            vehicle_dto = VehicleDTO(
                id=new_vehicle.id,
                VolunteerID=new_vehicle.VolunteerID,
                capacity=new_vehicle.capacity
            )
            return jsonify(vehicle_dto.__dict__), 201

    finally:
        db_session.close()
