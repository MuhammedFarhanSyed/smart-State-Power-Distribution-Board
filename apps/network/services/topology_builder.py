from typing import Dict, Optional, List
from apps.network.repositories import PoleRepository, TransformerRepository, FeederRepository
from core_engine.domain.models import NetworkTree, NodeState


class TopologyBuilderService:
    """
    Service responsible for loading electrical network assets from database repositories
    and constructing in-memory radial tree/graph representations for algorithm processing.
    """

    @classmethod
    def build_tree_for_dt(
        cls,
        dt_id: str,
        telemetry_states: Optional[Dict[str, bool]] = None,
        device_last_seen: Optional[Dict[str, float]] = None
    ) -> Optional[NetworkTree]:
        """
        Loads electrical network poles for a given DT and constructs an in-memory NetworkTree.

        :param dt_id: Primary key of the Distribution Transformer.
        :param telemetry_states: Optional map of pole_id/device_id -> energized (bool).
        :param device_last_seen: Optional map of pole_id/device_id -> last_seen_ts (float).
        :return: Fully populated NetworkTree object, or None if DT does not exist.
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

        # Pass 1: Instantiate NodeState for each static pole asset
        for pole in poles:
            pid = pole.pole_id
            parent_id = pole.parent_pole_id

            if pole.seq_on_line is None or (parent_id is None and pole.seq_on_line != 1):
                is_inferred = True

            # Lookup current energization state (default True/Live if telemetry unprovided)
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

            if parent_id:
                children_map.setdefault(parent_id, []).append(pid)
            elif pole.seq_on_line == 1 or parent_id is None:
                root_pole_ids.append(pid)

        # Pass 2: Connect children pointers to parent nodes
        for parent_id, c_ids in children_map.items():
            if parent_id in nodes:
                nodes[parent_id].children_ids = c_ids

        # Fallback root resolution if topology is unsequenced
        if not root_pole_ids and nodes:
            root_pole_ids.append(min(nodes.keys()))

        return NetworkTree(
            dt_id=dt_id,
            feeder_id=dt.feeder_id,
            root_pole_ids=root_pole_ids,
            nodes=nodes,
            is_topology_inferred=is_inferred
        )

    @classmethod
    def get_trees_for_feeder(
        cls,
        feeder_id: str,
        telemetry_states: Optional[Dict[str, bool]] = None
    ) -> List[NetworkTree]:
        """
        Retrieves in-memory NetworkTree objects for all transformers under an 11kV feeder.
        """
        dts = TransformerRepository.list_by_feeder(feeder_id)
        trees: List[NetworkTree] = []

        for dt in dts:
            tree = cls.build_tree_for_dt(dt.dt_id, telemetry_states=telemetry_states)
            if tree:
                trees.append(tree)

        return trees
