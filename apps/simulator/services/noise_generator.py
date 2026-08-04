import random
from typing import Dict, Any, List, Optional


class NoiseGenerator:
    """
    Applies real-world telemetry noise rules:
    - 30% dying packet loss (radio congestion)
    - FW 1.2 quiet fleet mode (no power_lost packet)
    - Duplicate packet generation
    - Out-of-order sequence numbers
    - Isolated dead sensor simulation
    """

    DYING_PACKET_LOSS_PROBABILITY = 0.30  # 30% of power_lost packets lost

    @classmethod
    def should_drop_dying_packet(cls, event: str, firmware: str = '1.4') -> bool:
        """
        Determines if a dying power_lost packet should be dropped due to:
        1. FW 1.2 fleet mode (100% loss of power_lost packets)
        2. 30% capacitor radio loss
        """
        if event != 'power_lost':
            return False

        # FW 1.2 never sends power_lost packets
        if firmware == '1.2':
            return True

        # 30% loss for FW 1.3+ reserve capacitors
        return random.random() < cls.DYING_PACKET_LOSS_PROBABILITY

    @classmethod
    def generate_duplicate_payload(cls, original_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a duplicate packet with matching sequence number."""
        dup = dict(original_payload)
        return dup

    @classmethod
    def generate_out_of_order_payload(cls, original_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generates an out-of-order stale packet with a lower sequence number."""
        stale = dict(original_payload)
        stale['seq'] = max(0, original_payload.get('seq', 10) - 5)
        return stale
