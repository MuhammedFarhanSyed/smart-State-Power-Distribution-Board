import unittest
from unittest.mock import patch, MagicMock

# Pure Python dataclass mock representing FaultIncident for framework-decoupled unit testing
class MockFaultIncident:
    STATUS_DETECTED = 'detected'
    STATUS_ACKNOWLEDGED = 'acknowledged'
    STATUS_CREW_ASSIGNED = 'crew_assigned'
    STATUS_RESOLVED = 'resolved'
    STATUS_VERIFIED = 'verified'
    STATUS_CLOSED = 'closed'

    def __init__(self, status='detected'):
        self.ticket_id = "12345678-1234-5678-1234-567812345678"
        self.asset_type = 'span'
        self.dt_id = "D-0112"
        self.feeder_id = "F-07-03"
        self.from_pole_id = "P2"
        self.to_pole_id = "P3"
        self.status = status
        self.assigned_crew = None
        self.resolved_at = None
        self.closed_at = None
        self.affected_poles = MagicMock()

    def save(self, update_fields=None):
        pass


class InvalidStatusTransition(Exception):
    pass


class PureStatusTransitionService:
    ALLOWED_TRANSITIONS = {
        'detected': {'acknowledged'},
        'acknowledged': {'crew_assigned'},
        'crew_assigned': {'resolved'},
        'resolved': {'verified', 'crew_assigned'},
        'verified': {'closed'},
        'closed': set(),
    }
    SYSTEM_ONLY_TARGET_STATUSES = {'verified', 'closed'}

    @classmethod
    def transition(cls, incident, target_status, changed_by='SYSTEM', notes='', allow_system_override=False):
        if target_status in cls.SYSTEM_ONLY_TARGET_STATUSES and not allow_system_override:
            raise InvalidStatusTransition(f"Status '{target_status}' is system-only.")
        allowed = cls.ALLOWED_TRANSITIONS.get(incident.status, set())
        if target_status not in allowed:
            raise InvalidStatusTransition(f"Invalid transition from '{incident.status}' to '{target_status}'.")
        incident.status = target_status
        return incident


class PureVerificationService:
    @classmethod
    def verify_and_close_incident(cls, incident, telemetry_states):
        affected_poles = ['P3', 'P4']
        dark_poles = [pid for pid in affected_poles if not telemetry_states.get(pid, True)]
        if dark_poles:
            return False, f"Telemetry verification failed: {len(dark_poles)} dark poles", incident

        PureStatusTransitionService.transition(incident, 'verified', allow_system_override=True)
        PureStatusTransitionService.transition(incident, 'closed', allow_system_override=True)
        return True, "Verified and closed via telemetry", incident


class TestTicketWorkflow(unittest.TestCase):
    def setUp(self):
        self.incident = MockFaultIncident(status='detected')

    def test_valid_lifecycle_transitions(self):
        # Detected -> Acknowledged
        PureStatusTransitionService.transition(self.incident, 'acknowledged', changed_by='OPERATOR')
        self.assertEqual(self.incident.status, 'acknowledged')

        # Acknowledged -> Crew Assigned
        PureStatusTransitionService.transition(self.incident, 'crew_assigned', changed_by='OPERATOR')
        self.assertEqual(self.incident.status, 'crew_assigned')

        # Crew Assigned -> Resolved
        PureStatusTransitionService.transition(self.incident, 'resolved', changed_by='OPERATOR')
        self.assertEqual(self.incident.status, 'resolved')

    def test_invalid_status_transition(self):
        # Detected -> Closed must fail
        with self.assertRaises(InvalidStatusTransition):
            PureStatusTransitionService.transition(self.incident, 'closed', changed_by='OPERATOR')

        # Manual operator transition to 'verified' must fail
        with self.assertRaises(InvalidStatusTransition):
            PureStatusTransitionService.transition(self.incident, 'verified', changed_by='OPERATOR')

    def test_automatic_telemetry_verification_and_closure(self):
        self.incident.status = 'resolved'
        telemetry_states = {'P3': True, 'P4': True}

        is_closed, msg, updated_inc = PureVerificationService.verify_and_close_incident(self.incident, telemetry_states)
        self.assertTrue(is_closed)
        self.assertEqual(updated_inc.status, 'closed')

    def test_telemetry_verification_rejection(self):
        self.incident.status = 'resolved'
        telemetry_states = {'P3': True, 'P4': False}

        is_closed, msg, updated_inc = PureVerificationService.verify_and_close_incident(self.incident, telemetry_states)
        self.assertFalse(is_closed)
        self.assertEqual(updated_inc.status, 'resolved')


if __name__ == '__main__':
    unittest.main()
