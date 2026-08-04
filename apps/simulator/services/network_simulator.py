from typing import Dict, Optional, List
from apps.network.services.topology_builder import TopologyBuilderService
from core_engine.domain.models import NetworkTree


class NetworkSimulator:
    """
    Service responsible for loading and maintaining in-memory network topology state
    for simulation execution.
    """

    _cached_trees: Dict[str, NetworkTree] = {}

    @classmethod
    def load_network_tree(cls, dt_id: str = 'D-0112') -> Optional[NetworkTree]:
        """
        Loads network tree for a DT from database assets and caches it in memory.
        """
        tree = TopologyBuilderService.build_tree_for_dt(dt_id)
        if tree:
            cls._cached_trees[dt_id] = tree
        return tree

    @classmethod
    def get_network_tree(cls, dt_id: str = 'D-0112') -> Optional[NetworkTree]:
        """
        Retrieves cached network tree or loads it on demand.
        """
        if dt_id not in cls._cached_trees:
            return cls.load_network_tree(dt_id)
        return cls._cached_trees[dt_id]

    @classmethod
    def reset_network(cls, dt_id: str = 'D-0112'):
        """Resets cached network state."""
        cls._cached_trees.pop(dt_id, None)
        return cls.load_network_tree(dt_id)
