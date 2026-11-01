from db_connection import get_session
from repository.delivery_assignmentRepository import DeliveryAssignmentRepository
from services.batch_algoritm.execute_full_matching import execute_full_matching
from services.assignment_notification_service import AssignmentNotificationService


def create_assignments_from_matching():

    result = execute_full_matching()

    db = get_session()

    try:

        repo = DeliveryAssignmentRepository(db)

        created_count = 0
        assignments = result.get("assignments", {}) if isinstance(result, dict) else {}

        for recipient_id, assignment in assignments.items():

            repo.create_delivery_assignment(
                DistributionCenterID=assignment["center_id"],
                RecipientID=recipient_id,
                VolunteerID=None,
                amount_of_meals=assignment["recipient_meals"],
                freshness_priority=assignment.get("freshness_priority", 0)

            )

            created_count += 1

        # Notify only entities affected by this specific run.
        AssignmentNotificationService().trigger_async_for_assignments(assignments)

        return {
            "message": result.get("message", "שיבוץ הושלם בהצלחה") if isinstance(result, dict) else "שיבוץ הושלם בהצלחה",
            "created_count": created_count,
            "total_requested_today": result.get("total_requested_today", created_count) if isinstance(result, dict) else created_count,
            "unassigned": result.get("unassigned", 0) if isinstance(result, dict) else 0,
            "unique_centers_used": result.get("unique_centers_used", len({a["center_id"] for a in assignments.values()})) if isinstance(result, dict) else len({a["center_id"] for a in assignments.values()}),
            "assignments": result.get("assignments", {}) if isinstance(result, dict) else {},
        }

    finally:
        db.close()