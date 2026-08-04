from typing import Dict, Any, List
from apps.faults.repositories import FaultIncidentRepository, ScheduledOutageRepository
from apps.faults.models import FaultIncident
from apps.ai_assistant.services.prompt_builder import PromptBuilder
from apps.ai_assistant.services.llm_client import LLMClient
from apps.ai_assistant.services.fallback_service import FallbackService


class RecommendationService:
    """
    Service generating advisory crew dispatch recommendations and shift handover summaries.
    """

    @classmethod
    def generate_recommendations(cls, ticket_id: str) -> Dict[str, Any]:
        incident = FaultIncidentRepository.get_by_id(ticket_id)
        if not incident:
            return {"error": f"Incident '{ticket_id}' not found."}

        incident_data = {
            "ticket_id": str(incident.ticket_id),
            "asset_type": incident.asset_type,
            "from_pole_id": incident.from_pole_id,
            "to_pole_id": incident.to_pole_id,
            "affected_poles_count": incident.affected_poles_count,
            "latitude": float(incident.latitude),
            "longitude": float(incident.longitude)
        }

        system_prompt, user_prompt = PromptBuilder.build_recommendation_prompt(incident_data)
        fallback = FallbackService.get_recommendation_fallback(incident_data)

        return LLMClient.generate_json_response(system_prompt, user_prompt, fallback)

    @classmethod
    def generate_shift_handover(cls) -> Dict[str, Any]:
        active_incidents = list(
            FaultIncident.objects.filter(status__in=['detected', 'acknowledged', 'crew_assigned', 'resolved'])
            .values('ticket_id', 'dt_id', 'asset_type', 'affected_poles_count', 'status')[:10]
        )

        resolved_incidents = list(
            FaultIncident.objects.filter(status__in=['verified', 'closed'])
            .values('ticket_id', 'dt_id', 'asset_type', 'affected_poles_count', 'closed_at')[:10]
        )

        system_prompt, user_prompt = PromptBuilder.build_handover_prompt(active_incidents, resolved_incidents)
        fallback = FallbackService.get_handover_fallback(active_incidents, resolved_incidents)

        return LLMClient.generate_json_response(system_prompt, user_prompt, fallback)
