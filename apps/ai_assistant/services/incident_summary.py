from typing import Dict, Any, List
from apps.faults.repositories import FaultIncidentRepository
from apps.ai_assistant.services.prompt_builder import PromptBuilder
from apps.ai_assistant.services.llm_client import LLMClient
from apps.ai_assistant.services.fallback_service import FallbackService


class IncidentSummaryService:
    """
    Service responsible for generating plain-English incident summaries and explaining confidence scores.
    """

    @classmethod
    def generate_summary(cls, ticket_id: str) -> Dict[str, Any]:
        incident = FaultIncidentRepository.get_by_id(ticket_id)
        if not incident:
            return {"error": f"Incident '{ticket_id}' not found."}

        incident_data = {
            "ticket_id": str(incident.ticket_id),
            "asset_type": incident.asset_type,
            "dt_id": incident.dt_id,
            "from_pole_id": incident.from_pole_id,
            "to_pole_id": incident.to_pole_id,
            "affected_poles_count": incident.affected_poles_count,
            "pincode": incident.pincode,
            "confidence_score": incident.confidence_score,
            "status": incident.status
        }

        system_prompt, user_prompt = PromptBuilder.build_summary_prompt(incident_data)
        fallback = FallbackService.get_summary_fallback(incident_data)

        return LLMClient.generate_json_response(system_prompt, user_prompt, fallback)

    @classmethod
    def explain_confidence(cls, ticket_id: str) -> Dict[str, Any]:
        incident = FaultIncidentRepository.get_by_id(ticket_id)
        if not incident:
            return {"error": f"Incident '{ticket_id}' not found."}

        incident_data = {
            "ticket_id": str(incident.ticket_id),
            "confidence_score": incident.confidence_score,
            "confidence_reasons": incident.confidence_reasons,
            "is_inferred": any("inferred" in r.lower() for r in incident.confidence_reasons)
        }

        system_prompt, user_prompt = PromptBuilder.build_confidence_explanation_prompt(incident_data)
        fallback = FallbackService.get_confidence_fallback(incident_data)

        return LLMClient.generate_json_response(system_prompt, user_prompt, fallback)
