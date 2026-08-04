from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.faults.serializers import (
    FaultIncidentSerializer,
    AssignCrewSerializer,
    ResolveIncidentSerializer
)
from apps.faults.services.incident_service import IncidentService
from apps.faults.services.status_transition import InvalidStatusTransition


class IncidentListView(APIView):
    """
    GET /api/incidents/
    List all incidents with optional query filters (status, dt_id, feeder_id).
    """

    def get(self, request, *args, **kwargs):
        status_filter = request.query_params.get('status')
        dt_id_filter = request.query_params.get('dt_id')
        feeder_id_filter = request.query_params.get('feeder_id')

        incidents = IncidentService.list_incidents(
            status=status_filter,
            dt_id=dt_id_filter,
            feeder_id=feeder_id_filter
        )
        serializer = FaultIncidentSerializer(incidents, many=True)
        return Response({"count": len(incidents), "results": serializer.data}, status=status.HTTP_200_OK)


class IncidentDetailView(APIView):
    """
    GET /api/incidents/{id}/
    Retrieve detailed incident record with timeline and affected poles.
    """

    def get(self, request, ticket_id, *args, **kwargs):
        incident = IncidentService.get_incident(ticket_id)
        if not incident:
            return Response({"error": f"Incident '{ticket_id}' not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = FaultIncidentSerializer(incident)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IncidentAcknowledgeView(APIView):
    """
    PATCH /api/incidents/{id}/acknowledge/
    Transitions incident status: Detected -> Acknowledged.
    """

    def patch(self, request, ticket_id, *args, **kwargs):
        try:
            incident = IncidentService.acknowledge_incident(ticket_id=ticket_id, operator_name='OPERATOR')
            serializer = FaultIncidentSerializer(incident)
            return Response({"message": "Incident acknowledged.", "data": serializer.data}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except InvalidStatusTransition as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class IncidentAssignCrewView(APIView):
    """
    PATCH /api/incidents/{id}/assign/
    Transitions incident status: Acknowledged -> Crew Assigned.
    """

    def patch(self, request, ticket_id, *args, **kwargs):
        serializer = AssignCrewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        crew_name = serializer.validated_data['crew_name']
        notes = serializer.validated_data.get('notes', '')

        try:
            incident = IncidentService.assign_crew(ticket_id=ticket_id, crew_name=crew_name, notes=notes, operator_name='OPERATOR')
            incident_serializer = FaultIncidentSerializer(incident)
            return Response({"message": f"Crew '{crew_name}' assigned successfully.", "data": incident_serializer.data}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except InvalidStatusTransition as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class IncidentResolveView(APIView):
    """
    PATCH /api/incidents/{id}/resolve/
    Transitions incident status: Crew Assigned -> Resolved.
    Triggers automated telemetry verification for closure.
    """

    def patch(self, request, ticket_id, *args, **kwargs):
        serializer = ResolveIncidentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        notes = serializer.validated_data.get('notes', '')

        try:
            incident, is_closed, verification_msg = IncidentService.mark_resolved(ticket_id=ticket_id, notes=notes, operator_name='OPERATOR')
            incident_serializer = FaultIncidentSerializer(incident)
            return Response(
                {
                    "message": "Incident marked resolved.",
                    "telemetry_verification_passed": is_closed,
                    "verification_details": verification_msg,
                    "data": incident_serializer.data
                },
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except InvalidStatusTransition as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
