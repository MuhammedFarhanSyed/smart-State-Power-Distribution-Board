from django.db import models


class Feeder(models.Model):
    """An 11 kV feeder that supplies one or more transformers."""

    feeder_id = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.feeder_id


class Transformer(models.Model):
    """A distribution transformer (DT) supplying a radial LT network."""

    dt_id = models.CharField(max_length=30, unique=True)
    feeder = models.ForeignKey(Feeder, on_delete=models.PROTECT, related_name="transformers")
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    households_served = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.dt_id


class Pole(models.Model):
    """A physical pole. `parent` is empty when the department lacks topology."""

    pole_id = models.CharField(max_length=30, unique=True)
    transformer = models.ForeignKey(Transformer, on_delete=models.PROTECT, related_name="poles")
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    pincode = models.CharField(max_length=10, blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    is_energized = models.BooleanField(null=True, default=None)
    last_state_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.pole_id


class Device(models.Model):
    """A telemetry device. A pole can have no device; device IDs can change over time."""

    device_id = models.CharField(max_length=60, unique=True)
    pole = models.ForeignKey(Pole, on_delete=models.PROTECT, related_name="devices")
    firmware = models.CharField(max_length=20, default="1.4.2")
    # -1 means this device has not sent an accepted message yet.
    last_seq = models.IntegerField(default=-1)
    is_online = models.BooleanField(default=True)

    def __str__(self):
        return self.device_id
