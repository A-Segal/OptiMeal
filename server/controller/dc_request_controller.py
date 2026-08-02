from flask import Blueprint, request, jsonify
from repository.DC_request_Repository import DCRequestRepository
from db_connection import SessionLocal
from dto.DC_requestDTO import DCRequestDTO
from datetime import datetime

# Blueprint עבור DS Requests
dc_request_bp = Blueprint('dc_request_bp', __name__, url_prefix='/dc_requests')


# ===================== יצירת בקשה =====================
@dc_request_bp.route('', methods=['POST'])
def add_request():
    db_session = SessionLocal()
    try:
        repo = DCRequestRepository(db_session)
        data = request.get_json()

        request_date = data.get('request_date')
        if request_date:
            try:
                # תומך גם ב-ISO string וגם ב-Date object מה-JSON
                if isinstance(request_date, str):
                    request_date = datetime.fromisoformat(request_date.replace('Z', '+00:00'))
                else:
                    request_date = datetime.now()
            except:
                request_date = datetime.now()
        else:
            request_date = datetime.now()

        freshness_priority = data.get('freshness_priority', 0)
        req_type = data.get('type', data.get('meal_type', 0))

        new_request = repo.create_request(
            distribution_center_id=data['DistributionCenterID'],
            amount_of_meals=data['amount_of_meals'],
            type=req_type,
            request_date=request_date,
            freshness_priority=freshness_priority
        )

        dto = DCRequestDTO(
            id=new_request.id,
            DistributionCenterID=new_request.DistributionCenterID,
            amount_of_meals=new_request.amount_of_meals,
            request_date=new_request.request_date.isoformat(),
            type=req_type,
            freshness_priority=new_request.freshness_priority
        )
        return jsonify(dto.__dict__), 201
    finally:
        db_session.close()


# ===================== קבלת בקשה לפי ID =====================
@dc_request_bp.route('/<int:request_id>', methods=['GET'])
def get_request(request_id):
    db_session = SessionLocal()
    try:
        repo = DCRequestRepository(db_session)
        req = repo.get_request(request_id)
        if req is None:
            return jsonify({'error': 'Request not found'}), 404

        dto = DCRequestDTO(
            id=req.id,
            DistributionCenterID=req.DistributionCenterID,
            amount_of_meals=req.amount_of_meals,
            request_date=req.request_date.isoformat(),
            freshness_priority=req.freshness_priority,
            type=getattr(req, 'type', 0)
        )
        return jsonify(dto.__dict__)
    finally:
        db_session.close()


# ===================== קבלת כל הבקשות =====================
@dc_request_bp.route('', methods=['GET'])
def get_all_requests():
    db_session = SessionLocal()
    try:
        repo = DCRequestRepository(db_session)
        all_requests = repo.get_all_requests()

        dto_list = [
            DCRequestDTO(
                id=r.id,
                DistributionCenterID=r.DistributionCenterID,
                amount_of_meals=r.amount_of_meals,
                request_date=r.request_date.isoformat(),
                freshness_priority=r.freshness_priority,
                type=getattr(r, 'type', 0)
            ).__dict__ for r in all_requests
        ]
        return jsonify(dto_list)
    finally:
        db_session.close()


# ===================== עדכון בקשה =====================
@dc_request_bp.route('/<int:request_id>', methods=['PUT'])
def update_request(request_id):
    db_session = SessionLocal()
    try:
        repo = DCRequestRepository(db_session)
        data = request.get_json()

        request_date = data.get('request_date')
        if request_date:
            request_date = datetime.fromisoformat(request_date)

        freshness_priority = data.get('freshness_priority', None)
        req_type = data.get('type', data.get('meal_type', None))

        updated_request = repo.update_request(
            request_id,
            amount_of_meals=data.get('amount_of_meals'),
            request_date=request_date,
            type=req_type,
            freshness_priority=freshness_priority
        )

        if updated_request is None:
            return jsonify({'error': 'Request not found'}), 404

        dto = DCRequestDTO(
            id=updated_request.id,
            DistributionCenterID=updated_request.DistributionCenterID,
            amount_of_meals=updated_request.amount_of_meals,
            request_date=updated_request.request_date.isoformat(),
            freshness_priority=updated_request.freshness_priority,
            type=getattr(updated_request, 'type', 0)
        )
        return jsonify(dto.__dict__)
    finally:
        db_session.close()


# ===================== מחיקת בקשה =====================
@dc_request_bp.route('/<int:request_id>', methods=['DELETE'])
def delete_request(request_id):
    db_session = SessionLocal()
    try:
        repo = DCRequestRepository(db_session)
        success = repo.delete_request(request_id)
        if not success:
            return jsonify({'error': 'Request not found'}), 404
        return jsonify({'message': 'Request deleted successfully'})
    finally:
        db_session.close()