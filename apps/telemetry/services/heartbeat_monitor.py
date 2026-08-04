from typing import List, Dict, Any
from apps.telemetry.repositories import DeviceRepository


class HeartbeatMonitorService:
    """
    Monitors IoT devices for missed heartbeats.
    Detects silent outages for ~8% of the fleet running Firmware 1.2 (which send no power_lost packets).
    """

    # Heartbeat interval is 15 min ± 45s jitter. Threshold set to 20 minutes (1200 seconds).
    HEARTBEAT_TIMEOUT_SECONDS = 1200

    @classmethod
    def check_silent_devices(cls) -> List[Dict[str, Any]]:
        """
        Scans active device registry for devices silent longer than the timeout window.
        Returns a list of silent device status dicts.
        """
        silent_devices = DeviceRepository.get_silent_devices(timeout_seconds=cls.HEARTBEAT_TIMEOUT_SECONDS)
        silent_records: List[Dict[str, Any]] = []

        for device in silent_devices:
            silent_records.append({
                'device_id': device.device_id,
                'pole_id': device.current_pole_id,
                'firmware_version': device.firmware_version,
                'last_seen_at': device.last_seen_at.isoformat() if device.last_seen_at else None,
                'is_fw_1_2_silent': (device.firmware_version == '1.2')
            })

        return silent_records
