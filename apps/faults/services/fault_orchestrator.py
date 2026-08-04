from typing import Dict, List, Optional
from apps.network.services.topology_builder import TopologyBuilderService
from apps.telemetry.repositories import TelemetryRepository
from apps.faults.repositories import FaultIncidentRepository, ScheduledOutageRepository
from core_engine.algorithms.incident_grouper import IncidentGrouper
from apps.faults.models import FaultIncident


class FaultOrchestratorService:
    """
    Orchestration service bridging Django framework repositories and the pure Python core localization algorithms.
    Loads graph trees, retrieves active scheduled outages, runs boundary detection/incident grouping,
    and persists ticket records.
    NEVER implements localization logic inside itself.
    """

    @classmethod
    def evaluate_dt_fault_state(
        cls,
        dt_id: str,
        telemetry_states: Optional[Dict[str, bool]] = None
    ) -> List[FaultIncident]:
        """
        Evaluates current energization state for a Distribution Transformer.

        :param dt_id: Primary key of Distribution Transformer.
        :param telemetry_states: Optional map of pole_id or device_id -> is_energized (bool).
        :return: List of created or updated FaultIncident database records.
        """
        # If telemetry_states not explicitly passed, query current states from TelemetryRepository
        if telemetry_states is None:
            # Load tree poles first to know what to query
            tree_base = TopologyBuilderService.build_tree_for_dt(dt_id)
            if not tree_base or not tree_base.nodes:
                return []
            pole_ids = list(tree_base.nodes.keys())
            telemetry_states = TelemetryRepository.get_latest_states_by_poles(pole_ids)

        # 1. Load pure-Python NetworkTree domain object
        tree = TopologyBuilderService.build_tree_for_dt(dt_id, telemetry_states=telemetry_states)
        if not tree or not tree.nodes:
            return []

        # 2. Check for power restoration (all poles live)
        all_live = all(node.is_energized for node in tree.nodes.values())
        if all_live:
            # Auto-verify & close active tickets for this DT via telemetry confirmation
            FaultIncidentRepository.resolve_incidents_for_dt(dt_id)
            return []

        # 3. Retrieve active scheduled outages (to suppress planned load shedding alerts)
        active_scheduled_outages = ScheduledOutageRepository.get_active_outages()

        # 4. Invoke pure-Python localization engine
        incident_payloads = IncidentGrouper.group_incidents(
            tree=tree,
            active_scheduled_outages=active_scheduled_outages
        )

        # 5. Persist incident payloads into FaultIncident DB records
        persisted_incidents: List[FaultIncident] = []
        for payload in incident_payloads:
            incident = FaultIncidentRepository.persist_incident_payload(payload)
            persisted_incidents.append(incident)

        return persisted_incidents
