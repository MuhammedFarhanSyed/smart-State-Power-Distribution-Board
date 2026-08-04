from django.urls import path
from apps.simulator.views import (
    LoadNetworkView,
    StartSimulationView,
    StopSimulationView,
    ResetSimulationView,
    InjectSpanFaultView,
    InjectTransformerFaultView,
    InjectFeederFaultView,
    RepairFaultView,
    SimulatorStatusView
)

app_name = 'simulator'

urlpatterns = [
    path('simulator/load-network', LoadNetworkView.as_view(), name='load-network'),
    path('simulator/start', StartSimulationView.as_view(), name='start'),
    path('simulator/stop', StopSimulationView.as_view(), name='stop'),
    path('simulator/reset', ResetSimulationView.as_view(), name='reset'),
    path('simulator/fault/span', InjectSpanFaultView.as_view(), name='fault-span'),
    path('simulator/fault/transformer', InjectTransformerFaultView.as_view(), name='fault-transformer'),
    path('simulator/fault/feeder', InjectFeederFaultView.as_view(), name='fault-feeder'),
    path('simulator/repair/<str:fault_id>', RepairFaultView.as_view(), name='repair-fault'),
    path('simulator/status', SimulatorStatusView.as_view(), name='status'),
]
