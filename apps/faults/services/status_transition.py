from typing import Optional, Dict, Set
from django.utils import timezone
from apps.faults.models import FaultIncident, IncidentTimeline


class InvalidStatusTransition(Exception):
    """Exception raised when an invalid status transition is attempted."""
    pass


class StatusTransitionService:
    """
    Enforces valid state transition paths for FaultIncident lifecycle and records complete timeline history.
    Lifecycle Path: Detected -> Acknowledged -> Crew Assigned -> Resolved -> Verified -> Closed.
    """

    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        FaultIncident.STATUS_DETECTED: {FaultIncident.STATUS_ACKNOWLEDGED},
        FaultIncident.STATUS_ACKNOWLEDGED: {FaultIncident.STATUS_CREW_ASSIGNED},
        FaultIncident.STATUS_CREW_ASSIGNED: {FaultIncident.STATUS_RESOLVED},
        FaultIncident.STATUS_RESOLVED: {FaultIncident.STATUS_VERIFIED, FaultIncident.STATUS_CREW_ASSIGNED}, # Re-assign if verification fails
        FaultIncident.STATUS_VERIFIED: {FaultIncident.STATUS_CLOSED},
        FaultIncident.STATUS_CLOSED: set(),  # Terminal state
    }

    SYSTEM_ONLY_TARGET_STATUSES = {
        FaultIncident.STATUS_VERIFIED,
        FaultIncident.STATUS_CLOSED
    }

    @classmethod
    def transition(
        cls,
        incident: FaultIncident,
        target_status: str,
        changed_by: str = 'SYSTEM',
        notes: str = '',
        allow_system_override: bool = False
    ) -> FaultIncident:
        """
        Executes a status transition, enforcing validity rules and timeline recording.

        :param incident: FaultIncident model instance.
        :param target_status: Target status string.
        :param changed_by: Username, operator role, or 'SYSTEM'.
        :param notes: Explanatory notes.
        :param allow_system_override: Set True for telemetry-driven automated verification.
        :return: Updated FaultIncident instance.
        """
        current_status = incident.status

        # 1. Reject manual operator calls to system-only statuses (verified, closed)
        if target_status in cls.SYSTEM_ONLY_TARGET_STATUSES and not allow_system_override:
            raise InvalidStatusTransition(
                f"Status '{target_status}' can only be executed automatically by telemetry verification, not manual operator input."
            )

        # 2. Check if transition path is allowed
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise InvalidStatusTransition(
                f"Invalid transition from '{current_status}' to '{target_status}'. Allowed target statuses: {list(allowed)}"
            )

        # 3. Apply state changes
        incident.status = target_status
        now = timezone.now()

        if target_status == FaultIncident.STATUS_RESOLVED:
            incident.resolved_at = now
        elif target_status == FaultIncident.STATUS_CLOSED:
            incident.closed_at = now

        update_fields = ['status', 'updated_at']
        if incident.resolved_at:
            update_fields.append('resolved_at')
        if incident.closed_at:
            update_fields.append('closed_at')

        incident.save(update_fields=update_fields)

        # 4. Record complete timeline event
        IncidentTimeline.objects.create(
            incident=incident,
            from_status=current_status,
            to_status=target_status,
            changed_by=changed_by,
            notes=notes
        )

        return incident
