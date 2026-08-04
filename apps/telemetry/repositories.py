from typing import Optional, List, Dict, Any
from django.utils import timezone
from datetime import timedelta
from apps.telemetry.models import Device, TelemetryReading


class DeviceRepository:
    """
    Repository encapsulating database access for IoT Device state.
    Maintains latest known state per device.
    """

    @staticmethod
    def get_by_id(device_id: str) -> Optional[Device]:
        """Fetch a device by its unique device_id."""
        try:
            return Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return None

    @staticmethod
    def update_latest_state(
        device_id: str,
        pole_id: Optional[str] = None,
        event: Optional[str] = None,
        energized: Optional[bool] = None,
        sequence_number: Optional[int] = None,
        firmware_version: str = '1.4'
    ) -> Device:
        """
        Upserts device record and updates its latest known field state.
        """
        now = timezone.now()
        device, created = Device.objects.get_or_create(
            device_id=device_id,
            defaults={
                'current_pole_id': pole_id,
                'firmware_version': firmware_version,
                'last_event': event,
                'last_energized_state': energized if energized is not None else True,
                'last_sequence_number': sequence_number or 0,
                'last_seen_at': now
            }
        )

        if not created:
            update_fields = ['last_seen_at', 'updated_at']
            device.last_seen_at = now

            if pole_id and device.current_pole_id != pole_id:
                device.current_pole_id = pole_id
                update_fields.append('current_pole_id')
            if event:
                device.last_event = event
                update_fields.append('last_event')
            if energized is not None:
                device.last_energized_state = energized
                update_fields.append('last_energized_state')
            if sequence_number is not None:
                device.last_sequence_number = sequence_number
                update_fields.append('last_sequence_number')
            if firmware_version and device.firmware_version != firmware_version:
                device.firmware_version = firmware_version
                update_fields.append('firmware_version')

            device.save(update_fields=update_fields)

        return device

    @staticmethod
    def get_silent_devices(timeout_seconds: int = 1200) -> List[Device]:
        """
        Fetch active devices whose last_seen_at is older than the timeout threshold
        (15 min interval + 5 min grace = 20 minutes / 1200s).
        """
        cutoff = timezone.now() - timedelta(seconds=timeout_seconds)
        return list(Device.objects.filter(
            is_active=True,
            last_seen_at__lt=cutoff
        ))


class TelemetryRepository:
    """
    Repository encapsulating database access for append-only raw TelemetryReading logs.
    """

    @staticmethod
    def create_reading(
        device_id: str,
        pole_id: str,
        event: str,
        energized: bool,
        device_timestamp,
        sequence_number: int,
        battery_mv: int = 3480,
        rssi: int = -91
    ) -> TelemetryReading:
        """Stores a raw telemetry packet exactly as received into append-only log."""
        return TelemetryReading.objects.create(
            device_id=device_id,
            pole_id=pole_id,
            event=event,
            energized=energized,
            device_timestamp=device_timestamp,
            sequence_number=sequence_number,
            battery_mv=battery_mv,
            rssi=rssi
        )

    @staticmethod
    def get_latest_sequence_for_device(device_id: str) -> Optional[int]:
        """Retrieve highest sequence number logged for a device."""
        reading = TelemetryReading.objects.filter(device_id=device_id).order_by('-sequence_number').first()
        return reading.sequence_number if reading else None

    @staticmethod
    def get_latest_reading_for_pole(pole_id: str) -> Optional[TelemetryReading]:
        """Retrieve latest telemetry reading for a given pole."""
        return TelemetryReading.objects.filter(pole_id=pole_id).order_by('-received_at').first()

    @staticmethod
    def get_latest_states_by_poles(pole_ids: List[str]) -> Dict[str, bool]:
        """
        Retrieves latest energization state for a batch of pole IDs.
        Returns dict of pole_id -> is_energized (bool).
        """
        if not pole_ids:
            return {}

        states: Dict[str, bool] = {}
        readings = TelemetryReading.objects.filter(
            pole_id__in=pole_ids
        ).order_by('pole_id', '-received_at')

        for r in readings:
            if r.pole_id not in states:
                states[r.pole_id] = r.energized

        return states
