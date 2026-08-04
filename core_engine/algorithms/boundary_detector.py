from typing import List, Optional, Tuple, Dict
from core_engine.domain.models import NetworkTree, NodeState, EdgeSpan


class BoundaryDetector:
    """
    Pure Python graph traversal algorithm for finding live/dark boundary edges in radial trees.
    Given a radial tree and node energization states, identifies:
    1. Span Fault: Live -> Dark transition edge (P_live -> P_dark).
    2. DT / Fuse Fault: 100% of poles under DT are dark with no live poles beneath.
    3. Feeder Fault: Entire feeder dark.
    """

    @classmethod
    def find_boundary_spans(cls, tree: NetworkTree) -> List[Tuple[str, Optional[EdgeSpan]]]:
        """
        Traverses tree branches starting from root poles.

        :return: List of tuples (fault_type: str, primary_span: Optional[EdgeSpan])
                 where fault_type is 'SPAN', 'DT', or 'NONE'.
        """
        if not tree.nodes:
            return []

        # Check if entire DT network is dark
        total_nodes = len(tree.nodes)
        dark_nodes = [node for node in tree.nodes.values() if node.is_dark]

        if len(dark_nodes) == total_nodes and total_nodes > 0:
            # Check if all root poles are dark with no live pole anywhere
            all_roots_dark = all(
                tree.get_node(r_id) and tree.get_node(r_id).is_dark
                for r_id in tree.root_pole_ids
            )
            if all_roots_dark:
                return [("DT", None)]

        # Traversal to find live -> dark boundary edges
        found_spans: List[Tuple[str, Optional[EdgeSpan]]] = []
        visited_nodes = set()

        for root_id in tree.root_pole_ids:
            root_node = tree.get_node(root_id)
            if not root_node:
                continue

            if root_node.is_dark:
                # Root pole itself is dark, check if parent is DT
                # The span is from DT -> root_id (or boundary edge)
                span = EdgeSpan(from_pole_id=f"DT-{tree.dt_id}", to_pole_id=root_id)
                found_spans.append(("SPAN", span))
            else:
                # Root is live, traverse downstream to find live -> dark transitions
                cls._search_downstream_boundaries(tree, root_id, found_spans, visited_nodes)

        return found_spans

    @classmethod
    def _search_downstream_boundaries(
        cls,
        tree: NetworkTree,
        current_id: str,
        results: List[Tuple[str, Optional[EdgeSpan]]],
        visited: set
    ):
        """DFS recursion following live paths to locate dark child transitions."""
        if current_id in visited:
            return
        visited.add(current_id)

        current_node = tree.get_node(current_id)
        if not current_node or current_node.is_dark:
            return  # Stop search along dark branches

        # Current is LIVE. Inspect children:
        for child_id in current_node.children_ids:
            child_node = tree.get_node(child_id)
            if not child_node:
                continue

            if child_node.is_dark:
                # Found Live -> Dark boundary edge! (current_id -> child_id)
                span = EdgeSpan(from_pole_id=current_id, to_pole_id=child_id)
                results.append(("SPAN", span))
            else:
                # Child is live, continue searching downstream
                cls._search_downstream_boundaries(tree, child_id, results, visited)
