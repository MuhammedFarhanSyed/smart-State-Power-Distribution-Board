from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.ai_assistant.services.incident_summary import IncidentSummaryService
from apps.ai_assistant.services.recommendation_service import RecommendationService


class IncidentSummaryView(APIView):
    """
    POST /api/ai/incident-summary/{incident_id}
    Generates plain-English summary for an incident ticket.
    """

    def post(self, request, incident_id, *args, **kwargs):
        res = IncidentSummaryService.generate_summary(incident_id)
        if "error" in res:
            return Response(res, status=status.HTTP_404_NOT_FOUND)
        return Response(res, status=status.HTTP_200_OK)


class ExplainConfidenceView(APIView):
    """
    POST /api/ai/explain-confidence/{incident_id}
    Explains the diagnostic confidence score and telemetry quality.
    """

    def post(self, request, incident_id, *args, **kwargs):
        res = IncidentSummaryService.explain_confidence(incident_id)
        if "error" in res:
            return Response(res, status=status.HTTP_404_NOT_FOUND)
        return Response(res, status=status.HTTP_200_OK)


class CrewRecommendationView(APIView):
    """
    POST /api/ai/recommendation/{incident_id}
    Provides advisory recommendations for crew size, vehicle type, and equipment.
    """

    def post(self, request, incident_id, *args, **kwargs):
        res = RecommendationService.generate_recommendations(incident_id)
        if "error" in res:
            return Response(res, status=status.HTTP_404_NOT_FOUND)
        return Response(res, status=status.HTTP_200_OK)


class ShiftHandoverView(APIView):
    """
    POST /api/ai/handover
    Generates shift handover summary for control room operators.
    """

    def post(self, request, *args, **kwargs):
        res = RecommendationService.generate_shift_handover()
        return Response(res, status=status.HTTP_200_OK)
