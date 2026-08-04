from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone as dt_timezone

try:
    from django.utils import timezone
    def get_now_iso():
        return timezone.now().isoformat()
except ImportError:
    def get_now_iso():
        return datetime.now(dt_timezone.utc).isoformat()

from apps.telemetry.services.ingestion import TelemetryIngestionService
from apps.faults.services.fault_orchestrator import FaultOrchestratorService


class TelemetryGenerator:
    """
    Generates synthetic telemetry payloads matching production schemas
    and pushes them strictly through the existing telemetry ingestion & fault orchestration pipeline.
    """

    _sequence_counters: Dict[str, int] = {}

    @classmethod
    def get_next_sequence(cls, device_id: str, is_boot: bool = False) -> int:
        """Gets next monotonic sequence number for a device. Resets to 0 on boot."""
        if is_boot:
            cls._sequence_counters[device_id] = 0
            return 0
        current = cls._sequence_counters.get(device_id, 100) + 1
        cls._sequence_counters[device_id] = current
        return current

    @classmethod
    def build_payload(
        cls,
        device_id: str,
        pole_id: str,
        event: str,
        energized: bool,
        firmware: str = '1.4',
        custom_seq: Optional[int] = None
    ) -> Dict[str, Any]:
        """Formats a payload matching production schema."""
        seq = custom_seq if custom_seq is not None else cls.get_next_sequence(device_id, is_boot=(event == 'boot'))
        now = get_now_iso()

        return {
            "device_id": device_id,
            "pole_id": pole_id,
            "event": event,
            "energized": energized,
            "ts": now,
            "seq": seq,
            "battery_mv": 3480 if energized else 2900,
            "rssi": -91,
            "fw": firmware
        }

    @classmethod
    def push_telemetry(
        cls,
        dt_id: str,
        payload: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Pushes a telemetry payload through:
        1. TelemetryIngestionService.process_payload()
        2. FaultOrchestratorService.evaluate_dt_fault_state()
        """
        success, message, result_dto = TelemetryIngestionService.process_payload(payload)

        if success:
            FaultOrchestratorService.evaluate_dt_fault_state(dt_id=dt_id)

        return success, message, result_dto
