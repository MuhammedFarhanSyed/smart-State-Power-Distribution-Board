from django.urls import path
from apps.telemetry.views import TelemetryIngestView

app_name = 'telemetry'

urlpatterns = [
    path('telemetry/', TelemetryIngestView.as_view(), name='ingest'),
]
