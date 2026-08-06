from rest_framework import serializers

from .models import Incident


class TelemetryPayloadSerializer(serializers.Serializer):
    """The HTTPS payload sent by one pole device."""

    device_id = serializers.CharField(max_length=60)
    pole_id = serializers.CharField(max_length=30)
    event = serializers.ChoiceField(choices=["heartbeat", "power_lost", "power_restored", "boot"])
    energized = serializers.BooleanField()
    ts = serializers.DateTimeField()
    seq = serializers.IntegerField(min_value=0)
    battery_mv = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    rssi = serializers.IntegerField(required=False, allow_null=True)
    fw = serializers.CharField(max_length=20, required=False, allow_blank=True)


class IncidentSerializer(serializers.ModelSerializer):
    upstream_pole_id = serializers.CharField(source="upstream_pole.pole_id", read_only=True)
    downstream_pole_id = serializers.CharField(source="downstream_pole.pole_id", read_only=True)
    transformer_id = serializers.CharField(source="transformer.dt_id", read_only=True)
    feeder_id = serializers.CharField(source="feeder.feeder_id", read_only=True)

    class Meta:
        model = Incident
        fields = [
            "id", "status", "fault_type", "feeder_id", "transformer_id",
            "upstream_pole_id", "downstream_pole_id", "latitude", "longitude",
            "pincode", "affected_pole_count", "confidence", "confidence_reason",
            "assigned_crew", "detected_at", "repair_reported_at", "verified_at", "closed_at",
        ]


class AssignCrewSerializer(serializers.Serializer):
    crew_name = serializers.CharField(max_length=100)


class SimulatorFaultSerializer(serializers.Serializer):
    fault_type = serializers.ChoiceField(choices=["span", "transformer", "feeder"])
    downstream_pole_id = serializers.CharField(required=False)
    dt_id = serializers.CharField(required=False)
    feeder_id = serializers.CharField(required=False)

    def validate(self, attrs):
        required_field = {
            "span": "downstream_pole_id",
            "transformer": "dt_id",
            "feeder": "feeder_id",
        }[attrs["fault_type"]]
        if not attrs.get(required_field):
            raise serializers.ValidationError({required_field: "This field is required for the selected fault type."})
        return attrs
