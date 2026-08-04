from django.urls import path
from apps.faults.views import (
    IncidentListView,
    IncidentDetailView,
    IncidentAcknowledgeView,
    IncidentAssignCrewView,
    IncidentResolveView
)

app_name = 'faults'

urlpatterns = [
    path('incidents/', IncidentListView.as_view(), name='incident-list'),
    path('incidents/<str:ticket_id>/', IncidentDetailView.as_view(), name='incident-detail'),
    path('incidents/<str:ticket_id>/acknowledge/', IncidentAcknowledgeView.as_view(), name='incident-acknowledge'),
    path('incidents/<str:ticket_id>/assign/', IncidentAssignCrewView.as_view(), name='incident-assign'),
    path('incidents/<str:ticket_id>/resolve/', IncidentResolveView.as_view(), name='incident-resolve'),
]
