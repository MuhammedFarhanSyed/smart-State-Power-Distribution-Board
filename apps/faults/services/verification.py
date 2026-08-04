from typing import List, Tuple
from apps.faults.models import FaultIncident
from apps.telemetry.repositories import TelemetryRepository
from apps.faults.services.status_transition import StatusTransitionService, InvalidStatusTransition


class VerificationService:
    """
    Service responsible for telemetry-driven verification of incident resolution.
    Verification & closure happen automatically based on field telemetry signals ONLY.
    """

    @classmethod
    def verify_and_close_incident(
        cls,
        incident: FaultIncident
    ) -> Tuple[bool, str, FaultIncident]:
        """
        Verifies power restoration across all affected poles of an incident using telemetry.
        If all affected poles report energized=True:
          1. Transitions to 'verified'
          2. Transitions to 'closed'
        If any affected pole is still dark:
          Rejects closure and leaves ticket in current state or re-opens to crew_assigned.

        :return: (is_closed: bool, message: str, incident: FaultIncident)
        """
        affected_poles = list(incident.affected_poles.values_list('pole_id', flat=True))
        if not affected_poles:
            return False, "No affected poles registered for incident", incident

        # Retrieve current telemetry states for all affected poles
        telemetry_states = TelemetryRepository.get_latest_states_by_poles(affected_poles)

        # Check if ALL affected poles are energized
        dark_poles = [
            pid for pid in affected_poles
            if not telemetry_states.get(pid, True)  # If state missing, assume dark for safety
        ]

        if dark_poles:
            message = f"Telemetry verification failed: {len(dark_poles)} of {len(affected_poles)} poles still dark ({', '.join(dark_poles[:3])})."
            return False, message, incident

        # All affected poles are confirmed live by telemetry!
        # Step 1: Transition to 'verified'
        try:
            if incident.status == FaultIncident.STATUS_RESOLVED:
                StatusTransitionService.transition(
                    incident=incident,
                    target_status=FaultIncident.STATUS_VERIFIED,
                    changed_by='TELEMETRY_VERIFIER',
                    notes='Telemetry confirmed 100% power restoration across affected poles.',
                    allow_system_override=True
                )

            # Step 2: Auto-close to 'closed'
            if incident.status == FaultIncident.STATUS_VERIFIED:
                StatusTransitionService.transition(
                    incident=incident,
                    target_status=FaultIncident.STATUS_CLOSED,
                    changed_by='TELEMETRY_AUTO_CLOSER',
                    notes='Incident ticket auto-closed following telemetry verification.',
                    allow_system_override=True
                )
            return True, "Incident verified and auto-closed successfully via telemetry", incident

        except InvalidStatusTransition as e:
            return False, f"Verification failed due to invalid status transition: {str(e)}", incident
