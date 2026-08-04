from typing import Dict, Optional, List
from apps.network.repositories import PoleRepository, TransformerRepository
from core_engine.domain.models import NetworkTree, NodeState


class TopologyBuilderService:
    """
    Service responsible for assembling pure-Python in-memory NetworkTree instances
    from Django ORM database records for use in graph traversal algorithms.
    """

    @classmethod
    def build_tree_for_dt(
        cls,
        dt_id: str,
        telemetry_states: Optional[Dict[str, bool]] = None,
        device_last_seen: Optional[Dict[str, float]] = None
    ) -> Optional[NetworkTree]:
        """
        Retrieves poles for a given DT from the database and constructs a NetworkTree DTO.

        :param dt_id: Primary key of the Distribution Transformer.
        :param telemetry_states: Map of pole_id or device_id -> energized (bool).
        :param device_last_seen: Map of pole_id or device_id -> last_seen_ts (float).
        :return: Fully populated NetworkTree domain object.
        """
        dt = TransformerRepository.get_by_id(dt_id)
        if not dt:
            return None

        poles = PoleRepository.get_poles_by_dt(dt_id)
        if not poles.exists():
            return NetworkTree(dt_id=dt_id, feeder_id=dt.feeder_id, root_pole_ids=[], nodes={})

        nodes: Dict[str, NodeState] = {}
        children_map: Dict[str, List[str]] = {}
        root_pole_ids: List[str] = []
        is_inferred = False

        telemetry_states = telemetry_states or {}
        device_last_seen = device_last_seen or {}

        # First pass: Instantiate NodeState for each pole
        for pole in poles:
            pid = pole.pole_id
            parent_id = pole.parent_pole_id

            if pole.seq_on_line is None or (parent_id is None and pole.seq_on_line != 1):
                is_inferred = True

            # Determine energization state from telemetry map (defaults to True/Live)
            is_energized = telemetry_states.get(pid, True)
            if pole.device_id and pole.device_id in telemetry_states:
                is_energized = telemetry_states[pole.device_id]

            last_seen = device_last_seen.get(pid)
            if pole.device_id and pole.device_id in device_last_seen:
                last_seen = device_last_seen[pole.device_id]

            node = NodeState(
                pole_id=pid,
                dt_id=dt_id,
                feeder_id=dt.feeder_id,
                is_energized=is_energized,
                last_seen_ts=last_seen,
                device_id=pole.device_id,
                has_telemetry_device=bool(pole.device_id),
                parent_id=parent_id,
                children_ids=[],
                latitude=float(pole.latitude),
                longitude=float(pole.longitude),
                seq_on_line=pole.seq_on_line,
                pincode=pole.pincode
            )
            nodes[pid] = node

            # Track parent -> children relationship
            if parent_id:
                children_map.setdefault(parent_id, []).append(pid)
            elif pole.seq_on_line == 1 or parent_id is None:
                root_pole_ids.append(pid)

        # Second pass: Attach children_ids lists to parent nodes
        for parent_id, c_ids in children_map.items():
            if parent_id in nodes:
                nodes[parent_id].children_ids = c_ids

        # If no explicit root pole was marked (e.g. unsequenced network), pick lowest seq or first pole
        if not root_pole_ids and nodes:
            first_pole_id = min(nodes.keys())
            root_pole_ids.append(first_pole_id)

        return NetworkTree(
            dt_id=dt_id,
            feeder_id=dt.feeder_id,
            root_pole_ids=root_pole_ids,
            nodes=nodes,
            is_topology_inferred=is_inferred
        )
