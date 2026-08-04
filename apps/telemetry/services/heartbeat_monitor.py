from typing import List, Dict, Any
from apps.telemetry.repositories import DeviceRepository


class HeartbeatMonitor:
    """
    Service responsible for scanning field device fleet to detect silent devices.
    Detects silent outages for ~8% of fleet on Firmware 1.2 (which send no power_lost packets).
    """

    HEARTBEAT_TIMEOUT_SECONDS = 1200  # 15 min heartbeat + 5 min jitter/grace

    @classmethod
    def detect_silent_devices(cls) -> List[Dict[str, Any]]:
        """
        Scans device registry for active devices silent longer than the 20-minute threshold.
        """
        silent_devices = DeviceRepository.get_silent_devices(timeout_seconds=cls.HEARTBEAT_TIMEOUT_SECONDS)
        results: List[Dict[str, Any]] = []

        for device in silent_devices:
            results.append({
                'device_id': device.device_id,
                'pole_id': device.current_pole_id,
                'firmware_version': device.firmware_version,
                'last_seen_at': device.last_seen_at.isoformat() if device.last_seen_at else None,
                'is_fw_1_2_silent': (device.firmware_version == '1.2')
            })

        return results
