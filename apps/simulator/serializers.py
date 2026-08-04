from rest_framework import serializers


class InjectSpanFaultSerializer(serializers.Serializer):
    dt_id = serializers.CharField(max_length=64, default='D-0112')
    from_pole_id = serializers.CharField(max_length=64, required=True)
    to_pole_id = serializers.CharField(max_length=64, required=True)
    apply_noise = serializers.BooleanField(default=True)


class InjectTransformerFaultSerializer(serializers.Serializer):
    dt_id = serializers.CharField(max_length=64, required=True)
    apply_noise = serializers.BooleanField(default=True)


class InjectFeederFaultSerializer(serializers.Serializer):
    feeder_id = serializers.CharField(max_length=64, required=True)
    dt_ids = serializers.ListField(child=serializers.CharField(max_length=64), required=True)
    apply_noise = serializers.BooleanField(default=True)


class LoadNetworkSerializer(serializers.Serializer):
    dt_id = serializers.CharField(max_length=64, default='D-0112')


class StartSimulationSerializer(serializers.Serializer):
    dt_id = serializers.CharField(max_length=64, default='D-0112')
