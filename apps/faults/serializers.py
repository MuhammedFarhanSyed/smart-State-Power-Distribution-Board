from rest_framework import serializers
from apps.faults.models import FaultIncident, AffectedPole, IncidentTimeline


class AffectedPoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffectedPole
        fields = ['pole_id', 'is_boundary']


class IncidentTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentTimeline
        fields = ['from_status', 'to_status', 'changed_by', 'notes', 'timestamp']


class FaultIncidentSerializer(serializers.ModelSerializer):
    affected_poles = AffectedPoleSerializer(many=True, read_only=True)
    timeline = IncidentTimelineSerializer(many=True, read_only=True)

    class Meta:
        model = FaultIncident
        fields = [
            'ticket_id',
            'asset_type',
            'feeder_id',
            'dt_id',
            'from_pole_id',
            'to_pole_id',
            'latitude',
            'longitude',
            'pincode',
            'affected_poles_count',
            'confidence_score',
            'confidence_reasons',
            'assigned_crew',
            'status',
            'detected_at',
            'resolved_at',
            'closed_at',
            'affected_poles',
            'timeline'
        ]


class AssignCrewSerializer(serializers.Serializer):
    crew_name = serializers.CharField(max_length=128, required=True)
    notes = serializers.CharField(max_length=256, required=False, allow_blank=True, default='')


class ResolveIncidentSerializer(serializers.Serializer):
    notes = serializers.CharField(max_length=256, required=False, allow_blank=True, default='')
