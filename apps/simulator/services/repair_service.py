from typing import List, Optional
from django.utils import timezone
from apps.simulator.models import ActiveFault
from apps.simulator.services.network_simulator import NetworkSimulator
from apps.simulator.services.telemetry_generator import TelemetryGenerator
from apps.faults.models import FaultIncident
from apps.faults.repositories import FaultIncidentRepository


class RepairService:
    """
    Simulates physical field repairs by restoring power and pushing boot, power_restored,
    and heartbeat telemetry signals into the ingestion pipeline.
    Enables automatic verification and ticket closure.
    """

    @classmethod
    def repair_fault(cls, fault_id: str) -> bool:
        """
        Repairs an injected fault by ID.
        Pushes power restoration telemetry streams for affected poles.
        """
        try:
            fault = ActiveFault.objects.get(fault_id=fault_id)
        except ActiveFault.DoesNotExist:
            return False

        if fault.is_repaired:
            return True  # Already repaired

        dt_id = fault.target_id
        tree = NetworkSimulator.get_network_tree(dt_id)

        # Determine poles needing restoration telemetry
        poles_to_restore: List[str] = []
        if fault.fault_type == ActiveFault.FAULT_SPAN and fault.to_pole_id:
            poles_to_restore = tree.get_downstream_subtree(fault.to_pole_id) if tree else [fault.to_pole_id]
        else:
            poles_to_restore = list(tree.nodes.keys()) if tree and tree.nodes else []

        # Push boot and power_restored telemetry for each restored pole
        for pid in poles_to_restore:
            node = tree.get_node(pid) if tree else None
            dev_id = node.device_id if node and node.device_id else f"DEV-{pid}"

            # 1. Boot event (resets seq counter)
            boot_payload = TelemetryGenerator.build_payload(
                device_id=dev_id,
                pole_id=pid,
                event='boot',
                energized=True
            )
            TelemetryGenerator.push_telemetry(dt_id=dt_id, payload=boot_payload)

            # 2. Power Restored event
            restored_payload = TelemetryGenerator.build_payload(
                device_id=dev_id,
                pole_id=pid,
                event='power_restored',
                energized=True
            )
            TelemetryGenerator.push_telemetry(dt_id=dt_id, payload=restored_payload)

            # 3. Energized Heartbeat event
            hb_payload = TelemetryGenerator.build_payload(
                device_id=dev_id,
                pole_id=pid,
                event='heartbeat',
                energized=True
            )
            TelemetryGenerator.push_telemetry(dt_id=dt_id, payload=hb_payload)

        # Mark active fault as repaired
        fault.is_repaired = True
        fault.repaired_at = timezone.now()
        fault.save(update_fields=['is_repaired', 'repaired_at', 'updated_at'])

        # Auto-verify active incidents under this DT
        active_incidents = FaultIncidentRepository.get_active_incidents_by_dt(dt_id)
        for inc in active_incidents:
            if inc.status == FaultIncident.STATUS_RESOLVED:
                from apps.faults.services.verification import VerificationService
                VerificationService.verify_and_close_incident(inc)

        return True
