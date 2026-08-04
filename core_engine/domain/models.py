from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set


@dataclass
class NodeState:
    """
    Pure Python domain model representing the state of an LT Pole node in the network tree.
    Completely decoupled from Django ORM.
    """
    pole_id: str
    dt_id: str
    feeder_id: str
    is_energized: bool = True
    last_seen_ts: Optional[float] = None
    device_id: Optional[str] = None
    has_telemetry_device: bool = True
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    latitude: float = 0.0
    longitude: float = 0.0
    seq_on_line: Optional[int] = None
    pincode: Optional[str] = None

    @property
    def is_dark(self) -> bool:
        return not self.is_energized


@dataclass
class EdgeSpan:
    """
    Represents a physical wire span edge between an upstream pole and a downstream pole.
    """
    from_pole_id: str  # Upstream (typically Live)
    to_pole_id: str    # Downstream (typically Dark)


@dataclass
class NetworkTree:
    """
    Pure Python domain representation of an LT distribution network tree under a DT or Feeder.
    Provides fast, in-memory graph operations without DB IO.
    """
    dt_id: str
    feeder_id: str
    root_pole_ids: List[str] = field(default_factory=list)
    nodes: Dict[str, NodeState] = field(default_factory=dict)
    is_topology_inferred: bool = False

    def get_node(self, pole_id: str) -> Optional[NodeState]:
        """Fetch a node by pole_id."""
        return self.nodes.get(pole_id)

    def get_parent(self, pole_id: str) -> Optional[NodeState]:
        """Fetch the parent node of a given pole."""
        node = self.get_node(pole_id)
        if node and node.parent_id:
            return self.nodes.get(node.parent_id)
        return None

    def get_children(self, pole_id: str) -> List[NodeState]:
        """Fetch immediate child nodes of a given pole."""
        node = self.get_node(pole_id)
        if not node:
            return []
        return [self.nodes[cid] for cid in node.children_ids if cid in self.nodes]

    def get_downstream_subtree(self, start_pole_id: str) -> List[str]:
        """
        Traverse downstream BFS/DFS to collect all pole IDs in the subtree rooted at start_pole_id (inclusive).
        Time Complexity: O(Subtree Size)
        """
        subtree: List[str] = []
        stack: List[str] = [start_pole_id]
        visited: Set[str] = set()

        while stack:
            current_id = stack.pop()
            if current_id in visited:
                continue
            visited.add(current_id)
            subtree.append(current_id)

            node = self.get_node(current_id)
            if node:
                # Add children to stack
                for cid in node.children_ids:
                    if cid not in visited:
                        stack.append(cid)

        return subtree

    def get_upstream_path(self, start_pole_id: str) -> List[str]:
        """
        Traverse upstream from start_pole_id to the root DT connection.
        Time Complexity: O(Depth)
        """
        path: List[str] = []
        current = self.get_node(start_pole_id)
        visited: Set[str] = set()

        while current and current.pole_id not in visited:
            visited.add(current.pole_id)
            path.append(current.pole_id)
            if not current.parent_id:
                break
            current = self.get_node(current.parent_id)

        return path
