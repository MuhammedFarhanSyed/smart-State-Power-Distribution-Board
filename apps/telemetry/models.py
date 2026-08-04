from django.db import models
from apps.common.models import TimeStampedModel


class Device(TimeStampedModel):
    """
    Represents an IoT telemetry sensor device fitted on a pole.
    Devices can be swapped between poles over time.
    """
    device_id = models.CharField(
        max_length=64,
        primary_key=True,
        help_text="Stable physical device identifier (e.g., KSPDB-SD07-D0112-4431)."
    )
    current_pole_id = models.CharField(
        max_length=64,
        db_index=True,
        blank=True,
        null=True,
        help_text="Pole ID where this device is currently mounted."
    )
    firmware_version = models.CharField(
        max_length=32,
        default='1.4',
        help_text="Firmware version (e.g., '1.2', '1.4'). FW 1.2 does NOT send power_lost packets."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the device is active in the field fleet (~4% are offline)."
    )
    last_seen_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp of most recent telemetry reading received."
    )

    class Meta:
        db_table = 'telemetry_device'
        verbose_name = 'IoT Device'
        verbose_name_plural = 'IoT Devices'
        ordering = ['device_id']

    def __str__(self) -> str:
        return f"Device {self.device_id} (FW: {self.firmware_version}, Pole: {self.current_pole_id or 'Unassigned'})"


class TelemetryReading(models.Model):
    """
    Append-only high-volume log table storing raw telemetry messages pushed by IoT devices.
    """
    EVENT_HEARTBEAT = 'heartbeat'
    EVENT_POWER_LOST = 'power_lost'
    EVENT_POWER_RESTORED = 'power_restored'
    EVENT_BOOT = 'boot'

    EVENT_CHOICES = [
        (EVENT_HEARTBEAT, 'Heartbeat'),
        (EVENT_POWER_LOST, 'Power Lost'),
        (EVENT_POWER_RESTORED, 'Power Restored'),
        (EVENT_BOOT, 'Boot'),
    ]

    device_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Source device identifier."
    )
    pole_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Pole identifier associated with this telemetry reading."
    )
    event = models.CharField(
        max_length=32,
        choices=EVENT_CHOICES,
        help_text="Event type: heartbeat, power_lost, power_restored, boot."
    )
    energized = models.BooleanField(
        help_text="Current energization state seen by the device (True = Live, False = Dark)."
    )
    device_timestamp = models.DateTimeField(
        help_text="Device internal clock timestamp (Device clock skew up to ±90s)."
    )
    sequence_number = models.BigIntegerField(
        help_text="Monotonic sequence number per device. Resets to 0 on boot."
    )
    battery_mv = models.IntegerField(
        default=3480,
        help_text="Reserve capacitor voltage in mV (dying message power reserve)."
    )
    rssi = models.IntegerField(
        default=-91,
        help_text="Cellular radio signal strength in dBm."
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Server-side ingest arrival timestamp."
    )

    class Meta:
        db_table = 'telemetry_reading'
        verbose_name = 'Telemetry Reading'
        verbose_name_plural = 'Telemetry Readings'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['device_id', 'sequence_number'], name='idx_telem_dev_seq'),
            models.Index(fields=['pole_id', 'received_at'], name='idx_telem_pole_rec'),
            models.Index(fields=['device_id', 'received_at'], name='idx_telem_dev_rec'),
        ]

    def __str__(self) -> str:
        return f"[{self.event.upper()}] Device: {self.device_id} | Pole: {self.pole_id} | Energized: {self.energized} | Seq: {self.sequence_number}"
