from typing import Dict, Any, Tuple, Optional
from django.utils import dateparse, timezone
from apps.telemetry.repositories import DeviceRepository, TelemetryReadingRepository
from apps.telemetry.services.deduplication import DeduplicationService


class TelemetryIngestionService:
    """
    Core ingestion service processing raw payload dicts from IoT devices.
    Orchestrates validation, deduplication, device state updates, and log recording.
    """

    @classmethod
    def process_telemetry_payload(cls, payload: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Processes a raw telemetry payload.

        Payload Spec:
        {
          "device_id": "KSPDB-SD07-D0112-4431",
          "pole_id": "P-024431",
          "event": "power_lost",
          "energized": false,
          "ts": "2026-07-29T02:14:07.412Z",
          "seq": 88213,
          "battery_mv": 3480,
          "rssi": -91,
          "fw": "1.4"
        }

        :return: (success: bool, message: str, ingested_data: Optional[Dict])
        """
        device_id = payload.get('device_id')
        pole_id = payload.get('pole_id')
        event = payload.get('event')
        energized = payload.get('energized')
        ts_str = payload.get('ts')
        seq = payload.get('seq')
        battery_mv = payload.get('battery_mv', 3480)
        rssi = payload.get('rssi', -91)
        fw = payload.get('fw', '1.4')

        # Validate mandatory fields
        if not device_id or not pole_id or event is None or energized is None or seq is None:
            return False, "Missing mandatory telemetry fields", None

        # Parse timestamp
        if ts_str:
            device_ts = dateparse.parse_datetime(ts_str)
            if not device_ts:
                return False, "Invalid ISO timestamp format", None
        else:
            device_ts = timezone.now()

        # Deduplication & Stale payload check
        is_valid, drop_reason = DeduplicationService.evaluate_reading(
            device_id=device_id,
            sequence_number=seq,
            event=event,
            device_timestamp=device_ts
        )

        if not is_valid:
            return False, f"Payload rejected: {drop_reason}", None

        # Upsert IoT Device record
        DeviceRepository.upsert_device(
            device_id=device_id,
            pole_id=pole_id,
            firmware_version=fw
        )

        # Create append-only log record
        reading = TelemetryReadingRepository.create_reading(
            device_id=device_id,
            pole_id=pole_id,
            event=event,
            energized=energized,
            device_timestamp=device_ts,
            sequence_number=seq,
            battery_mv=battery_mv,
            rssi=rssi
        )

        ingested_dto = {
            'reading_id': reading.id,
            'device_id': device_id,
            'pole_id': pole_id,
            'event': event,
            'energized': energized,
            'sequence_number': seq,
            'firmware_version': fw,
            'timestamp': device_ts.isoformat()
        }

        return True, "Telemetry processed successfully", ingested_dto
