from dto.volunteer_requestDTO import VolunteerRequestDTO
from typing import List
from flask import Blueprint, request, jsonify
from flask import Blueprint, jsonify
from db_connection import SessionLocal
from repository.Volunteer_requestRepository import VolunteerRequestRepository
from services.utils.googleMaps import travel_time_between_points
from services.volunteer_route_service import run_volunteer_route



from repository.VolunteerRepository import VolunteerRepository
from repository.delivery_assignmentRepository import DeliveryAssignmentRepository
from services.vrp.solver import solve
# from services.volunteer_route_service import run_volunteer_route
volunteer_request_bp = Blueprint(
    'volunteer_request_bp',
    __name__,
    url_prefix='/volunteer_request'
)



# ==================== יצירת בקשה (POST) ====================
@volunteer_request_bp.route('/run_route/<int:volunteer_id>', methods=['POST'])
def run_route(volunteer_id):
    db = SessionLocal()

    try:
        data = request.get_json(silent=True) or {}
        address = data.get("address")
        available_time = data.get("available_time")  # שעות (float)

        volunteer_repo = VolunteerRepository(db)
        assignment_repo = DeliveryAssignmentRepository(db)

        # מיקום התחלתי — או מכתובת, או מ-VolunteerRequest, או מה-body
        start_loc = None
        if not address:
            if data.get("lat") and data.get("lng"):
                start_loc = {"lat": float(data["lat"]), "lng": float(data["lng"])}
            else:
                # נסה לקחת מה-VolunteerRequest העדכני ביותר
                vr_repo = VolunteerRequestRepository(db)
                vr = vr_repo.get_by_volunteer_id(volunteer_id)
                if vr and vr.location_lat and vr.location_lng:
                    start_loc = {"lat": float(vr.location_lat), "lng": float(vr.location_lng)}
                    if not available_time:
                        available_time = vr.available_time

        result = run_volunteer_route(
            volunteer_id=volunteer_id,
            volunteer_repo=volunteer_repo,
            assignment_repo=assignment_repo,
            google_maps_service=travel_time_between_points,
            start_address=address,
            start_location_param=start_loc,
            available_time=available_time,
        )

        return jsonify(result), 200

    finally:
        db.close()
# ==================== קבלת בקשה לפי ID (GET) ====================
@volunteer_request_bp.route('/<int:request_id>', methods=['GET'])
def get_volunteer_request(request_id):
    db_session = SessionLocal()
    try:
        repo = VolunteerRequestRepository(db_session)
        request_obj = repo.get_volunteer_request(request_id)

        if not request_obj:
            return jsonify({'error': 'VolunteerRequest not found'}), 404

        dto = VolunteerRequestDTO(
            id=request_obj.id,
            volunteer_id=request_obj.volunteer_id,
            location_lat=request_obj.location_lat,
            location_lng=request_obj.location_lng,
            available_time=request_obj.available_time
        )

        return jsonify(dto.__dict__)
    finally:
        db_session.close()


# ==================== קבלת כל הבקשות (GET all) ====================
@volunteer_request_bp.route('', methods=['GET'])
def get_all_volunteer_requests():
    db_session = SessionLocal()
    try:
        repo = VolunteerRequestRepository(db_session)
        requests = repo.get_all_volunteer_requests()

        all_dto: List[dict] = [
            VolunteerRequestDTO(
                id=r.id,
                volunteer_id=r.volunteer_id,
                location_lat=r.location_lat,
                location_lng=r.location_lng,
                available_time=r.available_time
            ).__dict__ for r in requests
        ]

        return jsonify(all_dto)
    finally:
        db_session.close()


# ==================== עדכון בקשה (PUT) ====================
@volunteer_request_bp.route('/<int:request_id>', methods=['PUT'])
def update_volunteer_request(request_id):
    db_session = SessionLocal()
    try:
        repo = VolunteerRequestRepository(db_session)
        data = request.get_json()

        updated = repo.update_volunteer_request(
            request_id=request_id,
            volunteer_id=data.get('volunteer_id'),
            location_lat=data.get('location_lat'),
            location_lng=data.get('location_lng'),
            available_time=data.get('available_time')
        )

        if not updated:
            return jsonify({'error': 'VolunteerRequest not found'}), 404

        dto = VolunteerRequestDTO(
            id=updated.id,
            volunteer_id=updated.volunteer_id,
            location_lat=updated.location_lat,
            location_lng=updated.location_lng,
            available_time=updated.available_time
        )

        return jsonify(dto.__dict__)
    finally:
        db_session.close()


# ==================== מחיקת בקשה (DELETE) ====================
@volunteer_request_bp.route('/<int:request_id>', methods=['DELETE'])
def delete_volunteer_request(request_id):
    db_session = SessionLocal()
    try:
        repo = VolunteerRequestRepository(db_session)
        success = repo.delete_volunteer_request(request_id)

        if not success:
            return jsonify({'error': 'VolunteerRequest not found'}), 404

        return jsonify({'message': 'VolunteerRequest deleted successfully'})
    finally:
        db_session.close()


# # =========================
# # Run VRP Route (MAIN ENDPOINT)
# # =========================
# @volunteer_request_bp.route('/run_route/<int:volunteer_id>', methods=['POST'])
# def run_route(volunteer_id):
#     db_session = SessionLocal()
#
#     try:
#         volunteer_repo = VolunteerRequestRepository(db_session)
#         group_repo = DeliveryAssignmentRepository(db_session)
#
#         result = run_volunteer_route(
#             volunteer_id=volunteer_id,
#             volunteer_repo=volunteer_repo,
#             group_repo=group_repo,
#             google_maps_service=travel_time_between_points
#         )
#
#         return jsonify(result), 200
#
#     finally:
#         db_session.close()