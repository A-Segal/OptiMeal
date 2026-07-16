import logging
from typing import Any


class CenterSystemUnavailableError(Exception):
    pass


class CenterMessagingService:
    """
    Messaging adapter for external center systems.
    Replace `_is_external_system_available` and send implementation with real integration.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def send_popup(self, center_id: int, payload: dict[str, Any]) -> str:
        if not self._is_external_system_available(center_id):
            raise CenterSystemUnavailableError(f"Center system {center_id} is unavailable")

        # Placeholder transport. In production, call the external system API/websocket here.
        message_id = f"center-{center_id}-{payload.get('notification_key', 'msg')}"
        self.logger.info("Popup sent to center %s with message_id=%s", center_id, message_id)
        return message_id

    def _is_external_system_available(self, center_id: int) -> bool:
        # Hook for real availability check.
        return True
