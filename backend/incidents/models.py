from django.db import models

from network.models import Feeder, Pole, Transformer


class ScheduledOutage(models.Model):
    """A planned feeder or transformer shutdown from the department's outage feed."""

    class Scope(models.TextChoices):
        FEEDER = "feeder", "Feeder"
        TRANSFORMER = "transformer", "Transformer"

    external_id = models.CharField(max_length=50, unique=True)
    scope = models.CharField(max_length=20, choices=Scope.choices)
    feeder = models.ForeignKey(Feeder, null=True, blank=True, on_delete=models.PROTECT)
    transformer = models.ForeignKey(Transformer, null=True, blank=True, on_delete=models.PROTECT)
    start = models.DateTimeField()
    end = models.DateTimeField()
    reason = models.CharField(max_length=255)


class TelemetryEvent(models.Model):
    """An immutable copy of telemetry accepted by the ingest endpoint."""

    class EventType(models.TextChoices):
        HEARTBEAT = "heartbeat", "Heartbeat"
        POWER_LOST = "power_lost", "Power lost"
        POWER_RESTORED = "power_restored", "Power restored"
        BOOT = "boot", "Boot"

    device = models.ForeignKey("network.Device", on_delete=models.PROTECT)
    pole = models.ForeignKey(Pole, on_delete=models.PROTECT)
    event = models.CharField(max_length=20, choices=EventType.choices)
    energized = models.BooleanField()
    device_timestamp = models.DateTimeField()
    seq = models.PositiveIntegerField()
    received_at = models.DateTimeField(auto_now_add=True)
    battery_mv = models.PositiveIntegerField(null=True, blank=True)
    rssi = models.IntegerField(null=True, blank=True)
    firmware = models.CharField(max_length=20, blank=True)

    class Meta:
        indexes = [models.Index(fields=["pole", "received_at"])]


class Incident(models.Model):
    """One grouped outage ticket, never one record per dark pole."""

    class Status(models.TextChoices):
        DETECTED = "detected", "Detected"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        CREW_ASSIGNED = "crew_assigned", "Crew assigned"
        REPAIR_REPORTED = "repair_reported", "Repair reported"
        VERIFIED = "verified", "Verified"
        CLOSED = "closed", "Closed"

    class FaultType(models.TextChoices):
        SPAN = "span", "Span"
        TRANSFORMER = "transformer", "Transformer"
        FEEDER = "feeder", "Feeder"
        TOPOLOGY_UNKNOWN = "topology_unknown", "Topology unknown"

    class Confidence(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DETECTED)
    fault_type = models.CharField(max_length=30, choices=FaultType.choices)
    feeder = models.ForeignKey(Feeder, null=True, blank=True, on_delete=models.PROTECT)
    transformer = models.ForeignKey(Transformer, null=True, blank=True, on_delete=models.PROTECT)
    upstream_pole = models.ForeignKey(Pole, null=True, blank=True, on_delete=models.PROTECT, related_name="upstream_incidents")
    downstream_pole = models.ForeignKey(Pole, null=True, blank=True, on_delete=models.PROTECT, related_name="downstream_incidents")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    pincode = models.CharField(max_length=10, blank=True)
    affected_pole_count = models.PositiveIntegerField(default=0)
    confidence = models.CharField(max_length=10, choices=Confidence.choices)
    confidence_reason = models.TextField()
    assigned_crew = models.CharField(max_length=100, blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    repair_reported_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)


class IncidentPole(models.Model):
    """The poles believed to be affected by one incident."""

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="affected_poles")
    pole = models.ForeignKey(Pole, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["incident", "pole"], name="unique_incident_pole")
        ]
