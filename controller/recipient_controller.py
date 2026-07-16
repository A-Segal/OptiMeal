from flask import Blueprint, request, jsonify
from repository.recipientRepository import RecipientRepository
from db_connection import SessionLocal
from dto.recipientDTO import RecipientDTO
from services.utils.googleMaps import geocode_address
# Blueprint עבור Recipients
recipient_bp = Blueprint('recipient_bp', __name__, url_prefix='/recipients')

def recipient_to_dto(recipient):
    return RecipientDTO(
        id=recipient.id,
        fname=recipient.fname,
        lname=recipient.lname,
        username=recipient.username,
        mail=recipient.mail,
        phone=recipient.phone,
        location_lat=recipient.location_lat,
        location_lng=recipient.location_lng
    )

# יצירת Recipient חדש
@recipient_bp.route('', methods=['POST'])
def add_recipient():
    db_session = SessionLocal()
    try:
        repo = RecipientRepository(db_session)
        data = request.get_json()

        lat = data.get('location_lat')
        lng = data.get('location_lng')

        # אם נשלחה כתובת טקסט
        if data.get('address'):
            geo = geocode_address(data['address'])
            if "error" in geo:
                return jsonify({"error": "כתובת לא תקינה"}), 400

            lat = geo['lat']
            lng = geo['lng']

        new_recipient = repo.create_recipient(
            fname=data['fname'],
            lname=data['lname'],
            username=data['username'],
            password=data['password'],
            mail=data.get('mail'),
            phone=data.get('phone'),
            location_lat=lat,
            location_lng=lng
        )

        dto = recipient_to_dto(new_recipient)
        return jsonify(dto.__dict__), 201

    finally:
        db_session.close()

# קבלת Recipient לפי ID
@recipient_bp.route('/<int:recipient_id>', methods=['GET'])
def get_recipient(recipient_id):
    db_session = SessionLocal()
    try:
        repo = RecipientRepository(db_session)
        recipient = repo.get_recipient(recipient_id)
        if recipient is None:
            return jsonify({'error': 'Recipient not found'}), 404
        dto = recipient_to_dto(recipient)
        return jsonify(dto.__dict__)
    finally:
        db_session.close()



# קבלת כל ה-Recipients
@recipient_bp.route('', methods=['GET'])
def get_all_recipients():
    db_session = SessionLocal()
    try:
        repo = RecipientRepository(db_session)
        recipients = repo.get_all_recipients()
        result = [recipient_to_dto(r).__dict__ for r in recipients]
        return jsonify(result)
    finally:
        db_session.close()

# עדכון Recipient
@recipient_bp.route('/<int:recipient_id>', methods=['PUT'])
def update_recipient(recipient_id):
    db_session = SessionLocal()
    try:
        repo = RecipientRepository(db_session)
        data = request.get_json()
        lat = data.get('location_lat')
        lng = data.get('location_lng')

        # אם נשלחה כתובת טקסט — geocode
        if data.get('address'):
            geo = geocode_address(data['address'])
            if "error" in geo:
                return jsonify({'error': f"הכתובת לא נמצאה: {data['address']}"}), 400
            lat = geo['lat']
            lng = geo['lng']

        updated_recipient = repo.update_recipient(
            recipientID=recipient_id,
            fname=data.get('fname'),
            lname=data.get('lname'),
            username=data.get('username'),
            password=data.get('password'),
            mail=data.get('mail'),
            phone=data.get('phone'),
            location_lat=lat,
            location_lng=lng
        )
        if updated_recipient is None:
            return jsonify({'error': 'Recipient not found'}), 404
        dto = recipient_to_dto(updated_recipient)
        return jsonify(dto.__dict__)
    finally:
        db_session.close()

# מחיקת Recipient
@recipient_bp.route('/<int:recipient_id>', methods=['DELETE'])
def delete_recipient(recipient_id):
    db_session = SessionLocal()
    try:
        repo = RecipientRepository(db_session)
        success = repo.delete_recipient(recipient_id)
        if not success:
            return jsonify({'error': 'Recipient not found'}), 404
        return jsonify({'message': 'Recipient deleted successfully'})
    finally:
        db_session.close()