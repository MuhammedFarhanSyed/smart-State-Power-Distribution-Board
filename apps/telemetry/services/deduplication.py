from typing import Tuple, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from apps.telemetry.repositories import TelemetryRepository


class DeduplicationService:
    """
    Service responsible for deduplicating incoming telemetry packets using sequence numbers,
    handling boot sequence resets, and dropping stale retries (>6h old).
    """

    MAX_STALE_HOURS = 6

    @classmethod
    def evaluate_packet(
        cls,
        device_id: str,
        sequence_number: int,
        event: str,
        device_timestamp: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates a packet's validity based on sequence monotonicity and timestamp boundaries.

        :return: (is_valid: bool, reject_reason: Optional[str])
        """
        now = timezone.now()

        # 1. Reject stale retries (>6 hours old)
        if device_timestamp and (now - device_timestamp > timedelta(hours=cls.MAX_STALE_HOURS)):
            return False, f"Stale telemetry packet (older than {cls.MAX_STALE_HOURS} hours)"

        # 2. Boot sequence reset: boot event or sequence_number=0 resets monotonic check
        if event == 'boot' or sequence_number == 0:
            return True, None

        # 3. Check sequence monotonicity against repository
        latest_seq = TelemetryRepository.get_latest_sequence_for_device(device_id)
        if latest_seq is not None:
            if sequence_number <= latest_seq:
                return False, f"Duplicate or out-of-order sequence number ({sequence_number} <= {latest_seq})"

        return True, None
