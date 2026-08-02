from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.assignment_notification import AssignmentNotification


class AssignmentNotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_key(self, notification_key: str) -> Optional[AssignmentNotification]:
        return (
            self.db.query(AssignmentNotification)
            .filter(AssignmentNotification.notification_key == notification_key)
            .first()
        )

    def create_notification(
        self,
        notification_key: str,
        assignment_id: Optional[int],
        recipient_id: Optional[int],
        center_id: int,
        notification_type: str,
        payload_json: str,
        external_system_name: str,
        scheduled_date: datetime,
        max_retries: int = 3,
    ) -> AssignmentNotification:
        existing = self.find_by_key(notification_key)
        if existing:
            return existing

        notification = AssignmentNotification(
            notification_key=notification_key,
            assignment_id=assignment_id,
            recipient_id=recipient_id,
            center_id=center_id,
            notification_type=notification_type,
            status="pending",
            payload_json=payload_json,
            external_system_name=external_system_name,
            max_retries=max_retries,
            scheduled_date=scheduled_date,
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_dispatch_candidates(self, now: datetime) -> list[AssignmentNotification]:
        return (
            self.db.query(AssignmentNotification)
            .filter(AssignmentNotification.status.in_(["pending", "retried"]))
            .filter(
                (AssignmentNotification.next_retry_at.is_(None))
                | (AssignmentNotification.next_retry_at <= now)
            )
            .all()
        )

    def mark_sent(self, notification: AssignmentNotification, external_message_id: str) -> AssignmentNotification:
        notification.status = "sent"
        notification.external_message_id = external_message_id
        notification.sent_at = datetime.utcnow()
        notification.last_error = None
        notification.next_retry_at = None
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_retry(self, notification: AssignmentNotification, error_text: str, next_retry_at: datetime) -> AssignmentNotification:
        notification.retry_count = (notification.retry_count or 0) + 1
        notification.status = "retried"
        notification.last_error = error_text
        notification.next_retry_at = next_retry_at
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_failed(self, notification: AssignmentNotification, error_text: str) -> AssignmentNotification:
        notification.status = "failed"
        notification.last_error = error_text
        notification.next_retry_at = None
        self.db.commit()
        self.db.refresh(notification)
        return notification
