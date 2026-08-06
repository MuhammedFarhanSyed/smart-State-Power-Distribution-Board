from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from .models import Incident
from network.models import Feeder, Pole, Transformer
from .serializers import AssignCrewSerializer, IncidentSerializer, SimulatorFaultSerializer, TelemetryPayloadSerializer
from .services.telemetry import ingest_telemetry


@api_view(["GET"])
def health_check(request):
    """Small endpoint used to verify that the backend is running."""
    return Response({"status": "ok"})


@api_view(["POST"])
def ingest_telemetry_view(request):
    serializer = TelemetryPayloadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        result = ingest_telemetry(serializer.validated_data)
    except ValueError as error:
        return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {"accepted": result.accepted, "detail": result.reason},
        status=status.HTTP_201_CREATED if result.accepted else status.HTTP_200_OK,
    )


@api_view(["GET"])
def incident_list(request):
    """Return tickets for the operator dashboard, newest first."""
    incidents = Incident.objects.select_related(
        "feeder", "transformer", "upstream_pole", "downstream_pole"
    ).order_by("-detected_at")
    return Response(IncidentSerializer(incidents, many=True).data)


@api_view(["POST"])
def acknowledge_incident(request, incident_id: int):
    incident = get_object_or_404(Incident, id=incident_id)
    if incident.status != Incident.Status.DETECTED:
        return Response({"detail": "Only detected incidents can be acknowledged."}, status=400)
    incident.status = Incident.Status.ACKNOWLEDGED
    incident.save(update_fields=["status"])
    return Response(IncidentSerializer(incident).data)


@api_view(["POST"])
def assign_crew(request, incident_id: int):
    incident = get_object_or_404(Incident, id=incident_id)
    serializer = AssignCrewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if incident.status not in [Incident.Status.DETECTED, Incident.Status.ACKNOWLEDGED]:
        return Response({"detail": "This incident cannot be assigned in its current state."}, status=400)
    incident.status = Incident.Status.CREW_ASSIGNED
    incident.assigned_crew = serializer.validated_data["crew_name"]
    incident.save(update_fields=["status", "assigned_crew"])
    return Response(IncidentSerializer(incident).data)


@api_view(["POST"])
def report_repair(request, incident_id: int):
    """Record a crew report. Restoration telemetry remains the source of truth."""
    incident = get_object_or_404(Incident, id=incident_id)
    if incident.status != Incident.Status.CREW_ASSIGNED:
        return Response({"detail": "Only an assigned incident can have a repair reported."}, status=400)
    from django.utils import timezone

    incident.status = Incident.Status.REPAIR_REPORTED
    incident.repair_reported_at = timezone.now()
    incident.save(update_fields=["status", "repair_reported_at"])
    return Response(IncidentSerializer(incident).data)


@api_view(["POST"])
def inject_simulated_fault(request):
    """Testing-only endpoint. It emits telemetry; it never creates an incident directly."""
    serializer = SimulatorFaultSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    from .services import simulator

    data = serializer.validated_data
    try:
        if data["fault_type"] == "span":
            result = simulator.inject_span_fault(data["downstream_pole_id"])
        elif data["fault_type"] == "transformer":
            result = simulator.inject_transformer_fault(data["dt_id"])
        else:
            result = simulator.inject_feeder_fault(data["feeder_id"])
    except (ValueError, Pole.DoesNotExist, Transformer.DoesNotExist, Feeder.DoesNotExist) as error:
        return Response({"detail": str(error)}, status=400)
    return Response(result, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def simulate_repair(request, incident_id: int):
    """Testing-only restoration telemetry for a ticket already marked repair-reported."""
    incident = get_object_or_404(Incident, id=incident_id)
    if incident.status != Incident.Status.REPAIR_REPORTED:
        return Response({"detail": "Mark repair reported before simulating restoration."}, status=400)
    from .services import simulator

    try:
        result = simulator.repair_incident(incident.id)
    except ValueError as error:
        return Response({"detail": str(error)}, status=400)
    incident.refresh_from_db()
    return Response({"simulation": result, "incident": IncidentSerializer(incident).data})
