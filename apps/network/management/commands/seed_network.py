import random
from django.core.management.base import BaseCommand
from apps.network.models import Substation, Feeder, DistributionTransformer, Pole, Span
from apps.telemetry.models import Device


class Command(BaseCommand):
    help = 'Seeds synthetic electrical network asset database matching Karnataka ESCOM specs.'

    def add_arguments(self, parser):
        parser.add_argument('--poles', type=int, default=3000, help='Total number of poles to generate.')

    def handle(self, *args, **options):
        total_poles_target = options['poles']
        self.stdout.write(self.style.SUCCESS(f"Starting seed process for ~{total_poles_target} poles..."))

        # 1. Create 4 Substations
        substation_data = [
            ("KSPDB-SS-01", "Koramangala 66/11kV Substation", 12.9352, 77.6245),
            ("KSPDB-SS-02", "Indiranagar 66/11kV Substation", 12.9784, 77.6408),
            ("KSPDB-SS-03", "Jayanagar 66/11kV Substation", 12.9250, 77.5938),
            ("KSPDB-SS-04", "HSR Layout 66/11kV Substation", 12.9121, 77.6445),
        ]

        substations = []
        for s_id, s_name, s_lat, s_lon in substation_data:
            sub, _ = Substation.objects.get_or_create(
                substation_id=s_id,
                defaults={'name': s_name, 'latitude': s_lat, 'longitude': s_lon}
            )
            substations.append(sub)

        self.stdout.write(f"Seeded {len(substations)} Substations.")

        # 2. Create 31 Feeders
        feeders = []
        feeder_idx = 1
        for sub in substations:
            # ~8 feeders per substation
            for f in range(1, 8 if feeder_idx <= 24 else 8):
                if feeder_idx > 31:
                    break
                f_id = f"F-{feeder_idx:02d}-03"
                f_name = f"11kV Feeder {feeder_idx} ({sub.name.split()[0]})"
                feeder, _ = Feeder.objects.get_or_create(
                    feeder_id=f_id,
                    defaults={'substation': sub, 'name': f_name}
                )
                feeders.append(feeder)
                feeder_idx += 1

        self.stdout.write(f"Seeded {len(feeders)} Feeders.")

        # 3. Create 412 Distribution Transformers (DTs)
        dt_list = []
        dt_idx = 1
        for feeder in feeders:
            # ~13 DTs per feeder to reach 412
            dts_for_feeder = 13 if dt_idx <= 400 else 12
            for d in range(dts_for_feeder):
                if dt_idx > 412:
                    break
                dt_id = f"D-{dt_idx:04d}"
                # Base GPS around feeder's substation with small offset
                base_lat = float(feeder.substation.latitude) + (random.uniform(-0.015, 0.015))
                base_lon = float(feeder.substation.longitude) + (random.uniform(-0.015, 0.015))

                dt, _ = DistributionTransformer.objects.get_or_create(
                    dt_id=dt_id,
                    defaults={
                        'feeder': feeder,
                        'latitude': base_lat,
                        'longitude': base_lon,
                        'capacity_kva': random.choice([100, 250, 500]),
                        'households_served': random.randint(150, 450)
                    }
                )
                dt_list.append(dt)
                dt_idx += 1

        self.stdout.write(f"Seeded {len(dt_list)} Distribution Transformers.")

        # 4. Create Poles & Devices (Target ~3000 poles for seeded subset)
        poles_per_dt = max(7, total_poles_target // len(dt_list))
        pole_count = 0
        device_count = 0

        # We will make D-0112 a fully sequenced reference DT for testing
        reference_dt = DistributionTransformer.objects.filter(dt_id='D-0112').first() or dt_list[0]

        for dt in dt_list:
            is_sequenced = (dt.dt_id == reference_dt.dt_id or random.random() > 0.60) # ~40% sequenced, ~60% unsequenced
            cur_lat = float(dt.latitude)
            cur_lon = float(dt.longitude)

            prev_pole = None
            for p_idx in range(1, poles_per_dt + 1):
                pole_id = f"P-{pole_count + 24431:06d}"

                # Offset coordinates along line
                cur_lat += random.uniform(0.00015, 0.00035)
                cur_lon += random.uniform(0.00015, 0.00035)

                # ~91% fitted with devices
                has_device = (random.random() <= 0.91)
                dev_id = f"KSPDB-SD07-{dt.dt_id}-{pole_count + 4431}" if has_device else None

                # ~8% FW 1.2, rest 1.4
                fw_version = '1.2' if (has_device and random.random() <= 0.08) else '1.4'

                # ~3% missing pincodes
                pincode = "560078" if random.random() > 0.03 else None

                # Sequence & parent pointers
                seq_val = p_idx if is_sequenced else None
                parent_val = prev_pole if is_sequenced else None

                pole, _ = Pole.objects.get_or_create(
                    pole_id=pole_id,
                    defaults={
                        'feeder': dt.feeder,
                        'dt': dt,
                        'seq_on_line': seq_val,
                        'parent_pole': parent_val,
                        'latitude': cur_lat,
                        'longitude': cur_lon,
                        'pole_type': random.choice(['LT-9m-PCC', 'LT-8m-Steel']),
                        'ward': 'W-084',
                        'pincode': pincode,
                        'device_id': dev_id
                    }
                )

                if dev_id:
                    Device.objects.get_or_create(
                        device_id=dev_id,
                        defaults={
                            'current_pole_id': pole_id,
                            'firmware_version': fw_version,
                            'is_active': True
                        }
                    )
                    device_count += 1

                # If parent exists, create physical Span
                if parent_val:
                    span_id = f"SPAN-{parent_val.pole_id}-{pole.pole_id}"
                    Span.objects.get_or_create(
                        span_id=span_id,
                        defaults={
                            'from_pole': parent_val,
                            'to_pole': pole,
                            'dt': dt,
                            'feeder': dt.feeder,
                            'length_meters': random.uniform(35.0, 55.0)
                        }
                    )

                prev_pole = pole
                pole_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded grid network database:\n"
                f" - {len(substations)} Substations\n"
                f" - {len(feeders)} Feeders\n"
                f" - {len(dt_list)} Distribution Transformers\n"
                f" - {pole_count} Poles (~60% unsequenced, ~40% sequenced)\n"
                f" - {device_count} IoT Telemetry Devices (~91% fitted, ~8% FW 1.2)"
            )
        )
