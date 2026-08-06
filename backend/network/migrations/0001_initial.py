from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Feeder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("feeder_id", models.CharField(max_length=30, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Transformer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("dt_id", models.CharField(max_length=30, unique=True)),
                ("lat", models.DecimalField(decimal_places=6, max_digits=9)),
                ("lon", models.DecimalField(decimal_places=6, max_digits=9)),
                ("households_served", models.PositiveIntegerField(default=0)),
                ("feeder", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transformers", to="network.feeder")),
            ],
        ),
        migrations.CreateModel(
            name="Pole",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pole_id", models.CharField(max_length=30, unique=True)),
                ("lat", models.DecimalField(decimal_places=6, max_digits=9)),
                ("lon", models.DecimalField(decimal_places=6, max_digits=9)),
                ("pincode", models.CharField(blank=True, max_length=10)),
                ("is_energized", models.BooleanField(default=None, null=True)),
                ("last_state_at", models.DateTimeField(blank=True, null=True)),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="children", to="network.pole")),
                ("transformer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="poles", to="network.transformer")),
            ],
        ),
        migrations.CreateModel(
            name="Device",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("device_id", models.CharField(max_length=60, unique=True)),
                ("firmware", models.CharField(default="1.4.2", max_length=20)),
                ("last_seq", models.IntegerField(default=-1)),
                ("is_online", models.BooleanField(default=True)),
                ("pole", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="devices", to="network.pole")),
            ],
        ),
    ]
