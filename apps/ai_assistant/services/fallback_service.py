from typing import Dict, Any, List


class FallbackService:
    """
    Deterministic rule-based fallback service invoked when external LLM providers fail or are unconfigured.
    Guarantees 100% availability for control room operators without throwing errors.
    """

    @classmethod
    def get_summary_fallback(cls, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        asset_type = incident_data.get('asset_type', 'span').upper()
        from_pole = incident_data.get('from_pole_id', 'Unknown')
        to_pole = incident_data.get('to_pole_id', 'Unknown')
        dt_id = incident_data.get('dt_id', 'Unknown')
        count = incident_data.get('affected_poles_count', 1)

        summary = (
            f"Detected {asset_type} fault on DT {dt_id} between poles {from_pole} and {to_pole}. "
            f"A total of {count} downstream poles are currently dark."
        )

        return {
            "summary": summary,
            "priority": "HIGH" if count > 5 else "MEDIUM",
            "key_takeaway": f"Dispatch crew to inspect span {from_pole} -> {to_pole}.",
            "is_fallback": True
        }

    @classmethod
    def get_confidence_fallback(cls, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        score = incident_data.get('confidence_score', 0.8)
        reasons = incident_data.get('confidence_reasons', ["Deterministic boundary detection"])

        explanation = (
            f"Localization confidence score is {int(score * 100)}% based on deterministic live/dark boundary traversal. "
            f"Audit reasons: {', '.join(reasons)}."
        )

        return {
            "confidence_score": score,
            "explanation": explanation,
            "data_quality_assessment": "Evaluated using deterministic tree boundary rules.",
            "is_fallback": True
        }

    @classmethod
    def get_recommendation_fallback(cls, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        count = incident_data.get('affected_poles_count', 1)
        asset_type = incident_data.get('asset_type', 'span')

        crew_size = 3 if asset_type == 'dt' or count > 20 else 2
        vehicle = "Heavy Repair Van" if asset_type == 'dt' else "LT Repair Vehicle"
        time_est = 60 if asset_type == 'dt' else 35

        return {
            "recommended_crew_size": crew_size,
            "vehicle_type": vehicle,
            "required_equipment": [
                "11kV LT conductor repair kit",
                "Safety harness & insulated gloves",
                "PCC pole climbing ladder"
            ],
            "estimated_repair_time_minutes": time_est,
            "safety_advisory": "Isolate upstream transformer breaker before commencing line repair.",
            "is_fallback": True
        }

    @classmethod
    def get_handover_fallback(cls, active_incidents: List[Dict[str, Any]], resolved_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "shift_summary": f"Shift completed with {len(active_incidents)} active incidents and {len(resolved_incidents)} resolved incidents.",
            "active_issues_count": len(active_incidents),
            "resolved_issues_count": len(resolved_incidents),
            "pending_action_items": [
                f"Monitor {len(active_incidents)} active fault tickets for telemetry verification.",
                "Review upcoming scheduled load-shedding windows."
            ],
            "is_fallback": True
        }
