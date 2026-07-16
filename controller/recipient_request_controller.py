

from flask import Blueprint, request, jsonify
from repository.recipient_request_repository import RecipientRequestRepository
from db_connection import SessionLocal
from dto.recipient_requestDTO import RecipientRequestDTO
from datetime import datetime

# יצירת Blueprint עבור Recipient_Request
recipient_request_bp = Blueprint('recipient_request_bp', __name__, url_prefix='/recipient_request')


# ===================== יצירת בקשה חדשה (POST) =====================
@recipient_request_bp.route('', methods=['POST'])
def add_recipient_request():
    db_session = SessionLocal()
    try:
        repo = RecipientRequestRepository(db_session)
        data = request.get_json()

        req_date = data.get('request_date')
        if req_date:
            try:
                if isinstance(req_date, str):
                    req_date = datetime.fromisoformat(req_date.replace('Z', '+00:00'))
                else:
                    req_date = datetime.now()
            except:
                req_date = datetime.now()
        else:
            req_date = datetime.now()

        new_request = repo.create_request(
            recipient_id=data['RecipientID'],
            amount_of_meals=data['amount_of_meals'],
            request_date=req_date
        )

        # שימוש ב-DTO
        request_dto = RecipientRequestDTO(
            id=new_request.id,
            RecipientID=new_request.RecipientID,
            amount_of_meals=new_request.amount_of_meals,
            request_date=new_request.request_date.isoformat() if new_request.request_date else None
        )

        return jsonify(request_dto.__dict__), 201
    finally:
        db_session.close()

# ===================== קבלת כל הבקשות (GET) =====================
@recipient_request_bp.route('', methods=['GET'])
def get_all_recipient_requests():
    db_session = SessionLocal()
    try:
        repo = RecipientRequestRepository(db_session)
        all_requests = repo.get_all_requests()

        # ממיר כל אובייקט ל-DTO
        all_requests_dto = [
            RecipientRequestDTO(
                id=req.id,
                RecipientID=req.RecipientID,
                amount_of_meals=req.amount_of_meals,
                request_date=req.request_date.isoformat() if req.request_date else None
            ).__dict__ for req in all_requests
        ]

        return jsonify(all_requests_dto)
    finally:
        db_session.close()
# ===================== קבלת בקשה לפי ID (GET) =====================
@recipient_request_bp.route('/<int:request_id>', methods=['GET'])
def get_recipient_request(request_id):
    db_session = SessionLocal()
    try:
        repo = RecipientRequestRepository(db_session)
        request_obj = repo.get_request(request_id)
        if request_obj is None:
            return jsonify({'error': 'בקשה לא נמצאה'}), 404

        request_dto = RecipientRequestDTO(
            id=request_obj.id,
            RecipientID=request_obj.RecipientID,
            amount_of_meals=request_obj.amount_of_meals,
            request_date=request_obj.request_date
        )

        return jsonify(request_dto.__dict__)
    finally:
        db_session.close()


# ===================== עדכון בקשה (PUT) =====================
@recipient_request_bp.route('/<int:request_id>', methods=['PUT'])
def update_recipient_request(request_id):
    db_session = SessionLocal()
    try:
        repo = RecipientRequestRepository(db_session)
        data = request.get_json()

        updated_request = repo.update_request(
            request_id,
            amount_of_meals=data.get('amount_of_meals'),
            request_date=datetime.fromisoformat(data['request_date']) if data.get('request_date') else None
        )

        if updated_request is None:
            return jsonify({'error': 'בקשה לא נמצאה'}), 404

        request_dto = RecipientRequestDTO(
            id=updated_request.id,
            RecipientID=updated_request.RecipientID,
            amount_of_meals=updated_request.amount_of_meals,
            request_date=updated_request.request_date
        )

        return jsonify(request_dto.__dict__)
    finally:
        db_session.close()


# ===================== מחיקת בקשה (DELETE) =====================
@recipient_request_bp.route('/<int:request_id>', methods=['DELETE'])
def delete_recipient_request(request_id):
    db_session = SessionLocal()
    try:
        repo = RecipientRequestRepository(db_session)
        success = repo.delete_request(request_id)
        if not success:
            return jsonify({'error': 'בקשה לא נמצאה'}), 404
        return jsonify({'message': 'הבקשה נמחקה בהצלחה'})
    finally:
        db_session.close()