from typing import Optional, List, Tuple
from apps.faults.models import FaultIncident
from apps.faults.repositories import FaultIncidentRepository
from apps.faults.services.status_transition import StatusTransitionService
from apps.faults.services.verification import VerificationService


class IncidentService:
    """
    Service layer orchestrating incident lifecycle management and operator actions.
    """

    @staticmethod
    def get_incident(ticket_id: str) -> Optional[FaultIncident]:
        """Fetch incident by ticket UUID string."""
        return FaultIncidentRepository.get_by_id(ticket_id)

    @staticmethod
    def list_incidents(
        status: Optional[str] = None,
        dt_id: Optional[str] = None,
        feeder_id: Optional[str] = None
    ) -> List[FaultIncident]:
        """List incidents with optional filters."""
        qs = FaultIncident.objects.prefetch_related('affected_poles', 'timeline').all()
        if status:
            qs = qs.filter(status=status)
        if dt_id:
            qs = qs.filter(dt_id=dt_id)
        if feeder_id:
            qs = qs.filter(feeder_id=feeder_id)
        return list(qs)

    @classmethod
    def acknowledge_incident(cls, ticket_id: str, operator_name: str = 'OPERATOR') -> FaultIncident:
        """
        Transitions incident status from Detected -> Acknowledged.
        """
        incident = cls.get_incident(ticket_id)
        if not incident:
            raise ValueError(f"Incident with ticket_id '{ticket_id}' not found.")

        return StatusTransitionService.transition(
            incident=incident,
            target_status=FaultIncident.STATUS_ACKNOWLEDGED,
            changed_by=operator_name,
            notes="Incident acknowledged by control room operator."
        )

    @classmethod
    def assign_crew(
        cls,
        ticket_id: str,
        crew_name: str,
        notes: str = '',
        operator_name: str = 'OPERATOR'
    ) -> FaultIncident:
        """
        Transitions incident status from Acknowledged -> Crew Assigned.
        """
        incident = cls.get_incident(ticket_id)
        if not incident:
            raise ValueError(f"Incident with ticket_id '{ticket_id}' not found.")

        incident.assigned_crew = crew_name
        incident.save(update_fields=['assigned_crew', 'updated_at'])

        return StatusTransitionService.transition(
            incident=incident,
            target_status=FaultIncident.STATUS_CREW_ASSIGNED,
            changed_by=operator_name,
            notes=f"Crew '{crew_name}' assigned to dispatch. {notes}".strip()
        )

    @classmethod
    def mark_resolved(
        cls,
        ticket_id: str,
        notes: str = '',
        operator_name: str = 'OPERATOR'
    ) -> Tuple[FaultIncident, bool, str]:
        """
        Transitions incident status from Crew Assigned -> Resolved.
        Immediately triggers VerificationService to perform telemetry-based auto-closure.

        :return: (incident: FaultIncident, is_verified_closed: bool, verification_message: str)
        """
        incident = cls.get_incident(ticket_id)
        if not incident:
            raise ValueError(f"Incident with ticket_id '{ticket_id}' not found.")

        # 1. Transition to Resolved
        incident = StatusTransitionService.transition(
            incident=incident,
            target_status=FaultIncident.STATUS_RESOLVED,
            changed_by=operator_name,
            notes=f"Marked resolved by operator. Triggering telemetry verification... {notes}".strip()
        )

        # 2. Trigger automated telemetry verification
        is_closed, verification_msg, updated_incident = VerificationService.verify_and_close_incident(incident)

        return updated_incident, is_closed, verification_msg
