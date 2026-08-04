from django.db import models
from apps.common.models import TimeStampedModel


class Substation(TimeStampedModel):
    """
    Represents a 66/11 kV Substation.
    Top-level origin node for electrical distribution feeders.
    """
    substation_id = models.CharField(
        max_length=64,
        primary_key=True,
        help_text="Unique identifier for the substation (e.g., KSPDB-SS-01)."
    )
    name = models.CharField(
        max_length=128,
        help_text="Human-readable name of the substation."
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="GPS Latitude coordinate."
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="GPS Longitude coordinate."
    )

    class Meta:
        db_table = 'network_substation'
        verbose_name = 'Substation'
        verbose_name_plural = 'Substations'
        ordering = ['substation_id']

    def __str__(self) -> str:
        return f"{self.substation_id} - {self.name}"


class Feeder(TimeStampedModel):
    """
    Represents an 11 kV Feeder line originating from a Substation.
    """
    feeder_id = models.CharField(
        max_length=64,
        primary_key=True,
        help_text="Unique identifier for the feeder (e.g., F-07-03)."
    )
    substation = models.ForeignKey(
        Substation,
        on_delete=models.CASCADE,
        related_name='feeders',
        help_text="Parent substation supplying this feeder."
    )
    name = models.CharField(
        max_length=128,
        blank=True,
        default='',
        help_text="Optional descriptive name for the feeder."
    )

    class Meta:
        db_table = 'network_feeder'
        verbose_name = 'Feeder'
        verbose_name_plural = 'Feeders'
        ordering = ['feeder_id']

    def __str__(self) -> str:
        return f"Feeder {self.feeder_id} (Substation: {self.substation_id})"


class DistributionTransformer(TimeStampedModel):
    """
    Represents a Distribution Transformer (DT) converting 11 kV to 400/230V.
    Supplies low-tension (LT) radial lines of poles.
    """
    dt_id = models.CharField(
        max_length=64,
        primary_key=True,
        help_text="Unique identifier for the DT (e.g., D-0112)."
    )
    feeder = models.ForeignKey(
        Feeder,
        on_delete=models.CASCADE,
        related_name='transformers',
        help_text="Parent 11kV feeder supplying this distribution transformer."
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="GPS Latitude coordinate (~4m accuracy)."
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="GPS Longitude coordinate (~4m accuracy)."
    )
    capacity_kva = models.IntegerField(
        default=250,
        help_text="Transformer rated capacity in kVA."
    )
    households_served = models.IntegerField(
        default=300,
        help_text="Estimated number of households connected under this DT."
    )

    class Meta:
        db_table = 'network_distribution_transformer'
        verbose_name = 'Distribution Transformer'
        verbose_name_plural = 'Distribution Transformers'
        ordering = ['dt_id']

    def __str__(self) -> str:
        return f"DT {self.dt_id} (Feeder: {self.feeder_id})"


class Pole(TimeStampedModel):
    """
    Represents an LT Distribution Pole in the physical grid.
    Poles form a strict radial tree topology under their parent DT.
    """
    pole_id = models.CharField(
        max_length=64,
        primary_key=True,
        help_text="Unique identifier for the pole (e.g., P-024431)."
    )
    feeder = models.ForeignKey(
        Feeder,
        on_delete=models.CASCADE,
        related_name='poles',
        help_text="Parent 11kV feeder."
    )
    dt = models.ForeignKey(
        DistributionTransformer,
        on_delete=models.CASCADE,
        related_name='poles',
        help_text="Parent Distribution Transformer supplying power."
    )
    seq_on_line = models.IntegerField(
        null=True,
        blank=True,
        help_text="Position along LT line from transformer (1 = closest). Missing for ~60% of poles."
    )
    parent_pole = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        help_text="Upstream parent pole on the radial line. Missing for ~60% of poles."
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Surveyed GPS Latitude coordinate (accurate to ~4m)."
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Surveyed GPS Longitude coordinate (accurate to ~4m)."
    )
    pole_type = models.CharField(
        max_length=64,
        default='LT-9m-PCC',
        help_text="Physical pole material & height specification (e.g., LT-9m-PCC, LT-8m-Steel)."
    )
    ward = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Administrative ward subdivision."
    )
    pincode = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        db_index=True,
        help_text="Postal PIN code. Missing for ~3% of poles."
    )
    device_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        db_index=True,
        help_text="Stable device identifier of IoT hardware fitted on this pole (~91% fitted)."
    )

    class Meta:
        db_table = 'network_pole'
        verbose_name = 'Pole'
        verbose_name_plural = 'Poles'
        ordering = ['dt_id', 'seq_on_line', 'pole_id']
        indexes = [
            models.Index(fields=['dt', 'seq_on_line'], name='idx_pole_dt_seq'),
            models.Index(fields=['device_id'], name='idx_pole_device'),
            models.Index(fields=['parent_pole'], name='idx_pole_parent'),
        ]

    def __str__(self) -> str:
        return f"Pole {self.pole_id} (DT: {self.dt_id}, Device: {self.device_id or 'None'})"
