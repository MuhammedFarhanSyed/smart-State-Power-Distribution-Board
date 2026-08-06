from django.db import transaction
from django.utils import timezone

from incidents.models import Incident, IncidentPole, ScheduledOutage
from network.models import Feeder, Pole, Transformer


def _descendants(pole: Pole) -> list[Pole]:
    """Return every pole downstream in a known radial tree."""
    result = []
    pending = list(pole.children.all())
    while pending:
        current = pending.pop()
        result.append(current)
        pending.extend(current.children.all())
    return result


def _is_scheduled(transformer: Transformer) -> bool:
    now = timezone.now()
    return ScheduledOutage.objects.filter(start__lte=now, end__gte=now).filter(
        transformer=transformer
    ).exists() or ScheduledOutage.objects.filter(start__lte=now, end__gte=now).filter(
        feeder=transformer.feeder
    ).exists()


@transaction.atomic
def detect_for_transformer(transformer: Transformer) -> None:
    """Create one incident for each live-to-dark boundary under a transformer.

    This intentionally uses only the explicit parent links. When they are absent,
    it creates an honest transformer-level incident rather than guessing a span.
    """
    if _is_scheduled(transformer):
        return

    poles = list(transformer.poles.select_related("parent").prefetch_related("children"))
    dark_poles = [pole for pole in poles if pole.is_energized is False]
    if not dark_poles:
        return

    observed_poles = [pole for pole in poles if pole.is_energized is not None]
    if observed_poles and len(dark_poles) == len(observed_poles):
        incident, created = Incident.objects.get_or_create(
            transformer=transformer,
            fault_type=Incident.FaultType.TRANSFORMER,
            status__in=[Incident.Status.DETECTED, Incident.Status.ACKNOWLEDGED, Incident.Status.CREW_ASSIGNED, Incident.Status.REPAIR_REPORTED],
            defaults={
                "feeder": transformer.feeder,
                "latitude": transformer.lat,
                "longitude": transformer.lon,
                "affected_pole_count": len(dark_poles),
                "confidence": Incident.Confidence.MEDIUM,
                "confidence_reason": "Every reporting pole below this transformer is dark; the DT, fuse, or its upstream connection is affected.",
            },
        )
        if created:
            IncidentPole.objects.bulk_create(
                [IncidentPole(incident=incident, pole=pole) for pole in dark_poles], ignore_conflicts=True
            )
        return

    has_usable_topology = any(pole.parent_id for pole in poles)
    boundaries = []
    if has_usable_topology:
        for child in dark_poles:
            parent = child.parent
            if parent is None or parent.is_energized is not True:
                continue
            downstream = [child, *_descendants(child)]
            # A live downstream child makes this physically inconsistent with a span failure.
            if any(pole.is_energized is True for pole in downstream):
                continue
            boundaries.append((parent, child, downstream))

    if boundaries:
        for parent, child, downstream in boundaries:
            incident, created = Incident.objects.get_or_create(
                downstream_pole=child,
                status__in=[Incident.Status.DETECTED, Incident.Status.ACKNOWLEDGED, Incident.Status.CREW_ASSIGNED, Incident.Status.REPAIR_REPORTED],
                defaults={
                    "fault_type": Incident.FaultType.SPAN,
                    "transformer": transformer,
                    "feeder": transformer.feeder,
                    "upstream_pole": parent,
                    "latitude": (parent.lat + child.lat) / 2,
                    "longitude": (parent.lon + child.lon) / 2,
                    "pincode": child.pincode or parent.pincode,
                    "affected_pole_count": len(downstream),
                    "confidence": Incident.Confidence.HIGH,
                    "confidence_reason": "Known topology shows a live parent directly upstream of a dark subtree.",
                },
            )
            if created:
                IncidentPole.objects.bulk_create(
                    [IncidentPole(incident=incident, pole=pole) for pole in downstream], ignore_conflicts=True
                )
        return

    # No explicit boundary: degrade honestly when line order has not been digitized.
    incident, created = Incident.objects.get_or_create(
        transformer=transformer,
        fault_type=Incident.FaultType.TOPOLOGY_UNKNOWN,
        status__in=[Incident.Status.DETECTED, Incident.Status.ACKNOWLEDGED, Incident.Status.CREW_ASSIGNED, Incident.Status.REPAIR_REPORTED],
        defaults={
            "feeder": transformer.feeder,
            "latitude": transformer.lat,
            "longitude": transformer.lon,
            "affected_pole_count": len(dark_poles),
            "confidence": Incident.Confidence.LOW,
            "confidence_reason": "Multiple poles are dark, but pole order is unavailable; an exact span cannot be verified.",
        },
    )
    if created:
        IncidentPole.objects.bulk_create(
            [IncidentPole(incident=incident, pole=pole) for pole in dark_poles], ignore_conflicts=True
        )


@transaction.atomic
def detect_for_feeder(feeder: Feeder) -> None:
    """Create one feeder ticket when every reporting pole across the feeder is dark."""
    transformers = list(feeder.transformers.prefetch_related("poles").all())
    poles = [pole for transformer in transformers for pole in transformer.poles.all()]
    observed = [pole for pole in poles if pole.is_energized is not None]
    if not observed or any(pole.is_energized is not False for pole in observed):
        return

    incident, created = Incident.objects.get_or_create(
        feeder=feeder,
        transformer=None,
        fault_type=Incident.FaultType.FEEDER,
        status__in=[Incident.Status.DETECTED, Incident.Status.ACKNOWLEDGED, Incident.Status.CREW_ASSIGNED, Incident.Status.REPAIR_REPORTED],
        defaults={
            "latitude": sum(t.lat for t in transformers) / len(transformers),
            "longitude": sum(t.lon for t in transformers) / len(transformers),
            "affected_pole_count": len([pole for pole in observed if pole.is_energized is False]),
            "confidence": Incident.Confidence.MEDIUM,
            "confidence_reason": "Every reporting pole on this feeder is dark; this is a feeder-level outage pattern.",
        },
    )
    if created:
        IncidentPole.objects.bulk_create(
            [IncidentPole(incident=incident, pole=pole) for pole in observed], ignore_conflicts=True
        )


@transaction.atomic
def verify_repaired_incidents() -> None:
    """Close repair-reported tickets only after all affected poles are live again."""
    incidents = Incident.objects.filter(status=Incident.Status.REPAIR_REPORTED).prefetch_related("affected_poles__pole")
    for incident in incidents:
        affected = [link.pole for link in incident.affected_poles.all()]
        if affected and all(pole.is_energized is True for pole in affected):
            now = timezone.now()
            incident.status = Incident.Status.CLOSED
            incident.verified_at = now
            incident.closed_at = now
            incident.save(update_fields=["status", "verified_at", "closed_at"])
