from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path("telemetry/", views.ingest_telemetry_view, name="ingest-telemetry"),
    path("incidents/", views.incident_list, name="incident-list"),
    path("incidents/<int:incident_id>/acknowledge/", views.acknowledge_incident, name="acknowledge-incident"),
    path("incidents/<int:incident_id>/assign/", views.assign_crew, name="assign-crew"),
    path("incidents/<int:incident_id>/repair-reported/", views.report_repair, name="report-repair"),
    path("simulator/faults/", views.inject_simulated_fault, name="inject-simulated-fault"),
    path("simulator/incidents/<int:incident_id>/repair/", views.simulate_repair, name="simulate-repair"),
]
