from rest_framework import serializers
from apps.telemetry.models import TelemetryReading


class TelemetryIngestSerializer(serializers.Serializer):
    """
    Serializer validating incoming IoT device telemetry payload schema.
    """
    device_id = serializers.CharField(
        max_length=64,
        required=True,
        help_text="Stable device identifier."
    )
    pole_id = serializers.CharField(
        max_length=64,
        required=True,
        help_text="Pole identifier associated with this telemetry event."
    )
    event = serializers.ChoiceField(
        choices=TelemetryReading.EVENT_CHOICES,
        required=True,
        help_text="Telemetry event: heartbeat, power_lost, power_restored, boot."
    )
    energized = serializers.BooleanField(
        required=True,
        help_text="Current energization state seen by device (True = Live, False = Dark)."
    )
    ts = serializers.DateTimeField(
        required=True,
        help_text="Device internal timestamp (ISO format)."
    )
    seq = serializers.IntegerField(
        min_value=0,
        required=True,
        help_text="Monotonic sequence number per device. Resets to 0 on boot."
    )
    battery_mv = serializers.IntegerField(
        required=False,
        default=3480,
        help_text="Capacitor reserve voltage in mV."
    )
    rssi = serializers.IntegerField(
        required=False,
        default=-91,
        help_text="Signal strength in dBm."
    )
    fw = serializers.CharField(
        max_length=32,
        required=False,
        default='1.4',
        help_text="Device firmware version (e.g., '1.2', '1.4')."
    )
