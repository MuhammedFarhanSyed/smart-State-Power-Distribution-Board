from typing import Dict, Any, List, Tuple


class PromptBuilder:
    """
    Constructs structured system and user prompts for operator decision support tasks.
    Ensures LLMs respond strictly in JSON format.
    """

    SYSTEM_ROLE = (
        "You are an expert electrical distribution grid AI assistant for Karnataka ESCOM control room operators. "
        "Your task is strictly operator decision support. You do NOT localize faults. "
        "Always respond in valid, parseable JSON."
    )

    @classmethod
    def build_summary_prompt(cls, incident_data: Dict[str, Any]) -> Tuple[str, str]:
        """Constructs prompt for plain-English incident summary."""
        user_prompt = f"""
Analyze the following electrical distribution fault incident and produce a concise 2-sentence operator summary.

Incident Data:
- Ticket ID: {incident_data.get('ticket_id')}
- Asset Type: {incident_data.get('asset_type')}
- DT ID: {incident_data.get('dt_id')}
- Primary Span: {incident_data.get('from_pole_id')} -> {incident_data.get('to_pole_id')}
- Affected Poles Count: {incident_data.get('affected_poles_count')}
- PIN Code: {incident_data.get('pincode')}
- Confidence: {incident_data.get('confidence_score')}
- Status: {incident_data.get('status')}

Respond ONLY with valid JSON in this format:
{{
  "summary": "Concise 2-sentence summary here.",
  "priority": "HIGH|MEDIUM|LOW",
  "key_takeaway": "One-line takeaway for 2 a.m. operator"
}}
"""
        return cls.SYSTEM_ROLE, user_prompt.strip()

    @classmethod
    def build_confidence_explanation_prompt(cls, incident_data: Dict[str, Any]) -> Tuple[str, str]:
        """Constructs prompt for confidence score explanation."""
        user_prompt = f"""
Explain the diagnostic confidence score of {incident_data.get('confidence_score')} for this fault incident.

Diagnostic Reasons:
{incident_data.get('confidence_reasons')}

Topology Inferred: {incident_data.get('is_inferred', False)}

Respond ONLY with valid JSON in this format:
{{
  "confidence_score": {incident_data.get('confidence_score')},
  "explanation": "Clear explanation of why this confidence score was assigned.",
  "data_quality_assessment": "Assessment of telemetry and topology quality"
}}
"""
        return cls.SYSTEM_ROLE, user_prompt.strip()

    @classmethod
    def build_recommendation_prompt(cls, incident_data: Dict[str, Any]) -> Tuple[str, str]:
        """Constructs prompt for crew size, equipment, and repair effort recommendation."""
        user_prompt = f"""
Provide advisory dispatch recommendations for the following fault:

Asset Type: {incident_data.get('asset_type')}
Span: {incident_data.get('from_pole_id')} -> {incident_data.get('to_pole_id')}
Affected Poles: {incident_data.get('affected_poles_count')}
GPS: {incident_data.get('latitude')}, {incident_data.get('longitude')}

Respond ONLY with valid JSON in this format:
{{
  "recommended_crew_size": 2,
  "vehicle_type": "Ladder Van / Two-Wheeler",
  "required_equipment": ["11kV LT line repair kit", "Insulated gloves", "PCC pole ladder"],
  "estimated_repair_time_minutes": 45,
  "safety_advisory": "Ensure DT isolator switch opened before climbing pole."
}}
"""
        return cls.SYSTEM_ROLE, user_prompt.strip()

    @classmethod
    def build_handover_prompt(cls, active_incidents: List[Dict[str, Any]], resolved_incidents: List[Dict[str, Any]]) -> Tuple[str, str]:
        """Constructs prompt for shift handover report."""
        user_prompt = f"""
Generate a shift handover summary for the incoming control room operator.

Active Incidents ({len(active_incidents)}):
{active_incidents}

Recently Resolved Incidents ({len(resolved_incidents)}):
{resolved_incidents}

Respond ONLY with valid JSON in this format:
{{
  "shift_summary": "Executive summary of shift activity.",
  "active_issues_count": {len(active_incidents)},
  "resolved_issues_count": {len(resolved_incidents)},
  "pending_action_items": ["Item 1", "Item 2"]
}}
"""
        return cls.SYSTEM_ROLE, user_prompt.strip()
