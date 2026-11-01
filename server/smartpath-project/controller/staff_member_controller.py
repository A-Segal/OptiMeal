from flask import Blueprint, request, jsonify
from repository.staff_memberRepository import StaffMemberRepository
from repository.delivery_assignmentRepository import DeliveryAssignmentRepository
from repository.recipient_request_repository import RecipientRequestRepository
from repository.recipientRepository import RecipientRepository
from repository.distribution_centerRepository import DistributionCenterRepository
from repository.VolunteerRepository import VolunteerRepository
from db_connection import SessionLocal
from dto.staff_memberDTO import StaffMemberDTO
from services.utils.googleMaps import reverse_geocode_address
from datetime import date, timedelta
from email.utils import parseaddr
import re

staff_bp = Blueprint('staff_bp', __name__, url_prefix='/staff')


_PHONE_REGEX = re.compile(r"^0\d{8,9}$")


def _is_valid_email(value: str) -> bool:
    """
    Pragmatic validation to avoid rejecting valid real-world addresses.
    """
    _, parsed = parseaddr(value)
    if not parsed or "@" not in parsed:
        return False

    local, _, domain = parsed.rpartition("@")
    if not local or not domain:
        return False

    if " " in local or " " in domain:
        return False

    # Keep it permissive but require a dotted domain in normal email format.
    return "." in domain and not domain.startswith(".") and not domain.endswith(".")


def _is_manager_request() -> bool:
    permission = request.headers.get('X-User-Permission', '')
    return permission == 'director'


def _format_address(entity) -> str | None:
    if entity is None:
        return None

    lat = getattr(entity, 'location_lat', None)
    lng = getattr(entity, 'location_lng', None)

    if lat is None or lng is None:
        return None

    address = reverse_geocode_address(float(lat), float(lng))
    if address:
        return address

    return f"{lat}, {lng}"


def _status_from_assignment(assignment) -> str:
    if assignment is None:
        return 'not_assigned'
    if getattr(assignment, 'VolunteerID', None):
        return 'assigned'
    return 'pending'


def _build_service_rows(target_date, service_date, requests, assignments_by_recipient, recipients, centers):
    rows = []

    for request_obj in requests:
        if not request_obj.request_date or request_obj.request_date.date() != target_date:
            continue

        assignment = assignments_by_recipient.get(request_obj.RecipientID)
        recipient = recipients.get(request_obj.RecipientID)
        center = centers.get(assignment.DistributionCenterID) if assignment else None
        status = _status_from_assignment(assignment)

        dest_address = _format_address(recipient)
        source_address = _format_address(center) if center else None

        rows.append({
            'recipient_id': request_obj.RecipientID,
            'recipient_username': recipient.username if recipient else None,
            'center_id': assignment.DistributionCenterID if assignment else None,
            'center_username': center.username if center else None,
            'meals': request_obj.amount_of_meals,
            'address': dest_address or '-',
            'source_address': source_address or '-',
            'request_date': request_obj.request_date.date().isoformat(),
            'service_date': service_date.isoformat(),
            'status': status,
            'status_label': {
                'assigned': 'שויך',
                'pending': 'ממתין',
                'not_assigned': 'לא שובץ',
            }[status],
        })

    return rows


def _build_unassigned_rows(rows):
    return [row for row in rows if row['status'] == 'not_assigned']


def _sum_unassigned_meals(rows):
    return sum(int(row['meals']) for row in rows if row['status'] == 'not_assigned')

# ===================== יצירת עובד =====================
@staff_bp.route('', methods=['POST'])
def add_staff_member():
    db_session = SessionLocal()
    try:
        staff_repo = StaffMemberRepository(db_session)
        data = request.get_json()
        new_staff = staff_repo.create_staff_member(
            fname=data['fname'],
            lname=data['lname'],
            username=data['username'],
            password=data['password'],
            PermissionID=data['PermissionID'],
            mail=data.get('mail'),
            phone=data.get('phone')
        )
        staff_dto = StaffMemberDTO(
            id=new_staff.id,
            fname=new_staff.fname,
            lname=new_staff.lname,
            username=new_staff.username,
            mail=new_staff.mail,
            phone=new_staff.phone,
            PermissionID=new_staff.PermissionID
        )
        return jsonify(staff_dto.__dict__), 201
    finally:
        db_session.close()


# ===================== קבלת עובד לפי ID =====================
@staff_bp.route('/<int:staff_id>', methods=['GET'])
def get_staff_member(staff_id):
    db_session = SessionLocal()
    try:
        staff_repo = StaffMemberRepository(db_session)
        staff = staff_repo.get_staff_member(staff_id)
        if staff is None:
            return jsonify({'error': 'Staff member not found'}), 404

        staff_dto = StaffMemberDTO(
            id=staff.id,
            fname=staff.fname,
            lname=staff.lname,
            username=staff.username,
            mail=staff.mail,
            phone=staff.phone,
            PermissionID=staff.PermissionID
        )
        return jsonify(staff_dto.__dict__)
    finally:
        db_session.close()


# ===================== קבלת כל העובדים =====================
@staff_bp.route('', methods=['GET'])
def get_all_staff_members():
    db_session = SessionLocal()
    try:
        staff_repo = StaffMemberRepository(db_session)
        staff_members = staff_repo.get_all_staff_members()
        staff_dtos = [
            StaffMemberDTO(
                id=s.id,
                fname=s.fname,
                lname=s.lname,
                username=s.username,
                mail=s.mail,
                phone=s.phone,
                PermissionID=s.PermissionID
            ).__dict__ for s in staff_members
        ]
        return jsonify(staff_dtos)
    finally:
        db_session.close()


@staff_bp.route('/dashboard_summary', methods=['GET'])
def get_staff_dashboard_summary():
    db_session = SessionLocal()
    try:
        staff_repo = StaffMemberRepository(db_session)
        delivery_repo = DeliveryAssignmentRepository(db_session)
        recipient_request_repo = RecipientRequestRepository(db_session)
        recipient_repo = RecipientRepository(db_session)
        center_repo = DistributionCenterRepository(db_session)

        today = date.today()
        tomorrow = today + timedelta(days=1)

        assignments = delivery_repo.get_all_delivery_assignments()
        recipient_requests = recipient_request_repo.get_all_requests()
        recipients = {r.id: r for r in recipient_repo.get_all_recipients()}
        centers = {c.id: c for c in center_repo.get_all_distribution_centers()}
        staff_members = staff_repo.get_all_staff_members()

        assignments_by_recipient = {
            assignment.RecipientID: assignment
            for assignment in assignments
        }

        todays_requests = _build_service_rows(
            today,
            tomorrow,
            recipient_requests,
            assignments_by_recipient,
            recipients,
            centers,
        )

        tomorrows_requests = _build_service_rows(
            tomorrow,
            tomorrow,
            recipient_requests,
            assignments_by_recipient,
            recipients,
            centers,
        )

        today_assigned = sum(1 for row in todays_requests if row['status'] != 'not_assigned')
        today_unassigned = sum(1 for row in todays_requests if row['status'] == 'not_assigned')
        tomorrow_assigned = sum(1 for row in tomorrows_requests if row['status'] != 'not_assigned')
        tomorrow_unassigned = sum(1 for row in tomorrows_requests if row['status'] == 'not_assigned')
        today_unassigned_rows = _build_unassigned_rows(todays_requests)
        tomorrow_unassigned_rows = _build_unassigned_rows(tomorrows_requests)

        return jsonify({
            'today_date': today.isoformat(),
            'tomorrow_date': tomorrow.isoformat(),
            'today_allocation': {
                'successful_assignments': today_assigned,
                'failed_assignments': today_unassigned,
                'status': 'idle' if not todays_requests else ('completed' if today_unassigned == 0 else 'partial'),
                'total_requests': len(todays_requests),
            },
            'tomorrow_allocation': {
                'successful_assignments': tomorrow_assigned,
                'failed_assignments': tomorrow_unassigned,
                'status': 'idle' if not tomorrows_requests else ('completed' if tomorrow_unassigned == 0 else 'partial'),
                'total_requests': len(tomorrows_requests),
            },
            'requests_for_today': todays_requests,
            'requests_for_tomorrow': tomorrows_requests,
            'unassigned_today': today_unassigned_rows,
            'unassigned_tomorrow': tomorrow_unassigned_rows,
            'today_stats': {
                'unassigned_requests': len(today_unassigned_rows),
                'unassigned_meals': _sum_unassigned_meals(todays_requests),
            },
            'tomorrow_stats': {
                'unassigned_requests': len(tomorrow_unassigned_rows),
                'unassigned_meals': _sum_unassigned_meals(tomorrows_requests),
            },
            'staff_overview': {
                'secretaries': sum(1 for member in staff_members if member.PermissionID != 1),
                'managers': sum(1 for member in staff_members if member.PermissionID == 1),
            }
        })
    finally:
        db_session.close()


@staff_bp.route('/system_users', methods=['GET'])
def get_system_users():
    db_session = SessionLocal()
    try:
        staff_repo = StaffMemberRepository(db_session)
        recipient_repo = RecipientRepository(db_session)
        center_repo = DistributionCenterRepository(db_session)
        volunteer_repo = VolunteerRepository(db_session)

        users = []

        users.extend([
            {
                'id': staff.id,
                'user_type': 'staff',
                'role_label': 'מנהל' if staff.PermissionID == 1 else 'מזכירות',
                'username': staff.username,
                'full_name': f"{staff.fname} {staff.lname}",
                'mail': staff.mail,
                'phone': staff.phone,
            }
            for staff in staff_repo.get_all_staff_members()
        ])

        users.extend([
            {
                'id': recipient.id,
                'user_type': 'recipient',
                'role_label': 'מוטב',
                'username': recipient.username,
                'full_name': f"{recipient.fname} {recipient.lname}",
                'mail': recipient.mail,
                'phone': recipient.phone,
            }
            for recipient in recipient_repo.get_all_recipients()
        ])

        users.extend([
            {
                'id': center.id,
                'user_type': 'distribution_center',
                'role_label': 'מרכז חלוקה',
                'username': center.username,
                'full_name': f"{center.fname} {center.lname}",
                'mail': center.mail,
                'phone': center.phone,
            }
            for center in center_repo.get_all_distribution_centers()
        ])

        users.extend([
            {
                'id': volunteer.id,
                'user_type': 'volunteer',
                'role_label': 'מתנדב',
                'username': volunteer.username,
                'full_name': f"{volunteer.fname} {volunteer.lname}",
                'mail': volunteer.mail,
                'phone': volunteer.phone,
            }
            for volunteer in volunteer_repo.get_all_volunteers()
        ])

        return jsonify(users)
    finally:
        db_session.close()


@staff_bp.route('/system_users/<string:user_type>/<int:user_id>', methods=['DELETE'])
def delete_system_user(user_type, user_id):
    if not _is_manager_request():
        return jsonify({'error': 'Manager permissions required'}), 403

    db_session = SessionLocal()
    try:
        staff_repo = StaffMemberRepository(db_session)
        recipient_repo = RecipientRepository(db_session)
        center_repo = DistributionCenterRepository(db_session)
        volunteer_repo = VolunteerRepository(db_session)

        if user_type == 'staff':
            success = staff_repo.delete_staff_member(user_id)
        elif user_type == 'recipient':
            success = recipient_repo.delete_recipient(user_id)
        elif user_type == 'distribution_center':
            success = center_repo.delete_distribution_center(user_id)
        elif user_type == 'volunteer':
            success = volunteer_repo.delete_volunteer(user_id)
        else:
            return jsonify({'error': 'Unsupported user type'}), 400

        if not success:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'message': 'User deleted successfully'})
    finally:
        db_session.close()


@staff_bp.route('/manager_create_user', methods=['POST'])
def manager_create_user():
    if not _is_manager_request():
        return jsonify({'error': 'Manager permissions required'}), 403

    db_session = SessionLocal()
    try:
        staff_repo = StaffMemberRepository(db_session)
        recipient_repo = RecipientRepository(db_session)

        data = request.get_json() or {}
        if not isinstance(data, dict):
            return jsonify({'error': 'פורמט בקשה לא תקין'}), 400

        role_type = str(data.get('role_type') or '').strip().lower()
        fname = str(data.get('fname') or '').strip()
        lname = str(data.get('lname') or '').strip()
        username = str(data.get('username') or '').strip()
        password = str(data.get('password') or '').strip()
        mail = str(data.get('mail') or '').strip() or None
        phone = str(data.get('phone') or '').strip() or None

        if role_type not in ('secretary', 'regular_user'):
            return jsonify({'error': 'Invalid role type'}), 400

        if not fname or not lname or not username or not password:
            return jsonify({'error': 'יש למלא את כל שדות החובה'}), 400

        if mail and not _is_valid_email(mail):
            return jsonify({'error': 'פורמט אימייל לא תקין'}), 400

        if phone and not _PHONE_REGEX.match(phone):
            return jsonify({'error': 'פורמט טלפון לא תקין'}), 400

        if staff_repo.get_by_username(username) or recipient_repo.get_by_username(username):
            return jsonify({'error': 'Username already exists'}), 409

        if role_type == 'secretary':
            created = staff_repo.create_staff_member(
                fname=fname,
                lname=lname,
                username=username,
                password=password,
                PermissionID=2,
                mail=mail,
                phone=phone,
            )

            return jsonify({
                'id': created.id,
                'role': 'staff',
                'role_label': 'מזכירות',
                'permission': 'מזכירות',
                'fname': created.fname,
                'lname': created.lname,
                'username': created.username,
                'mail': created.mail,
                'phone': created.phone,
            }), 201

        created = recipient_repo.create_recipient(
            fname=fname,
            lname=lname,
            username=username,
            password=password,
            mail=mail,
            phone=phone,
            location_lat=None,
            location_lng=None,
        )

        return jsonify({
            'id': created.id,
            'role': 'recipient',
            'role_label': 'משתמש רגיל',
            'fname': created.fname,
            'lname': created.lname,
            'username': created.username,
            'mail': created.mail,
            'phone': created.phone,
        }), 201
    finally:
        db_session.close()


# ===================== עדכון עובד =====================
@staff_bp.route('/<int:staff_id>', methods=['PUT'])
def update_staff_member(staff_id):
    db_session = SessionLocal()
    try:
        staff_repo = StaffMemberRepository(db_session)
        data = request.get_json()
        updated_staff = staff_repo.update_staff_member(
            staff_id,
            fname=data.get('fname'),
            lname=data.get('lname'),
            username=data.get('username'),
            password=data.get('password'),
            PermissionID=data.get('PermissionID'),
            mail=data.get('mail'),
            phone=data.get('phone')
        )
        if updated_staff is None:
            return jsonify({'error': 'Staff member not found'}), 404

        staff_dto = StaffMemberDTO(
            id=updated_staff.id,
            fname=updated_staff.fname,
            lname=updated_staff.lname,
            username=updated_staff.username,
            mail=updated_staff.mail,
            phone=updated_staff.phone,
            PermissionID=updated_staff.PermissionID
        )
        return jsonify(staff_dto.__dict__)
    finally:
        db_session.close()


# ===================== מחיקת עובד =====================
@staff_bp.route('/<int:staff_id>', methods=['DELETE'])
def delete_staff_member(staff_id):
    db_session = SessionLocal()
    try:
        staff_repo = StaffMemberRepository(db_session)
        success = staff_repo.delete_staff_member(staff_id)
        if not success:
            return jsonify({'error': 'Staff member not found'}), 404
        return jsonify({'message': 'Staff member deleted successfully'})
    finally:
        db_session.close()