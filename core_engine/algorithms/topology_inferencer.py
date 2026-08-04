import math
from typing import List, Dict, Tuple, Optional
from core_engine.domain.models import NetworkTree, NodeState


class TopologyInferencer:
    """
    Pure Python spatial algorithm for inferring radial network tree structures
    for transformers with missing wiring sequence (~60% of network).
    Uses geometric proximity (Euclidean distance) from the transformer outwards to build MST edges.
    """

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates approximate ground distance in meters between two GPS coordinates."""
        # Simple equirectangular approximation for small distances (~4m accuracy)
        lat_mid = math.radians((lat1 + lat2) / 2.0)
        d_lat = math.radians(lat2 - lat1) * 6371000.0
        d_lon = math.radians(lon2 - lon1) * 6371000.0 * math.cos(lat_mid)
        return math.sqrt(d_lat * d_lat + d_lon * d_lon)

    @classmethod
    def infer_radial_tree(
        cls,
        dt_id: str,
        feeder_id: str,
        dt_lat: float,
        dt_lon: float,
        nodes: Dict[str, NodeState]
    ) -> NetworkTree:
        """
        Infers parent-child links for unsequenced nodes based on spatial proximity to DT and upstream nodes.
        Time Complexity: O(N^2) for Prim's MST construction where N <= 240 poles per DT.
        """
        if not nodes:
            return NetworkTree(dt_id=dt_id, feeder_id=feeder_id, root_pole_ids=[], nodes={}, is_topology_inferred=True)

        unvisited = set(nodes.keys())
        visited_nodes: Dict[str, NodeState] = {}
        root_pole_ids: List[str] = []

        # Find closest pole to DT coordinates as the primary root
        closest_root_id: Optional[str] = None
        min_dt_dist = float('inf')

        for pid, node in nodes.items():
            dist = cls.calculate_distance(dt_lat, dt_lon, node.latitude, node.longitude)
            if dist < min_dt_dist:
                min_dt_dist = dist
                closest_root_id = pid

        if closest_root_id:
            root_node = nodes[closest_root_id]
            root_node.seq_on_line = 1
            root_node.parent_id = None
            visited_nodes[closest_root_id] = root_node
            unvisited.remove(closest_root_id)
            root_pole_ids.append(closest_root_id)

        # Prim's algorithm to connect remaining unvisited poles to nearest visited pole
        seq_counter = 2
        while unvisited:
            best_parent_id: Optional[str] = None
            best_child_id: Optional[str] = None
            min_edge_dist = float('inf')

            for parent_id in visited_nodes.keys():
                parent_node = visited_nodes[parent_id]
                for child_id in unvisited:
                    child_node = nodes[child_id]
                    dist = cls.calculate_distance(
                        parent_node.latitude, parent_node.longitude,
                        child_node.latitude, child_node.longitude
                    )
                    if dist < min_edge_dist:
                        min_edge_dist = dist
                        best_parent_id = parent_id
                        best_child_id = child_id

            if best_parent_id and best_child_id:
                child_node = nodes[best_child_id]
                child_node.parent_id = best_parent_id
                child_node.seq_on_line = seq_counter
                visited_nodes[best_parent_id].children_ids.append(best_child_id)

                visited_nodes[best_child_id] = child_node
                unvisited.remove(best_child_id)
                seq_counter += 1
            else:
                break

        return NetworkTree(
            dt_id=dt_id,
            feeder_id=feeder_id,
            root_pole_ids=root_pole_ids,
            nodes=visited_nodes,
            is_topology_inferred=True
        )
