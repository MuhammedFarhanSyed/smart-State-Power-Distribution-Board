import unittest
from core_engine.domain.models import NetworkTree, NodeState
from core_engine.algorithms.boundary_detector import BoundaryDetector
from core_engine.algorithms.noise_filter import NoiseFilter
from core_engine.algorithms.incident_grouper import IncidentGrouper


class TestLocalizationLogic(unittest.TestCase):
    """
    Pure Python unit test suite for fault localization graph algorithms.
    Runs in microseconds without starting Django or requiring a database connection.
    """

    def setUp(self):
        """Set up standard sample network tree nodes."""
        self.dt_id = "D-0112"
        self.feeder_id = "F-07-03"

    def test_span_fault_localization(self):
        """
        Scenario:
        DT -> P1 (Live) -> P2 (Live) -> P3 (Dark) -> P4 (Dark)
        Core Logic Requirement:
        The fault exists on SPAN P2 -> P3. Exactly 1 ticket created for P3 and P4.
        """
        nodes = {
            "P1": NodeState(pole_id="P1", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=True, parent_id=None, children_ids=["P2"], seq_on_line=1),
            "P2": NodeState(pole_id="P2", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=True, parent_id="P1", children_ids=["P3"], seq_on_line=2),
            "P3": NodeState(pole_id="P3", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=False, parent_id="P2", children_ids=["P4"], seq_on_line=3),
            "P4": NodeState(pole_id="P4", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=False, parent_id="P3", children_ids=[], seq_on_line=4),
        }
        tree = NetworkTree(dt_id=self.dt_id, feeder_id=self.feeder_id, root_pole_ids=["P1"], nodes=nodes)

        incidents = IncidentGrouper.group_incidents(tree)

        self.assertEqual(len(incidents), 1, "Must generate exactly 1 ticket for a snapped wire")
        inc = incidents[0]
        self.assertEqual(inc.asset_type, 'span')
        self.assertEqual(inc.from_pole_id, 'P2')
        self.assertEqual(inc.to_pole_id, 'P3')
        self.assertIn('P3', inc.affected_pole_ids)
        self.assertIn('P4', inc.affected_pole_ids)
        self.assertEqual(len(inc.affected_pole_ids), 2)

    def test_dead_sensor_rejection(self):
        """
        Scenario:
        DT -> P1 (Live) -> P2 (Dark) -> P3 (Live)
        Core Logic Requirement:
        A dark pole with live downstream children is physically impossible.
        Must be rejected as a dead sensor (0 tickets emitted).
        """
        nodes = {
            "P1": NodeState(pole_id="P1", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=True, parent_id=None, children_ids=["P2"], seq_on_line=1),
            "P2": NodeState(pole_id="P2", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=False, parent_id="P1", children_ids=["P3"], seq_on_line=2),
            "P3": NodeState(pole_id="P3", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=True, parent_id="P2", children_ids=[], seq_on_line=3),
        }
        tree = NetworkTree(dt_id=self.dt_id, feeder_id=self.feeder_id, root_pole_ids=["P1"], nodes=nodes)

        self.assertTrue(NoiseFilter.is_dead_sensor(tree, "P2"))

        incidents = IncidentGrouper.group_incidents(tree)
        self.assertEqual(len(incidents), 0, "Dead sensor must generate 0 outage tickets")

    def test_scheduled_outage_suppression(self):
        """
        Scenario:
        DT is 100% dark, but matches active scheduled load-shedding window for D-0112.
        Core Logic Requirement:
        Suppressed from emitting fault alerts (0 tickets emitted).
        """
        nodes = {
            "P1": NodeState(pole_id="P1", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=False, parent_id=None, children_ids=["P2"], seq_on_line=1),
            "P2": NodeState(pole_id="P2", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=False, parent_id="P1", children_ids=[], seq_on_line=2),
        }
        tree = NetworkTree(dt_id=self.dt_id, feeder_id=self.feeder_id, root_pole_ids=["P1"], nodes=nodes)
        scheduled_outages = [{'target_id': self.dt_id, 'scope': 'dt'}]

        incidents = IncidentGrouper.group_incidents(tree, active_scheduled_outages=scheduled_outages)
        self.assertEqual(len(incidents), 0, "Scheduled load shedding must be suppressed")

    def test_multiple_simultaneous_faults(self):
        """
        Scenario:
        2 separate wire breaks on the same DT:
        Branch A: P1 (Live) -> P2 (Live) -> P3 (Dark) -> P4 (Dark)
        Branch B: P1 (Live) -> P10 (Live) -> P11 (Dark)
        Core Logic Requirement:
        Must generate exactly 2 distinct tickets (Span P2-P3 and Span P10-P11).
        """
        nodes = {
            # Root
            "P1": NodeState(pole_id="P1", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=True, parent_id=None, children_ids=["P2", "P10"], seq_on_line=1),
            # Branch A
            "P2": NodeState(pole_id="P2", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=True, parent_id="P1", children_ids=["P3"], seq_on_line=2),
            "P3": NodeState(pole_id="P3", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=False, parent_id="P2", children_ids=["P4"], seq_on_line=3),
            "P4": NodeState(pole_id="P4", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=False, parent_id="P3", children_ids=[], seq_on_line=4),
            # Branch B
            "P10": NodeState(pole_id="P10", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=True, parent_id="P1", children_ids=["P11"], seq_on_line=2),
            "P11": NodeState(pole_id="P11", dt_id=self.dt_id, feeder_id=self.feeder_id, is_energized=False, parent_id="P10", children_ids=[], seq_on_line=3),
        }
        tree = NetworkTree(dt_id=self.dt_id, feeder_id=self.feeder_id, root_pole_ids=["P1"], nodes=nodes)

        incidents = IncidentGrouper.group_incidents(tree)

        self.assertEqual(len(incidents), 2, "Must generate exactly 2 distinct tickets for 2 separate wire breaks")
        spans = {(inc.from_pole_id, inc.to_pole_id) for inc in incidents}
        self.assertIn(('P2', 'P3'), spans)
        self.assertIn(('P10', 'P11'), spans)


if __name__ == '__main__':
    unittest.main()
