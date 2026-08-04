from typing import Dict, Any, Tuple, Optional
from django.utils import dateparse, timezone
from apps.telemetry.repositories import DeviceRepository, TelemetryRepository
from apps.telemetry.services.deduplication import DeduplicationService


class IngestionService:
    """
    Service responsible for validating telemetry payloads, invoking deduplication,
    updating latest device state, and persisting raw telemetry packets into append-only storage.
    NEVER performs fault localization or ticket creation.
    """

    @classmethod
    def process_payload(cls, validated_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Processes validated payload data.

        :param validated_data: Clean dictionary from DRF TelemetryIngestSerializer.
        :return: (success: bool, message: str, result_dto: Optional[Dict])
        """
        device_id = validated_data['device_id']
        pole_id = validated_data['pole_id']
        event = validated_data['event']
        energized = validated_data['energized']
        device_ts = validated_data['ts']
        seq = validated_data['seq']
        battery_mv = validated_data.get('battery_mv', 3480)
        rssi = validated_data.get('rssi', -91)
        fw = validated_data.get('fw', '1.4')

        # 1. Sequence Deduplication & Stale Retry Check
        is_valid, reject_reason = DeduplicationService.evaluate_packet(
            device_id=device_id,
            sequence_number=seq,
            event=event,
            device_timestamp=device_ts
        )

        if not is_valid:
            return False, f"Packet rejected: {reject_reason}", None

        # 2. Update Device latest known state
        DeviceRepository.update_latest_state(
            device_id=device_id,
            pole_id=pole_id,
            event=event,
            energized=energized,
            sequence_number=seq,
            firmware_version=fw
        )

        # 3. Store in append-only TelemetryReading log
        reading = TelemetryRepository.create_reading(
            device_id=device_id,
            pole_id=pole_id,
            event=event,
            energized=energized,
            device_timestamp=device_ts,
            sequence_number=seq,
            battery_mv=battery_mv,
            rssi=rssi
        )

        result_dto = {
            'reading_id': reading.id,
            'device_id': device_id,
            'pole_id': pole_id,
            'event': event,
            'energized': energized,
            'seq': seq,
            'fw': fw,
            'timestamp': device_ts.isoformat()
        }

        return True, "Telemetry packet ingested successfully", result_dto
