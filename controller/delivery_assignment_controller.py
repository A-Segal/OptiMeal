from flask import Blueprint, request, jsonify
from repository.delivery_assignmentRepository import DeliveryAssignmentRepository
from repository.distribution_centerRepository import DistributionCenterRepository
from repository.recipientRepository import RecipientRepository
from repository.recipient_request_repository import RecipientRequestRepository
from db_connection import SessionLocal
from dto.delivery_assignmentDTO import DeliveryAssignmentDTO
from typing import List
from datetime import date
from services.delivery_assignment_service import create_assignments_from_matching_and_get_results


# Blueprint עבור DeliveryAssignment
delivery_assignment_bp = Blueprint('delivery_assignment_bp', __name__, url_prefix='/delivery_assignment')
@delivery_assignment_bp.route('/run_matching', methods=['POST'])
def run_matching_and_create_assignments():
    """
    מפעיל את אלגוריתם השיבוץ, מכניס את ההקצאות לטבלת DeliveryAssignment,
    ומחזיר תוצאות מפורטות + סטטיסטיקות.
    """
    try:
        result = create_assignments_from_matching_and_get_results()

        db = SessionLocal()
        try:
            # סטטיסטיקות נוספות
            rr_repo = RecipientRequestRepository(db)
            all_reqs = rr_repo.get_all_requests()
            today_requests = [r for r in all_reqs if r.request_date.date() == date.today()]
            total_requested = len(today_requests)
            total_assigned = result["created_count"]

            # ספירת מרכזים ייחודיים
            unique_centers = len(set(a["center_id"] for a in result["assignments"]))

            return jsonify({
                "message": f"{total_assigned} שיבוצים נוצרו בהצלחה",
                "created_count": total_assigned,
                "total_requested_today": total_requested,
                "unassigned": total_requested - total_assigned,
                "unique_centers_used": unique_centers,
                "assignments": result["assignments"]
            }), 201
        finally:
            db.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== קבלת משלוח לפי ID (GET) ====================
@delivery_assignment_bp.route('/<int:assignment_id>', methods=['GET'])
def get_delivery_assignment(assignment_id):
    db_session = SessionLocal()
    try:
        repo = DeliveryAssignmentRepository(db_session)
        assignment = repo.get_delivery_assignment(assignment_id)
        if not assignment:
            return jsonify({'error': 'DeliveryAssignment not found'}), 404

        dto = DeliveryAssignmentDTO(
            id=assignment.id,
            DistributionCenterID=assignment.DistributionCenterID,
            RecipientID=assignment.RecipientID,
            VolunteerID=assignment.VolunteerID,
            amount_of_meals=assignment.amount_of_meals,
            freshness_priority=assignment.freshness_priority
        )

        return jsonify(dto.__dict__)
    finally:
        db_session.close()


# ==================== קבלת כל המשלוחים (GET all) ====================
@delivery_assignment_bp.route('', methods=['GET'])
def get_all_delivery_assignments():
    db_session = SessionLocal()
    try:
        repo = DeliveryAssignmentRepository(db_session)
        assignments = repo.get_all_delivery_assignments()

        all_dto: List[dict] = [
            DeliveryAssignmentDTO(
                id=a.id,
                DistributionCenterID=a.DistributionCenterID,
                RecipientID=a.RecipientID,
                VolunteerID=a.VolunteerID,
                amount_of_meals=a.amount_of_meals,
                freshness_priority=a.freshness_priority
            ).__dict__ for a in assignments
        ]

        return jsonify(all_dto)
    finally:
        db_session.close()


# ==================== עדכון משלוח (PUT) ====================
@delivery_assignment_bp.route('/<int:assignment_id>', methods=['PUT'])
def update_delivery_assignment(assignment_id):
    db_session = SessionLocal()
    try:
        repo = DeliveryAssignmentRepository(db_session)
        data = request.get_json()

        updated = repo.update_delivery_assignment(
            assignmentID=assignment_id,
            DistributionCenterID=data.get('DistributionCenterID'),
            RecipientID=data.get('RecipientID'),
            VolunteerID=data.get('VolunteerID'),
            amount_of_meals=data.get('amount_of_meals'),
            freshness_priority=data.get('freshness_priority')
        )

        if not updated:
            return jsonify({'error': 'DeliveryAssignment not found'}), 404

        dto = DeliveryAssignmentDTO(
            id=updated.id,
            DistributionCenterID=updated.DistributionCenterID,
            RecipientID=updated.RecipientID,
            VolunteerID=updated.VolunteerID,
            amount_of_meals=updated.amount_of_meals,
            freshness_priority=updated.freshness_priority
        )

        return jsonify(dto.__dict__)
    finally:
        db_session.close()


# ==================== מחיקת משלוח (DELETE) ====================
@delivery_assignment_bp.route('/<int:assignment_id>', methods=['DELETE'])
def delete_delivery_assignment(assignment_id):
    db_session = SessionLocal()
    try:
        repo = DeliveryAssignmentRepository(db_session)
        success = repo.delete_delivery_assignment(assignment_id)
        if not success:
            return jsonify({'error': 'DeliveryAssignment not found'}), 404
        return jsonify({'message': 'DeliveryAssignment deleted successfully'})
    finally:
        db_session.close()
