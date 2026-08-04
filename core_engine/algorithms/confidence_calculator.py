from typing import List, Tuple
from core_engine.domain.models import NetworkTree


class ConfidenceCalculator:
    """
    Pure Python service calculating fault localization confidence score (0.0 to 1.0)
    and generating an audit trail of human-readable diagnostic reasons.
    """

    @classmethod
    def calculate(
        cls,
        tree: NetworkTree,
        affected_pole_ids: List[str],
        has_power_lost_packet: bool = True,
        is_scheduled: bool = False
    ) -> Tuple[float, List[str]]:
        """
        Calculates confidence score and list of diagnostic explanations.

        :return: (confidence_score: float, reasoning_list: List[str])
        """
        reasons: List[str] = []
        score = 1.0

        if is_scheduled:
            return 0.0, ["Suppressed: Matches scheduled load-shedding window."]

        # 1. Topology certainty penalty
        if tree.is_topology_inferred:
            score -= 0.20
            reasons.append("Topology inferred from GPS coordinates (60% unsequenced network).")
        else:
            reasons.append("Topology verified from pole registry (40% sequenced network).")

        # 2. Telemetry density check
        total_affected = len(affected_pole_ids)
        telemetry_count = sum(
            1 for pid in affected_pole_ids
            if tree.get_node(pid) and tree.get_node(pid).has_telemetry_device
        )

        coverage_ratio = telemetry_count / float(total_affected) if total_affected > 0 else 0.0

        if coverage_ratio >= 0.8:
            reasons.append(f"High telemetry density ({int(coverage_ratio * 100)}% devices reporting).")
        elif coverage_ratio >= 0.5:
            score -= 0.15
            reasons.append(f"Moderate telemetry density ({int(coverage_ratio * 100)}% devices reporting).")
        else:
            score -= 0.30
            reasons.append(f"Low telemetry density ({int(coverage_ratio * 100)}% devices reporting).")

        # 3. Capacitor power_lost packet vs heartbeat timeout
        if has_power_lost_packet:
            reasons.append("Direct capacitor reserve power_lost packet received from frontier device.")
        else:
            score -= 0.15
            reasons.append("Inferred from missed heartbeat timeout (FW 1.2 quiet mode).")

        # Bound score between 0.0 and 1.0
        final_score = max(0.0, min(1.0, round(score, 2)))
        return final_score, reasons
