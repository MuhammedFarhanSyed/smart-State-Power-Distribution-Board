from typing import Optional, List, Dict, Any
from django.utils import timezone
from datetime import timedelta
from apps.faults.models import ScheduledOutage, FaultIncident, AffectedPole
from core_engine.algorithms.incident_grouper import IncidentPayload


class ScheduledOutageRepository:
    """
    Repository encapsulating database queries for Scheduled Maintenance Outages.
    """

    @staticmethod
    def get_active_outages() -> List[Dict[str, str]]:
        """
        Retrieves active scheduled outages taking into account a 45-minute overrun buffer window.
        Returns a list of dicts: [{'target_id': 'D-0112', 'scope': 'dt'}, ...]
        """
        now = timezone.now()
        # Include buffer for shutdowns starting early or running up to 45 mins late
        buffer_start = now + timedelta(minutes=15)
        buffer_end = now - timedelta(minutes=45)

        outages = ScheduledOutage.objects.filter(
            start_time__lte=buffer_start,
            end_time__gte=buffer_end
        )

        return [{'target_id': o.target_id, 'scope': o.scope} for o in outages]

    @staticmethod
    def create_scheduled_outage(
        outage_id: str,
        scope: str,
        target_id: str,
        start_time,
        end_time,
        reason: str = "Planned maintenance"
    ) -> ScheduledOutage:
        """Helper to create a scheduled outage record."""
        return ScheduledOutage.objects.create(
            outage_id=outage_id,
            scope=scope,
            target_id=target_id,
            start_time=start_time,
            end_time=end_time,
            reason=reason
        )


class FaultIncidentRepository:
    """
    Repository encapsulating database persistence for FaultIncident tickets and AffectedPoles.
    """

    @staticmethod
    def get_by_id(ticket_id: str) -> Optional[FaultIncident]:
        """Fetch an incident by UUID ticket_id."""
        try:
            return FaultIncident.objects.prefetch_related('affected_poles').get(ticket_id=ticket_id)
        except FaultIncident.DoesNotExist:
            return None

    @staticmethod
    def get_active_incident_for_span(from_pole_id: str, to_pole_id: str) -> Optional[FaultIncident]:
        """Find an active (non-resolved) incident matching a specific span boundary."""
        return FaultIncident.objects.filter(
            from_pole_id=from_pole_id,
            to_pole_id=to_pole_id,
            status__in=[
                FaultIncident.STATUS_DETECTED,
                FaultIncident.STATUS_ACKNOWLEDGED,
                FaultIncident.STATUS_CREW_ASSIGNED,
                FaultIncident.STATUS_RESOLVED
            ]
        ).first()

    @staticmethod
    def get_active_incidents_by_dt(dt_id: str) -> List[FaultIncident]:
        """Retrieve active incidents under a DT."""
        return list(FaultIncident.objects.filter(
            dt_id=dt_id,
            status__in=[
                FaultIncident.STATUS_DETECTED,
                FaultIncident.STATUS_ACKNOWLEDGED,
                FaultIncident.STATUS_CREW_ASSIGNED,
                FaultIncident.STATUS_RESOLVED
            ]
        ).prefetch_related('affected_poles'))

    @classmethod
    def persist_incident_payload(cls, payload: IncidentPayload) -> FaultIncident:
        """
        Idempotently persists or updates a localized incident payload into MySQL DB.
        Guarantees: Exactly ONE ticket per physical fault span.
        """
        # Check if active incident already exists for this span/DT
        existing = None
        if payload.asset_type == 'span' and payload.from_pole_id and payload.to_pole_id:
            existing = cls.get_active_incident_for_span(payload.from_pole_id, payload.to_pole_id)

        if existing:
            # Update existing ticket with refreshed affected pole count and confidence
            existing.affected_poles_count = len(payload.affected_pole_ids)
            existing.confidence_score = payload.confidence_score
            existing.confidence_reasons = payload.confidence_reasons
            existing.save(update_fields=['affected_poles_count', 'confidence_score', 'confidence_reasons', 'updated_at'])

            # Refresh affected poles
            existing.affected_poles.all().delete()
            cls._create_affected_poles(existing, payload.affected_pole_ids, payload.to_pole_id)
            return existing

        # Create new FaultIncident ticket
        incident = FaultIncident.objects.create(
            asset_type=payload.asset_type,
            feeder_id=payload.feeder_id,
            dt_id=payload.dt_id,
            from_pole_id=payload.from_pole_id,
            to_pole_id=payload.to_pole_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            pincode=payload.pincode,
            affected_poles_count=len(payload.affected_pole_ids),
            confidence_score=payload.confidence_score,
            confidence_reasons=payload.confidence_reasons,
            status=FaultIncident.STATUS_DETECTED
        )

        cls._create_affected_poles(incident, payload.affected_pole_ids, payload.to_pole_id)
        return incident

    @staticmethod
    def _create_affected_poles(incident: FaultIncident, pole_ids: List[str], boundary_pole_id: Optional[str]):
        """Helper to bulk create AffectedPole rows."""
        affected_rows = []
        for pid in pole_ids:
            affected_rows.append(AffectedPole(
                incident=incident,
                pole_id=pid,
                is_boundary=(pid == boundary_pole_id)
            ))
        if affected_rows:
            AffectedPole.objects.bulk_create(affected_rows, batch_size=500)

    @staticmethod
    def resolve_incidents_for_dt(dt_id: str) -> int:
        """
        Auto-verifies and closes all active incidents under a DT when telemetry confirms restoration.
        """
        now = timezone.now()
        updated = FaultIncident.objects.filter(
            dt_id=dt_id,
            status__in=[
                FaultIncident.STATUS_DETECTED,
                FaultIncident.STATUS_ACKNOWLEDGED,
                FaultIncident.STATUS_CREW_ASSIGNED,
                FaultIncident.STATUS_RESOLVED
            ]
        ).update(
            status=FaultIncident.STATUS_VERIFIED_CLOSED,
            resolved_at=now
        )
        return updated
