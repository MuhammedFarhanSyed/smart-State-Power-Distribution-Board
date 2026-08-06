from django.utils import timezone

from incidents.models import IncidentPole
from incidents.services.localization import _descendants, detect_for_feeder, detect_for_transformer, verify_repaired_incidents
from incidents.services.telemetry import ingest_telemetry
from network.models import Device, Feeder, Pole, Transformer


def _send_state(poles: list[Pole], event: str, energized: bool) -> int:
    """Generate telemetry through the normal ingestion path, with detection deferred."""
    sent = 0
    for device in Device.objects.filter(pole__in=poles).select_related("pole"):
        ingest_telemetry(
            {
                "device_id": device.device_id,
                "pole_id": device.pole.pole_id,
                "event": event,
                "energized": energized,
                "ts": timezone.now(),
                "seq": device.last_seq + 1,
                "battery_mv": 3480,
                "rssi": -88,
                "fw": device.firmware,
            },
            run_detection=False,
        )
        sent += 1
    return sent


def inject_span_fault(downstream_pole_id: str) -> dict:
    child = Pole.objects.select_related("parent", "transformer").get(pole_id=downstream_pole_id)
    if child.parent is None:
        raise ValueError("Select a pole with a recorded parent to simulate a span fault.")
    affected = [child, *_descendants(child)]
    sent = _send_state(affected, "power_lost", False)
    detect_for_transformer(child.transformer)
    return {"telemetry_messages_sent": sent, "affected_poles": len(affected)}


def inject_transformer_fault(dt_id: str) -> dict:
    transformer = Transformer.objects.get(dt_id=dt_id)
    poles = list(transformer.poles.all())
    sent = _send_state(poles, "power_lost", False)
    detect_for_transformer(transformer)
    return {"telemetry_messages_sent": sent, "affected_poles": len(poles)}


def inject_feeder_fault(feeder_id: str) -> dict:
    feeder = Feeder.objects.get(feeder_id=feeder_id)
    poles = list(Pole.objects.filter(transformer__feeder=feeder))
    sent = _send_state(poles, "power_lost", False)
    detect_for_feeder(feeder)
    return {"telemetry_messages_sent": sent, "affected_poles": len(poles)}


def repair_incident(incident_id: int) -> dict:
    incident_poles = list(IncidentPole.objects.filter(incident_id=incident_id).select_related("pole"))
    if not incident_poles:
        raise ValueError("This incident has no recorded affected poles to restore.")
    sent = _send_state([link.pole for link in incident_poles], "power_restored", True)
    verify_repaired_incidents()
    return {"telemetry_messages_sent": sent, "affected_poles": len(incident_poles)}
