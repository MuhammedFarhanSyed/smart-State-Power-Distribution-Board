from django.urls import path
from apps.ai_assistant.views import (
    IncidentSummaryView,
    ExplainConfidenceView,
    CrewRecommendationView,
    ShiftHandoverView
)

app_name = 'ai_assistant'

urlpatterns = [
    path('ai/incident-summary/<str:incident_id>', IncidentSummaryView.as_view(), name='summary'),
    path('ai/explain-confidence/<str:incident_id>', ExplainConfidenceView.as_view(), name='explain-confidence'),
    path('ai/recommendation/<str:incident_id>', CrewRecommendationView.as_view(), name='recommendation'),
    path('ai/handover', ShiftHandoverView.as_view(), name='handover'),
]
