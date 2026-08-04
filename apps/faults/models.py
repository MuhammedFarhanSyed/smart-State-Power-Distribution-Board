import uuid
from django.db import models
from apps.common.models import TimeStampedModel


class ScheduledOutage(TimeStampedModel):
    """
    Represents planned maintenance / load-shedding shutdowns published by the department feed.
    Used by NoiseFilter to suppress false alarm tickets.
    """
    SCOPE_FEEDER = 'feeder'
    SCOPE_DT = 'dt'

    SCOPE_CHOICES = [
        (SCOPE_FEEDER, '11kV Feeder'),
        (SCOPE_DT, 'Distribution Transformer'),
    ]

    outage_id = models.CharField(
        max_length=64,
        primary_key=True,
        help_text="Unique scheduled outage ID (e.g., SO-2026-07-29-014)."
    )
    scope = models.CharField(
        max_length=32,
        choices=SCOPE_CHOICES,
        help_text="Scope of shutdown: 'feeder' or 'dt'."
    )
    target_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Target Feeder ID (e.g., F-07-03) or DT ID (e.g., D-0112)."
    )
    start_time = models.DateTimeField(
        help_text="Planned shutdown start timestamp."
    )
    end_time = models.DateTimeField(
        help_text="Planned shutdown end timestamp (Note: shutdowns overrun by 20-40 min routinely)."
    )
    reason = models.CharField(
        max_length=256,
        default="Planned maintenance",
        help_text="Reason for load shedding / shutdown."
    )

    class Meta:
        db_table = 'faults_scheduled_outage'
        verbose_name = 'Scheduled Outage'
        verbose_name_plural = 'Scheduled Outages'
        ordering = ['-start_time']

    def __str__(self) -> str:
        return f"ScheduledOutage {self.outage_id} [{self.scope}:{self.target_id}] ({self.start_time} - {self.end_time})"


class FaultIncident(TimeStampedModel):
    """
    Represents a single localized physical grid fault incident ticket.
    Exactly 1 ticket per physical fault (grouped across all downstream dark poles).
    """
    ASSET_SPAN = 'span'
    ASSET_DT = 'dt'
    ASSET_FEEDER = 'feeder'

    ASSET_CHOICES = [
        (ASSET_SPAN, 'Wire Span Break'),
        (ASSET_DT, 'Distribution Transformer / Fuse'),
        (ASSET_FEEDER, '11kV Feeder Trip'),
    ]

    STATUS_DETECTED = 'detected'
    STATUS_ACKNOWLEDGED = 'acknowledged'
    STATUS_CREW_ASSIGNED = 'crew_assigned'
    STATUS_RESOLVED = 'resolved'
    STATUS_VERIFIED_CLOSED = 'verified_closed'

    STATUS_CHOICES = [
        (STATUS_DETECTED, 'Detected'),
        (STATUS_ACKNOWLEDGED, 'Acknowledged'),
        (STATUS_CREW_ASSIGNED, 'Crew Assigned'),
        (STATUS_RESOLVED, 'Resolved (Pending Telemetry Verification)'),
        (STATUS_VERIFIED_CLOSED, 'Verified Closed'),
    ]

    ticket_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique UUID for the incident ticket."
    )
    asset_type = models.CharField(
        max_length=32,
        choices=ASSET_CHOICES,
        default=ASSET_SPAN,
        help_text="Type of failed asset: span, dt, or feeder."
    )
    feeder_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="11kV Feeder ID."
    )
    dt_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Distribution Transformer ID."
    )
    from_pole_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="Upstream live pole ID of the fault boundary span."
    )
    to_pole_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="Downstream dark pole ID of the fault boundary span."
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Navigation GPS Latitude for dispatch."
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Navigation GPS Longitude for dispatch."
    )
    pincode = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        db_index=True,
        help_text="Postal PIN code of fault location."
    )
    affected_poles_count = models.IntegerField(
        default=1,
        help_text="Total count of downstream dark poles grouped under this single incident."
    )
    confidence_score = models.FloatField(
        default=1.0,
        help_text="Diagnostic confidence score between 0.0 and 1.0."
    )
    confidence_reasons = models.JSONField(
        default=list,
        help_text="JSON list of human-readable diagnostic reasons explaining the confidence score."
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_DETECTED,
        db_index=True,
        help_text="Ticket lifecycle status."
    )
    detected_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when the fault boundary was localized."
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when telemetry verified full power restoration."
    )

    class Meta:
        db_table = 'faults_incident'
        verbose_name = 'Fault Incident Ticket'
        verbose_name_plural = 'Fault Incident Tickets'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['dt_id', 'status'], name='idx_fault_dt_status'),
            models.Index(fields=['from_pole_id', 'to_pole_id'], name='idx_fault_span'),
        ]

    def __str__(self) -> str:
        return f"Ticket {self.ticket_id} [{self.asset_type.upper()}] DT: {self.dt_id} | Span: {self.from_pole_id}->{self.to_pole_id} | Status: {self.status}"


class AffectedPole(TimeStampedModel):
    """
    Maps all downstream dark poles associated with a single FaultIncident ticket.
    """
    incident = models.ForeignKey(
        FaultIncident,
        on_delete=models.CASCADE,
        related_name='affected_poles',
        help_text="Parent fault incident ticket."
    )
    pole_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Pole ID affected by the upstream fault."
    )
    is_boundary = models.BooleanField(
        default=False,
        help_text="True if this pole is the first dark pole at the live/dark boundary."
    )

    class Meta:
        db_table = 'faults_affected_pole'
        verbose_name = 'Affected Pole'
        verbose_name_plural = 'Affected Poles'
        ordering = ['incident', 'pole_id']

    def __str__(self) -> str:
        return f"AffectedPole {self.pole_id} (Incident: {self.incident_id}, Boundary: {self.is_boundary})"
