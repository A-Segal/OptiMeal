from flask import Blueprint, request, jsonify
from db_connection import SessionLocal

from repository.VolunteerRepository import VolunteerRepository
from repository.recipientRepository import RecipientRepository
from repository.distribution_centerRepository import DistributionCenterRepository
from repository.staff_memberRepository import StaffMemberRepository

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    db_session = SessionLocal()

    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return jsonify({"message": "username and password required"}), 400

        # ===================== VOLUNTEER =====================
        volunteer_repo = VolunteerRepository(db_session)
        volunteer = volunteer_repo.get_by_username_password(username, password)

        if volunteer:
            return jsonify({
                "id": volunteer.id,
                "role": "volunteer",
                "username": volunteer.username
            }), 200

        # ===================== RECIPIENT =====================
        recipient_repo = RecipientRepository(db_session)
        recipient = recipient_repo.get_by_username_password(username, password)

        if recipient:
            return jsonify({
                "id": recipient.id,
                "role": "recipient",
                "username": recipient.username
            }), 200

        # ===================== DISTRIBUTION CENTER =====================
        dc_repo = DistributionCenterRepository(db_session)
        dc = dc_repo.get_by_username_password(username, password)

        if dc:
            return jsonify({
                "id": dc.id,
                "role": "distribution_center",
                "username": dc.username
            }), 200

        # ===================== STAFF MEMBER =====================
        staff_repo = StaffMemberRepository(db_session)
        staff = staff_repo.get_by_username(username)
        print(f"[DEBUG STAFF] username='{username}', found={staff is not None}, PermissionID={getattr(staff, 'PermissionID', 'N/A')}")
        if staff:
            # בדיקת סיסמה
            from services.utils.auth_utils import verify_password
            if not verify_password(password, staff.password):
                return jsonify({"message": "Invalid password"}), 401

            # PermissionID=1 → director, כל השאר → מזכירות
            permission_type = "director" if staff.PermissionID == 1 else "מזכירות"

            return jsonify({
                "id": staff.id,
                "fname": staff.fname,
                "lname": staff.lname,
                "role": "staff",
                "username": staff.username,
                "permission": permission_type
            }), 200

        # ===================== NOT FOUND =====================
        return jsonify({"message": "User not found"}), 404

    finally:
        db_session.close()