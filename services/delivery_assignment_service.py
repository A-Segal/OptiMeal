from db_connection import get_session
from repository.delivery_assignmentRepository import DeliveryAssignmentRepository
from repository.distribution_centerRepository import DistributionCenterRepository
from repository.recipientRepository import RecipientRepository
from repository.recipient_request_repository import RecipientRequestRepository
from services.batch_algoritm.execute_full_matching import execute_full_matching
from datetime import date


def create_assignments_from_matching():
    """
    שומר תוצאות שיבוץ ב-DB. מחזיר count.
    """
    assignments = execute_full_matching()
    db = get_session()
    try:
        repo = DeliveryAssignmentRepository(db)
        created_count = 0
        for recipient_id, assignment in assignments.items():
            repo.create_delivery_assignment(
                DistributionCenterID=assignment["center_id"],
                RecipientID=recipient_id,
                VolunteerID=None,
                amount_of_meals=assignment["recipient_meals"],
                freshness_priority=assignment.get("freshness_priority", 0)
            )
            created_count += 1
        return created_count
    finally:
        db.close()


def create_assignments_from_matching_and_get_results():
    """
    שומר תוצאות שיבוץ ב-DB וגם מחזיר מילון מפורט:
    { created_count, assignments: [{recipient_id, center_id, ...}] }
    """
    assignments = execute_full_matching()

    db = get_session()
    try:
        # שליפת נתונים להעשרת התוצאות
        center_repo = DistributionCenterRepository(db)
        recipient_repo = RecipientRepository(db)

        centers = {c.id: c for c in center_repo.get_all_distribution_centers()}
        recipients = {r.id: r for r in recipient_repo.get_all_recipients()}

        repo = DeliveryAssignmentRepository(db)
        created_count = 0
        enriched = []

        for recipient_id, assignment in assignments.items():
            repo.create_delivery_assignment(
                DistributionCenterID=assignment["center_id"],
                RecipientID=recipient_id,
                VolunteerID=None,
                amount_of_meals=assignment["recipient_meals"],
                freshness_priority=assignment.get("freshness_priority", 0)
            )
            created_count += 1

            center = centers.get(assignment["center_id"])
            recipient = recipients.get(recipient_id)

            enriched.append({
                "recipient_id": recipient_id,
                "recipient_name": f"{recipient.fname or ''} {recipient.lname or ''}".strip() if recipient else f"נזקק #{recipient_id}",
                "center_id": assignment["center_id"],
                "center_name": center.fname if center else f"מרכז #{assignment['center_id']}",
                "meals": assignment["recipient_meals"],
                "score": round(assignment["score"], 3),
            })

        return {
            "created_count": created_count,
            "assignments": enriched
        }
    finally:
        db.close()
