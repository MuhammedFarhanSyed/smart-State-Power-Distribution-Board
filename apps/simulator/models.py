import uuid
from django.db import models
from apps.common.models import TimeStampedModel


class SimulationScenario(TimeStampedModel):
    """
    Preset or custom simulation scenario definitions (e.g., 'Monsoon Storm Multi-Break', 'FW 1.2 Quiet Outage').
    """
    scenario_id = models.CharField(
        max_length=64,
        primary_key=True,
        help_text="Unique scenario identifier."
    )
    name = models.CharField(
        max_length=128,
        help_text="Scenario name."
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="Description of scenario behavior."
    )
    config_json = models.JSONField(
        default=dict,
        help_text="Configuration parameters (noise levels, packet drop ratios, firmware mix)."
    )

    class Meta:
        db_table = 'simulator_scenario'
        verbose_name = 'Simulation Scenario'
        verbose_name_plural = 'Simulation Scenarios'
        ordering = ['scenario_id']

    def __str__(self) -> str:
        return f"Scenario {self.scenario_id} ({self.name})"


class ActiveSimulation(TimeStampedModel):
    """
    Tracks an active simulation session running against a specific DT or Feeder.
    """
    STATUS_RUNNING = 'running'
    STATUS_STOPPED = 'stopped'
    STATUS_RESET = 'reset'

    STATUS_CHOICES = [
        (STATUS_RUNNING, 'Running'),
        (STATUS_STOPPED, 'Stopped'),
        (STATUS_RESET, 'Reset'),
    ]

    session_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique session UUID."
    )
    dt_id = models.CharField(
        max_length=64,
        db_index=True,
        default='D-0112',
        help_text="Target Distribution Transformer under simulation."
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_STOPPED,
        help_text="Simulation status."
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Simulation start timestamp."
    )
    stopped_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Simulation stop timestamp."
    )

    class Meta:
        db_table = 'simulator_active_simulation'
        verbose_name = 'Active Simulation'
        verbose_name_plural = 'Active Simulations'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"SimulationSession {self.session_id} [DT: {self.dt_id}] Status: {self.status}"


class ActiveFault(TimeStampedModel):
    """
    Tracks active injected faults within the simulator workspace.
    """
    FAULT_SPAN = 'span'
    FAULT_TRANSFORMER = 'transformer'
    FAULT_FEEDER = 'feeder'

    FAULT_CHOICES = [
        (FAULT_SPAN, 'Span Break'),
        (FAULT_TRANSFORMER, 'Transformer Fault'),
        (FAULT_FEEDER, 'Feeder Fault'),
    ]

    fault_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique fault injection UUID."
    )
    fault_type = models.CharField(
        max_length=32,
        choices=FAULT_CHOICES,
        default=FAULT_SPAN,
        help_text="Type of fault injected."
    )
    target_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Target DT ID or Feeder ID."
    )
    from_pole_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Upstream pole ID of injected wire break."
    )
    to_pole_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Downstream pole ID of injected wire break."
    )
    is_repaired = models.BooleanField(
        default=False,
        help_text="True if repair telemetry has been generated and injected."
    )
    injected_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of fault injection."
    )
    repaired_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of fault repair telemetry injection."
    )

    class Meta:
        db_table = 'simulator_active_fault'
        verbose_name = 'Active Injected Fault'
        verbose_name_plural = 'Active Injected Faults'
        ordering = ['-injected_at']

    def __str__(self) -> str:
        return f"ActiveFault {self.fault_id} [{self.fault_type.upper()}] Target: {self.target_id} | Repaired: {self.is_repaired}"
