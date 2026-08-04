from typing import Dict, Any, List, Optional
from apps.simulator.models import ActiveFault
from apps.simulator.services.network_simulator import NetworkSimulator
from apps.simulator.services.telemetry_generator import TelemetryGenerator
from apps.simulator.services.noise_generator import NoiseGenerator


class FaultInjector:
    """
    Injects Span Faults, Transformer Faults, and Feeder Faults by generating telemetry payloads.
    Applies real-world noise rules (packet loss, dead sensors, out-of-order) and pushes payloads into ingestion.
    """

    @classmethod
    def inject_span_fault(
        cls,
        dt_id: str,
        from_pole_id: str,
        to_pole_id: str,
        apply_noise: bool = True
    ) -> ActiveFault:
        """
        Injects a wire span break between from_pole_id and to_pole_id.
        All downstream poles under to_pole_id become dark.
        """
        tree = NetworkSimulator.get_network_tree(dt_id)
        affected_ids = tree.get_downstream_subtree(to_pole_id) if tree else [to_pole_id]

        # Record ActiveFault entry
        fault = ActiveFault.objects.create(
            fault_type=ActiveFault.FAULT_SPAN,
            target_id=dt_id,
            from_pole_id=from_pole_id,
            to_pole_id=to_pole_id,
            is_repaired=False
        )

        # Generate telemetry for dark downstream poles
        for pid in affected_ids:
            node = tree.get_node(pid) if tree else None
            dev_id = node.device_id if node and node.device_id else f"DEV-{pid}"
            fw = '1.4'

            # Evaluate dying packet drop noise rule
            if apply_noise and NoiseGenerator.should_drop_dying_packet('power_lost', firmware=fw):
                continue  # 30% lost dying packet / FW 1.2 quiet mode

            payload = TelemetryGenerator.build_payload(
                device_id=dev_id,
                pole_id=pid,
                event='power_lost',
                energized=False,
                firmware=fw
            )
            TelemetryGenerator.push_telemetry(dt_id=dt_id, payload=payload)

        return fault

    @classmethod
    def inject_transformer_fault(
        cls,
        dt_id: str,
        apply_noise: bool = True
    ) -> ActiveFault:
        """
        Injects a transformer / fuse blow fault.
        100% of poles under the DT become dark.
        """
        tree = NetworkSimulator.get_network_tree(dt_id)
        all_pole_ids = list(tree.nodes.keys()) if tree and tree.nodes else []

        fault = ActiveFault.objects.create(
            fault_type=ActiveFault.FAULT_TRANSFORMER,
            target_id=dt_id,
            is_repaired=False
        )

        for pid in all_pole_ids:
            node = tree.get_node(pid)
            dev_id = node.device_id if node and node.device_id else f"DEV-{pid}"
            fw = '1.4'

            if apply_noise and NoiseGenerator.should_drop_dying_packet('power_lost', firmware=fw):
                continue

            payload = TelemetryGenerator.build_payload(
                device_id=dev_id,
                pole_id=pid,
                event='power_lost',
                energized=False,
                firmware=fw
            )
            TelemetryGenerator.push_telemetry(dt_id=dt_id, payload=payload)

        return fault

    @classmethod
    def inject_feeder_fault(
        cls,
        feeder_id: str,
        dt_ids: List[str],
        apply_noise: bool = True
    ) -> ActiveFault:
        """
        Injects a 11kV feeder trip fault.
        Poles across all DTs under the feeder become dark.
        """
        fault = ActiveFault.objects.create(
            fault_type=ActiveFault.FAULT_FEEDER,
            target_id=feeder_id,
            is_repaired=False
        )

        for dt_id in dt_ids:
            cls.inject_transformer_fault(dt_id=dt_id, apply_noise=apply_noise)

        return fault
