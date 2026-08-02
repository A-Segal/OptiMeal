from flask import Blueprint, request, jsonify
from repository.VolunteerRepository import VolunteerRepository
from db_connection import SessionLocal
from dto.volunteerDTO import VolunteerDTO

volunteer_bp = Blueprint('volunteer_bp', __name__, url_prefix='/volunteers')

# ===================== יצירת מתנדב =====================
@volunteer_bp.route('', methods=['POST'])
def add_volunteer():
    db_session = SessionLocal()
    try:
        volunteer_repo = VolunteerRepository(db_session)
        data = request.get_json()
        new_volunteer = volunteer_repo.create_volunteer(
            fname=data['fname'],
            lname=data['lname'],
            username=data['username'],
            password=data['password'],
            vehicle_capacity=data['vehicle_capacity'],
            mail=data.get('mail'),
            phone=data.get('phone')
        )

        volunteer_dto = VolunteerDTO(
            id=new_volunteer.id,
            fname=new_volunteer.fname,
            lname=new_volunteer.lname,
            username=new_volunteer.username,
            mail=new_volunteer.mail,
            phone=new_volunteer.phone
        )

        return jsonify(volunteer_dto.__dict__), 201
    finally:
        db_session.close()


# ===================== קבלת מתנדב לפי ID =====================
@volunteer_bp.route('/<int:volunteer_id>', methods=['GET'])
def get_volunteer(volunteer_id):
    db_session = SessionLocal()
    try:
        volunteer_repo = VolunteerRepository(db_session)
        volunteer = volunteer_repo.get_volunteer(volunteer_id)
        if volunteer is None:
            return jsonify({'error': 'Volunteer not found'}), 404

        volunteer_dto = VolunteerDTO(
            id=volunteer.id,
            fname=volunteer.fname,
            lname=volunteer.lname,
            username=volunteer.username,
            mail=volunteer.mail,
            phone=volunteer.phone
        )

        return jsonify(volunteer_dto.__dict__)
    finally:
        db_session.close()


# ===================== קבלת כל המתנדבים =====================
@volunteer_bp.route('', methods=['GET'])
def get_all_volunteers():
    db_session = SessionLocal()
    try:
        volunteer_repo = VolunteerRepository(db_session)
        volunteers = volunteer_repo.get_all_volunteers()

        volunteers_dto = [
            VolunteerDTO(
                id=v.id,
                fname=v.fname,
                lname=v.lname,
                username=v.username,
                mail=v.mail,
                phone=v.phone
            ).__dict__ for v in volunteers
        ]

        return jsonify(volunteers_dto)
    finally:
        db_session.close()


# ===================== עדכון מתנדב =====================
@volunteer_bp.route('/<int:volunteer_id>', methods=['PUT'])
def update_volunteer(volunteer_id):
    db_session = SessionLocal()
    try:
        volunteer_repo = VolunteerRepository(db_session)
        data = request.get_json()
        updated_volunteer = volunteer_repo.update_volunteer(
            volunteer_id,
            fname=data.get('fname'),
            lname=data.get('lname'),
            username=data.get('username'),
            password=data.get('password'),
            mail=data.get('mail'),
            phone=data.get('phone')
        )

        if updated_volunteer is None:
            return jsonify({'error': 'Volunteer not found'}), 404

        volunteer_dto = VolunteerDTO(
            id=updated_volunteer.id,
            fname=updated_volunteer.fname,
            lname=updated_volunteer.lname,
            username=updated_volunteer.username,
            mail=updated_volunteer.mail,
            phone=updated_volunteer.phone
        )

        return jsonify(volunteer_dto.__dict__)
    finally:
        db_session.close()


# ===================== מחיקת מתנדב =====================


@volunteer_bp.route('/<int:volunteer_id>', methods=['DELETE'])
def delete_volunteer(volunteer_id):
    db_session = SessionLocal()
    try:
        volunteer_repo = VolunteerRepository(db_session)
        success = volunteer_repo.delete_volunteer(volunteer_id)
        if not success:
            return jsonify({'error': 'Volunteer not found or could not be deleted'}), 404
        return jsonify({'message': 'Volunteer and related vehicles deleted successfully'})
    finally:
        db_session.close()