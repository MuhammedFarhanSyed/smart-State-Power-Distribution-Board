from typing import List, Dict, Set, Optional
from core_engine.domain.models import NetworkTree, NodeState


class NoiseFilter:
    """
    Pure Python noise filter for validating physical electrical state constraints.
    Rejects dead sensors, impossible downstream live states, and suppresses scheduled outages.
    """

    @classmethod
    def is_dead_sensor(cls, tree: NetworkTree, pole_id: str) -> bool:
        """
        Checks if a dark pole is an isolated dead sensor / faulty modem.
        A dark pole is a dead sensor if ANY downstream child/descendant pole is LIVE.
        In a radial tree, if a line snaps at pole X, ALL downstream poles MUST be dark.
        If downstream poles are live, electricity is flowing through pole X, meaning pole X's sensor is lying.
        """
        node = tree.get_node(pole_id)
        if not node or node.is_energized:
            return False  # Not dark, so not a dark sensor failure

        # Check downstream subtree for live poles
        downstream_ids = tree.get_downstream_subtree(pole_id)
        for c_id in downstream_ids:
            if c_id == pole_id:
                continue
            child_node = tree.get_node(c_id)
            if child_node and child_node.is_energized:
                return True  # Found a live downstream pole -> Single Dead Sensor!

        return False

    @classmethod
    def is_scheduled_outage(
        cls,
        target_id: str,
        target_scope: str,
        active_scheduled_outages: List[Dict[str, str]]
    ) -> bool:
        """
        Checks if a DT or Feeder outage matches an active scheduled load-shedding window.

        :param target_id: DT ID or Feeder ID.
        :param target_scope: 'dt' or 'feeder'.
        :param active_scheduled_outages: List of dicts [{'target_id': 'D-0112', 'scope': 'dt'}]
        """
        for outage in active_scheduled_outages:
            if outage.get('scope') == target_scope and outage.get('target_id') == target_id:
                return True
        return False
