import logging
import threading
from datetime import date, datetime, time, timedelta
from typing import Any

from db_connection import get_session
from repository.distribution_centerRepository import DistributionCenterRepository
from repository.recipientRepository import RecipientRepository
from repository.recipient_request_repository import RecipientRequestRepository
from services.center_messaging_service import CenterMessagingService, CenterSystemUnavailableError


logger = logging.getLogger("assignment_notifications")


class AssignmentNotificationService:
    def __init__(self) -> None:
        self.messaging_service = CenterMessagingService()

    def trigger_async_for_assignments(self, run_assignments: dict[Any, Any]) -> None:
        worker = threading.Thread(target=self._run_pipeline_for_run, args=(run_assignments,), daemon=True)
        worker.start()

    def _run_pipeline_for_run(self, run_assignments: dict[Any, Any]) -> None:
        db = get_session()
        try:
            filtered = self._filter_assignments_for_run(db, run_assignments)
            self._send_notifications_for_run(db, filtered)
        except Exception as exc:
            logger.exception("Assignment notification pipeline failed: %s", exc)
        finally:
            db.close()

    def _filter_assignments_for_run(self, db, run_assignments: dict[Any, Any]) -> list[dict[str, Any]]:
        # Only users/centers from the current run are eligible for notifications.
        requests = RecipientRequestRepository(db).get_all_requests()
        today = date.today()
        today_recipient_ids = {
            request_obj.RecipientID
            for request_obj in requests
            if request_obj.request_date and request_obj.request_date.date() == today
        }

        filtered: list[dict[str, Any]] = []
        for recipient_id_raw, assignment in (run_assignments or {}).items():
            try:
                recipient_id = int(recipient_id_raw)
            except (TypeError, ValueError):
                continue

            center_id = assignment.get("center_id") if isinstance(assignment, dict) else None
            if center_id is None:
                continue

            if recipient_id not in today_recipient_ids:
                continue

            filtered.append(
                {
                    "recipient_id": recipient_id,
                    "center_id": int(center_id),
                    "assigned_quantity": int(assignment.get("recipient_meals", 0)) if isinstance(assignment, dict) else 0,
                    "freshness_priority": int(assignment.get("freshness_priority", 0)) if isinstance(assignment, dict) else 0,
                }
            )

        return filtered

    def _send_notifications_for_run(self, db, assignments: list[dict[str, Any]]) -> None:
        center_repo = DistributionCenterRepository(db)
        recipient_repo = RecipientRepository(db)

        scheduled_dt = datetime.combine(date.today() + timedelta(days=1), time.min)

        for assignment in assignments:
            center = center_repo.get_distribution_center(assignment["center_id"])
            recipient = recipient_repo.get_recipient(assignment["recipient_id"])

            if not center or not recipient:
                continue

            recipient_payload = self._build_recipient_payload(assignment, center.username, scheduled_dt)
            center_payload = self._build_preparation_payload(assignment, recipient.username, scheduled_dt)

            try:
                self.messaging_service.send_popup(assignment["center_id"], recipient_payload)
                self.messaging_service.send_popup(assignment["center_id"], center_payload)
            except CenterSystemUnavailableError as exc:
                logger.warning(
                    "External system unavailable for center_id=%s. Notification skipped for this run: %s",
                    assignment["center_id"],
                    exc,
                )
            except Exception as exc:
                logger.exception(
                    "Failed to send run-scoped notifications for center_id=%s recipient_id=%s",
                    assignment["center_id"],
                    assignment["recipient_id"],
                )

    def _build_recipient_payload(self, assignment: dict[str, Any], center_username: str, scheduled_dt: datetime) -> dict[str, Any]:
        return {
            "kind": "recipient_confirmation",
            "assignment_key": self._assignment_key(assignment["recipient_id"], assignment["center_id"]),
            "recipe_id": assignment["recipient_id"],
            "recipient_id": assignment["recipient_id"],
            "center_id": assignment["center_id"],
            "center_username": center_username,
            "status": "assigned",
            "scheduled_date": scheduled_dt.isoformat(),
            "assigned_quantity": assignment["assigned_quantity"],
            "details": {
                "freshness_priority": assignment["freshness_priority"],
            },
        }

    def _build_preparation_payload(self, assignment: dict[str, Any], recipient_username: str, scheduled_dt: datetime) -> dict[str, Any]:
        return {
            "kind": "center_preparation",
            "assignment_key": self._assignment_key(assignment["recipient_id"], assignment["center_id"]),
            "recipe_id": assignment["recipient_id"],
            "recipient_id": assignment["recipient_id"],
            "recipient_username": recipient_username,
            "center_id": assignment["center_id"],
            "required_quantity": assignment["assigned_quantity"],
            "scheduled_date": scheduled_dt.isoformat(),
            "assignment_details": {
                "freshness_priority": assignment["freshness_priority"],
            },
        }

    def _assignment_key(self, recipient_id: int, center_id: int) -> str:
        return f"run:{recipient_id}:{center_id}"
