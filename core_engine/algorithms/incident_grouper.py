from dataclasses import dataclass
from typing import List, Optional, Dict
from core_engine.domain.models import NetworkTree, EdgeSpan
from core_engine.algorithms.boundary_detector import BoundaryDetector
from core_engine.algorithms.noise_filter import NoiseFilter
from core_engine.algorithms.confidence_calculator import ConfidenceCalculator


@dataclass
class IncidentPayload:
    """
    Pure Python domain DTO representing a localized physical incident ready for ticket persistence.
    """
    asset_type: str  # 'span', 'dt', 'feeder'
    dt_id: str
    feeder_id: str
    from_pole_id: Optional[str]
    to_pole_id: Optional[str]
    affected_pole_ids: List[str]
    confidence_score: float
    confidence_reasons: List[str]
    latitude: float
    longitude: float
    pincode: Optional[str]


class IncidentGrouper:
    """
    Pure Python service that groups dark downstream pole clusters into single incident payloads.
    Filters dead sensors and calculates diagnostic confidence.
    """

    @classmethod
    def group_incidents(
        cls,
        tree: NetworkTree,
        active_scheduled_outages: Optional[List[Dict[str, str]]] = None
    ) -> List[IncidentPayload]:
        """
        Processes tree energization state and returns a list of distinct localized incidents.
        Guarantees: Exactly 1 incident per snapped wire span / DT fault.
        """
        active_scheduled_outages = active_scheduled_outages or []
        boundaries = BoundaryDetector.find_boundary_spans(tree)
        incidents: List[IncidentPayload] = []

        if not boundaries:
            return []

        for fault_type, span in boundaries:
            if fault_type == "DT":
                # Transformer-level fault
                all_pole_ids = list(tree.nodes.keys())

                # Check load-shedding suppression
                is_scheduled = NoiseFilter.is_scheduled_outage(tree.dt_id, 'dt', active_scheduled_outages)
                if is_scheduled:
                    continue

                score, reasons = ConfidenceCalculator.calculate(
                    tree=tree,
                    affected_pole_ids=all_pole_ids,
                    has_power_lost_packet=True,
                    is_scheduled=False
                )

                root_node = tree.nodes.get(tree.root_pole_ids[0]) if tree.root_pole_ids else None
                lat = root_node.latitude if root_node else 0.0
                lon = root_node.longitude if root_node else 0.0
                pincode = root_node.pincode if root_node else None

                incidents.append(IncidentPayload(
                    asset_type='dt',
                    dt_id=tree.dt_id,
                    feeder_id=tree.feeder_id,
                    from_pole_id=None,
                    to_pole_id=None,
                    affected_pole_ids=all_pole_ids,
                    confidence_score=score,
                    confidence_reasons=reasons,
                    latitude=lat,
                    longitude=lon,
                    pincode=pincode
                ))

            elif fault_type == "SPAN" and span:
                to_pole_id = span.to_pole_id

                # Dead Sensor Filter: If dark pole has live children, it's a dead sensor -> IGNORE
                if NoiseFilter.is_dead_sensor(tree, to_pole_id):
                    continue

                # Collect all downstream dark poles in sub-tree
                affected_pole_ids = tree.get_downstream_subtree(to_pole_id)

                # Check load-shedding suppression
                is_scheduled = NoiseFilter.is_scheduled_outage(tree.dt_id, 'dt', active_scheduled_outages)
                if is_scheduled:
                    continue

                score, reasons = ConfidenceCalculator.calculate(
                    tree=tree,
                    affected_pole_ids=affected_pole_ids,
                    has_power_lost_packet=True,
                    is_scheduled=False
                )

                to_node = tree.get_node(to_pole_id)
                lat = to_node.latitude if to_node else 0.0
                lon = to_node.longitude if to_node else 0.0
                pincode = to_node.pincode if to_node else None

                incidents.append(IncidentPayload(
                    asset_type='span',
                    dt_id=tree.dt_id,
                    feeder_id=tree.feeder_id,
                    from_pole_id=span.from_pole_id,
                    to_pole_id=span.to_pole_id,
                    affected_pole_ids=affected_pole_ids,
                    confidence_score=score,
                    confidence_reasons=reasons,
                    latitude=lat,
                    longitude=lon,
                    pincode=pincode
                ))

        return incidents
