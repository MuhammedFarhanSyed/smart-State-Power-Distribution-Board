from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.simulator.models import ActiveSimulation, ActiveFault
from apps.simulator.serializers import (
    InjectSpanFaultSerializer,
    InjectTransformerFaultSerializer,
    InjectFeederFaultSerializer,
    LoadNetworkSerializer,
    StartSimulationSerializer
)
from apps.simulator.services.network_simulator import NetworkSimulator
from apps.simulator.services.fault_injector import FaultInjector
from apps.simulator.services.repair_service import RepairService


class LoadNetworkView(APIView):
    """POST /api/simulator/load-network"""
    def post(self, request, *args, **kwargs):
        serializer = LoadNetworkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dt_id = serializer.validated_data.get('dt_id', 'D-0112')

        tree = NetworkSimulator.load_network_tree(dt_id)
        pole_count = len(tree.nodes) if tree else 0

        return Response({
            "message": f"Network tree for DT '{dt_id}' loaded successfully.",
            "dt_id": dt_id,
            "total_poles": pole_count
        }, status=status.HTTP_200_OK)


class StartSimulationView(APIView):
    """POST /api/simulator/start"""
    def post(self, request, *args, **kwargs):
        serializer = StartSimulationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dt_id = serializer.validated_data.get('dt_id', 'D-0112')

        sim, _ = ActiveSimulation.objects.get_or_create(dt_id=dt_id)
        sim.status = ActiveSimulation.STATUS_RUNNING
        sim.started_at = timezone.now()
        sim.save()

        return Response({
            "message": "Simulation started.",
            "session_id": str(sim.session_id),
            "dt_id": dt_id,
            "status": sim.status
        }, status=status.HTTP_200_OK)


class StopSimulationView(APIView):
    """POST /api/simulator/stop"""
    def post(self, request, *args, **kwargs):
        sim = ActiveSimulation.objects.filter(status=ActiveSimulation.STATUS_RUNNING).first()
        if sim:
            sim.status = ActiveSimulation.STATUS_STOPPED
            sim.stopped_at = timezone.now()
            sim.save()

        return Response({"message": "Simulation stopped."}, status=status.HTTP_200_OK)


class ResetSimulationView(APIView):
    """POST /api/simulator/reset"""
    def post(self, request, *args, **kwargs):
        ActiveSimulation.objects.all().update(status=ActiveSimulation.STATUS_RESET)
        ActiveFault.objects.all().update(is_repaired=True)
        NetworkSimulator.reset_network('D-0112')

        return Response({"message": "Simulator workspace reset."}, status=status.HTTP_200_OK)


class InjectSpanFaultView(APIView):
    """POST /api/simulator/fault/span"""
    def post(self, request, *args, **kwargs):
        serializer = InjectSpanFaultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dt_id = serializer.validated_data.get('dt_id', 'D-0112')
        from_pole_id = serializer.validated_data['from_pole_id']
        to_pole_id = serializer.validated_data['to_pole_id']
        apply_noise = serializer.validated_data.get('apply_noise', True)

        fault = FaultInjector.inject_span_fault(
            dt_id=dt_id,
            from_pole_id=from_pole_id,
            to_pole_id=to_pole_id,
            apply_noise=apply_noise
        )

        return Response({
            "message": f"Span fault injected between {from_pole_id} -> {to_pole_id}",
            "fault_id": str(fault.fault_id),
            "target_dt": dt_id
        }, status=status.HTTP_201_CREATED)


class InjectTransformerFaultView(APIView):
    """POST /api/simulator/fault/transformer"""
    def post(self, request, *args, **kwargs):
        serializer = InjectTransformerFaultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dt_id = serializer.validated_data['dt_id']
        apply_noise = serializer.validated_data.get('apply_noise', True)

        fault = FaultInjector.inject_transformer_fault(dt_id=dt_id, apply_noise=apply_noise)

        return Response({
            "message": f"Transformer fault injected for DT '{dt_id}'",
            "fault_id": str(fault.fault_id)
        }, status=status.HTTP_201_CREATED)


class InjectFeederFaultView(APIView):
    """POST /api/simulator/fault/feeder"""
    def post(self, request, *args, **kwargs):
        serializer = InjectFeederFaultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        feeder_id = serializer.validated_data['feeder_id']
        dt_ids = serializer.validated_data['dt_ids']
        apply_noise = serializer.validated_data.get('apply_noise', True)

        fault = FaultInjector.inject_feeder_fault(feeder_id=feeder_id, dt_ids=dt_ids, apply_noise=apply_noise)

        return Response({
            "message": f"Feeder fault injected for Feeder '{feeder_id}'",
            "fault_id": str(fault.fault_id)
        }, status=status.HTTP_201_CREATED)


class RepairFaultView(APIView):
    """POST /api/simulator/repair/{fault_id}"""
    def post(self, request, fault_id, *args, **kwargs):
        success = RepairService.repair_fault(fault_id)
        if not success:
            return Response({"error": f"Fault '{fault_id}' not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "message": f"Fault '{fault_id}' repaired. Restoration telemetry injected.",
            "fault_id": fault_id,
            "is_repaired": True
        }, status=status.HTTP_200_OK)


class SimulatorStatusView(APIView):
    """GET /api/simulator/status"""
    def get(self, request, *args, **kwargs):
        sim = ActiveSimulation.objects.first()
        active_faults = ActiveFault.objects.filter(is_repaired=False)

        return Response({
            "simulation_status": sim.status if sim else "idle",
            "active_faults_count": active_faults.count(),
            "active_faults": [
                {
                    "fault_id": str(f.fault_id),
                    "fault_type": f.fault_type,
                    "target_id": f.target_id,
                    "span": f"{f.from_pole_id} -> {f.to_pole_id}" if f.from_pole_id else None,
                    "injected_at": f.injected_at.isoformat()
                }
                for f in active_faults
            ]
        }, status=status.HTTP_200_OK)
