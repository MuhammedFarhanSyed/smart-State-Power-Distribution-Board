import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from network.models import Device, Feeder, Pole, Transformer


class Command(BaseCommand):
    help = "Seed a small, realistic synthetic power network when the database is empty."

    def handle(self, *args, **options):
        if Pole.objects.exists():
            self.stdout.write("Network already exists; skipping seed.")
            return

        random.seed(42)
        feeders = [Feeder.objects.create(feeder_id=f"F-07-{number:02d}") for number in range(1, 4)]

        pole_number = 1
        for dt_number in range(1, 16):
            feeder = feeders[(dt_number - 1) % len(feeders)]
            base_lat = Decimal("12.960000") + Decimal(dt_number) * Decimal("0.002000")
            base_lon = Decimal("77.580000") + Decimal(dt_number) * Decimal("0.001500")
            transformer = Transformer.objects.create(
                dt_id=f"D-{dt_number:04d}",
                feeder=feeder,
                lat=base_lat,
                lon=base_lon,
                households_served=random.randint(120, 350),
            )

            # The first six DTs have digitized parent links; the remaining nine do not.
            topology_known = dt_number <= 6
            created_poles = []
            for position in range(1, 81):
                parent = None
                if topology_known and position > 1:
                    # Every tenth pole starts a short branch; otherwise continue the main run.
                    parent_index = position - 10 if position % 10 == 0 else position - 2
                    parent = created_poles[parent_index]

                pole = Pole.objects.create(
                    pole_id=f"P-{pole_number:06d}",
                    transformer=transformer,
                    parent=parent,
                    lat=base_lat + Decimal(position) * Decimal("0.000035"),
                    lon=base_lon + Decimal(position) * Decimal("0.000020"),
                    pincode="" if random.random() < 0.03 else "560078",
                    is_energized=True,
                )
                created_poles.append(pole)
                pole_number += 1

                # About 9% of poles deliberately have no telemetry device.
                if random.random() >= 0.09:
                    Device.objects.create(
                        device_id=f"KSPDB-SD07-{transformer.dt_id}-{position:04d}",
                        pole=pole,
                        firmware="1.2.9" if random.random() < 0.08 else "1.4.2",
                    )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Feeder.objects.count()} feeders, {Transformer.objects.count()} transformers, "
            f"{Pole.objects.count()} poles, and {Device.objects.count()} devices."
        ))
