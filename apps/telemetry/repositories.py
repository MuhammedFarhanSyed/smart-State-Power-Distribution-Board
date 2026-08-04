from typing import Optional, List, Dict, Any
from django.utils import timezone
from datetime import timedelta
from apps.telemetry.models import Device, TelemetryReading


class DeviceRepository:
    """
    Encapsulates database access methods for IoT Device state.
    """

    @staticmethod
    def get_by_id(device_id: str) -> Optional[Device]:
        """Fetch a device by its unique ID."""
        try:
            return Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return None

    @staticmethod
    def upsert_device(device_id: str, pole_id: Optional[str] = None, firmware_version: str = '1.4') -> Device:
        """Get or create device record and update its pole association and last_seen timestamp."""
        now = timezone.now()
        device, created = Device.objects.get_or_create(
            device_id=device_id,
            defaults={
                'current_pole_id': pole_id,
                'firmware_version': firmware_version,
                'last_seen_at': now
            }
        )
        if not created:
            updated = False
            if pole_id and device.current_pole_id != pole_id:
                device.current_pole_id = pole_id
                updated = True
            if firmware_version and device.firmware_version != firmware_version:
                device.firmware_version = firmware_version
                updated = True
            device.last_seen_at = now
            device.save(update_fields=['current_pole_id', 'firmware_version', 'last_seen_at', 'updated_at'])

        return device

    @staticmethod
    def get_silent_devices(timeout_seconds: int = 1200) -> List[Device]:
        """
        Find active devices that have not sent telemetry within the timeout threshold
        (default 20 minutes = 15 min heartbeat + 5 min jitter/grace period).
        Used by HeartbeatMonitorService to detect silent FW 1.2 failures.
        """
        cutoff = timezone.now() - timedelta(seconds=timeout_seconds)
        return list(Device.objects.filter(
            is_active=True,
            last_seen_at__lt=cutoff
        ))


class TelemetryReadingRepository:
    """
    Encapsulates high-volume query and insert operations for TelemetryReading logs.
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
        """Insert a single raw telemetry reading log."""
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
        """Retrieve the highest sequence number processed for a device."""
        reading = TelemetryReading.objects.filter(device_id=device_id).order_by('-sequence_number').first()
        return reading.sequence_number if reading else None

    @staticmethod
    def get_latest_reading_for_pole(pole_id: str) -> Optional[TelemetryReading]:
        """Retrieve the most recent telemetry reading for a given pole."""
        return TelemetryReading.objects.filter(pole_id=pole_id).order_by('-received_at').first()

    @staticmethod
    def get_latest_states_for_poles(pole_ids: List[str]) -> Dict[str, bool]:
        """
        Efficiently fetches the current energization state for a list of pole IDs.
        Returns map of pole_id -> is_energized (bool).
        """
        if not pole_ids:
            return {}

        states: Dict[str, bool] = {}
        # Fetch latest reading per pole
        readings = TelemetryReading.objects.filter(
            pole_id__in=pole_ids
        ).order_by('pole_id', '-received_at')

        # Pick first (newest) record per pole
        for r in readings:
            if r.pole_id not in states:
                states[r.pole_id] = r.energized

        return states
