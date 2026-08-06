from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from incidents.models import TelemetryEvent
from incidents.services.localization import detect_for_transformer, verify_repaired_incidents
from network.models import Device


@dataclass
class IngestResult:
    accepted: bool
    reason: str
    event: TelemetryEvent | None = None


@transaction.atomic
def ingest_telemetry(payload: dict, run_detection: bool = True) -> IngestResult:
    """Save one message, update the latest pole state, then run deterministic detection."""
    try:
        device = Device.objects.select_for_update().select_related("pole__transformer").get(
            device_id=payload["device_id"]
        )
    except Device.DoesNotExist as error:
        raise ValueError("Unknown device_id. Devices must be seeded before telemetry is accepted.") from error

    if device.pole.pole_id != payload["pole_id"]:
        raise ValueError("device_id is not currently registered against this pole_id.")

    # A boot packet is allowed to restart the per-device sequence at zero.
    if payload["event"] != TelemetryEvent.EventType.BOOT and payload["seq"] <= device.last_seq:
        return IngestResult(accepted=False, reason="Duplicate or stale sequence number.")

    event = TelemetryEvent.objects.create(
        device=device,
        pole=device.pole,
        event=payload["event"],
        energized=payload["energized"],
        device_timestamp=payload["ts"],
        seq=payload["seq"],
        battery_mv=payload.get("battery_mv"),
        rssi=payload.get("rssi"),
        firmware=payload.get("fw", ""),
    )

    device.last_seq = payload["seq"]
    device.is_online = True
    if payload.get("fw"):
        device.firmware = payload["fw"]
    device.save(update_fields=["last_seq", "is_online", "firmware"])

    device.pole.is_energized = payload["energized"]
    device.pole.last_state_at = timezone.now()
    device.pole.save(update_fields=["is_energized", "last_state_at"])

    if run_detection:
        detect_for_transformer(device.pole.transformer)
        verify_repaired_incidents()
    return IngestResult(accepted=True, reason="Telemetry accepted.", event=event)
