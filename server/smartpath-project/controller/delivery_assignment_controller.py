from flask import Blueprint, request, jsonify
from repository.delivery_assignmentRepository import DeliveryAssignmentRepository
from db_connection import SessionLocal
from dto.delivery_assignmentDTO import DeliveryAssignmentDTO  # נניח שיש קובץ DTO
from typing import List
from services.delivery_assignment_service import create_assignments_from_matching
from services.utils.googleMaps import reverse_geocode_address
from repository.recipientRepository import RecipientRepository
from repository.distribution_centerRepository import DistributionCenterRepository


# Blueprint עבור DeliveryAssignment
delivery_assignment_bp = Blueprint('delivery_assignment_bp', __name__, url_prefix='/delivery_assignment')


@delivery_assignment_bp.route('', methods=['POST'])
def create_delivery_assignment():
    db_session = SessionLocal()
    try:
        data = request.get_json() or {}
        repo = DeliveryAssignmentRepository(db_session)

        created = repo.create_delivery_assignment(
            DistributionCenterID=data.get('DistributionCenterID'),
            RecipientID=data.get('RecipientID'),
            VolunteerID=data.get('VolunteerID'),
            amount_of_meals=data.get('amount_of_meals'),
            freshness_priority=data.get('freshness_priority', 0)
        )

        dto = DeliveryAssignmentDTO(
            id=created.id,
            DistributionCenterID=created.DistributionCenterID,
            RecipientID=created.RecipientID,
            VolunteerID=created.VolunteerID,
            amount_of_meals=created.amount_of_meals,
            freshness_priority=created.freshness_priority
        )
        return jsonify(dto.__dict__), 201
    finally:
        db_session.close()


@delivery_assignment_bp.route('/run_matching', methods=['POST'])
def run_matching_and_create_assignments():
    """
    מפעיל את אלגוריתם השיבוץ ומכניס את ההקצאות לטבלת DeliveryAssignment
    """
    try:
        result = create_assignments_from_matching()
        return jsonify(result), 201
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

        recipient_repo = RecipientRepository(db_session)
        center_repo = DistributionCenterRepository(db_session)
        recipients = {r.id: r for r in recipient_repo.get_all_recipients()}
        centers = {c.id: c for c in center_repo.get_all_distribution_centers()}

        all_dto: List[dict] = []
        for a in assignments:
            recipient = recipients.get(a.RecipientID)
            center = centers.get(a.DistributionCenterID)
            address = None
            if recipient and recipient.location_lat is not None and recipient.location_lng is not None:
                address = reverse_geocode_address(float(recipient.location_lat), float(recipient.location_lng))
            elif center and center.location_lat is not None and center.location_lng is not None:
                address = reverse_geocode_address(float(center.location_lat), float(center.location_lng))

            dto = DeliveryAssignmentDTO(
                id=a.id,
                DistributionCenterID=a.DistributionCenterID,
                RecipientID=a.RecipientID,
                VolunteerID=a.VolunteerID,
                amount_of_meals=a.amount_of_meals,
                freshness_priority=a.freshness_priority
            ).__dict__
            dto.update({
                "recipient_username": recipient.username if recipient else None,
                "center_username": center.username if center else None,
                "address": address,
            })
            all_dto.append(dto)

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
