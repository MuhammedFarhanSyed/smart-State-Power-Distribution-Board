from typing import Tuple, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from apps.telemetry.repositories import TelemetryReadingRepository


class DeduplicationService:
    """
    Enforces device sequence monotonicity, filters duplicate/out-of-order payloads,
    and drops stale retries (> 6 hours old).
    """

    MAX_STALE_HOURS = 6

    @classmethod
    def evaluate_reading(
        cls,
        device_id: str,
        sequence_number: int,
        event: str,
        device_timestamp: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates an incoming reading against sequence history and timestamp limits.

        :return: (is_valid, drop_reason)
        """
        now = timezone.now()

        # 1. Filter stale retries (>6 hours old)
        if device_timestamp and (now - device_timestamp > timedelta(hours=cls.MAX_STALE_HOURS)):
            return False, f"Stale telemetry payload (older than {cls.MAX_STALE_HOURS} hours)"

        # 2. Boot event resets sequence counter to 0
        if event == 'boot' or sequence_number == 0:
            return True, None

        # 3. Check sequence monotonicity against existing readings
        latest_seq = TelemetryReadingRepository.get_latest_sequence_for_device(device_id)
        if latest_seq is not None:
            if sequence_number <= latest_seq:
                return False, f"Duplicate or out-of-order sequence number ({sequence_number} <= {latest_seq})"

        return True, None
