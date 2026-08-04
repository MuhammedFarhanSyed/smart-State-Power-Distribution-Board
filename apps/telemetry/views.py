from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.telemetry.serializers import TelemetryIngestSerializer
from apps.telemetry.services.ingestion import IngestionService


class TelemetryIngestView(APIView):
    """
    REST API endpoint for ingesting IoT pole telemetry payloads.
    Endpoint: POST /api/telemetry/
    """

    def post(self, request, *args, **kwargs):
        serializer = TelemetryIngestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        success, message, result_dto = IngestionService.process_payload(serializer.validated_data)

        if not success:
            return Response(
                {
                    "status": "rejected",
                    "message": message
                },
                status=status.HTTP_202_ACCEPTED
            )

        return Response(
            {
                "status": "accepted",
                "message": message,
                "data": result_dto
            },
            status=status.HTTP_202_ACCEPTED
        )
