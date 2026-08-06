from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [("network", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="ScheduledOutage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.CharField(max_length=50, unique=True)),
                ("scope", models.CharField(choices=[("feeder", "Feeder"), ("transformer", "Transformer")], max_length=20)),
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField()),
                ("reason", models.CharField(max_length=255)),
                ("feeder", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="network.feeder")),
                ("transformer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="network.transformer")),
            ],
        ),
        migrations.CreateModel(
            name="TelemetryEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event", models.CharField(choices=[("heartbeat", "Heartbeat"), ("power_lost", "Power lost"), ("power_restored", "Power restored"), ("boot", "Boot")], max_length=20)),
                ("energized", models.BooleanField()),
                ("device_timestamp", models.DateTimeField()),
                ("seq", models.PositiveIntegerField()),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("battery_mv", models.PositiveIntegerField(blank=True, null=True)),
                ("rssi", models.IntegerField(blank=True, null=True)),
                ("firmware", models.CharField(blank=True, max_length=20)),
                ("device", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="network.device")),
                ("pole", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="network.pole")),
            ],
        ),
        migrations.CreateModel(
            name="Incident",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("detected", "Detected"), ("acknowledged", "Acknowledged"), ("crew_assigned", "Crew assigned"), ("repair_reported", "Repair reported"), ("verified", "Verified"), ("closed", "Closed")], default="detected", max_length=30)),
                ("fault_type", models.CharField(choices=[("span", "Span"), ("transformer", "Transformer"), ("feeder", "Feeder"), ("topology_unknown", "Topology unknown")], max_length=30)),
                ("latitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("longitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("pincode", models.CharField(blank=True, max_length=10)),
                ("affected_pole_count", models.PositiveIntegerField(default=0)),
                ("confidence", models.CharField(choices=[("high", "High"), ("medium", "Medium"), ("low", "Low")], max_length=10)),
                ("confidence_reason", models.TextField()),
                ("assigned_crew", models.CharField(blank=True, max_length=100)),
                ("detected_at", models.DateTimeField(auto_now_add=True)),
                ("repair_reported_at", models.DateTimeField(blank=True, null=True)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("downstream_pole", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="downstream_incidents", to="network.pole")),
                ("feeder", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="network.feeder")),
                ("transformer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="network.transformer")),
                ("upstream_pole", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="upstream_incidents", to="network.pole")),
            ],
        ),
        migrations.CreateModel(
            name="IncidentPole",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("incident", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="affected_poles", to="incidents.incident")),
                ("pole", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="network.pole")),
            ],
        ),
        migrations.AddIndex(model_name="telemetryevent", index=models.Index(fields=["pole", "received_at"], name="telemetry_pole_received_idx")),
        migrations.AddConstraint(model_name="incidentpole", constraint=models.UniqueConstraint(fields=("incident", "pole"), name="unique_incident_pole")),
    ]
