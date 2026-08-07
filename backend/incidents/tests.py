from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from incidents.models import Incident, TelemetryEvent
from incidents.services.localization import detect_for_transformer
from incidents.services.simulator import inject_span_fault, inject_transformer_fault, repair_incident
from incidents.services.telemetry import ingest_telemetry
from network.models import Device, Feeder, Pole, Transformer


class LocalizationTestCase(TestCase):
    def setUp(self):
        self.feeder = Feeder.objects.create(feeder_id="F-TEST-01")
        self.dt = Transformer.objects.create(
            dt_id="D-TEST-01",
            feeder=self.feeder,
            lat=Decimal("12.960000"),
            lon=Decimal("77.580000"),
            households_served=150,
        )
        self.p1 = Pole.objects.create(
            pole_id="P-TEST-01",
            transformer=self.dt,
            parent=None,
            lat=Decimal("12.960100"),
            lon=Decimal("77.580100"),
            is_energized=True,
        )
        self.p2 = Pole.objects.create(
            pole_id="P-TEST-02",
            transformer=self.dt,
            parent=self.p1,
            lat=Decimal("12.960200"),
            lon=Decimal("77.580200"),
            is_energized=True,
        )
        self.dev1 = Device.objects.create(device_id="DEV-TEST-01", pole=self.p1)
        self.dev2 = Device.objects.create(device_id="DEV-TEST-02", pole=self.p2)

    def test_telemetry_ingestion_and_deduplication(self):
        res1 = ingest_telemetry({
            "device_id": "DEV-TEST-01",
            "pole_id": "P-TEST-01",
            "event": "heartbeat",
            "energized": True,
            "ts": timezone.now(),
            "seq": 1,
        })
        self.assertTrue(res1.accepted)

        # Duplicate sequence number should be rejected
        res2 = ingest_telemetry({
            "device_id": "DEV-TEST-01",
            "pole_id": "P-TEST-01",
            "event": "heartbeat",
            "energized": True,
            "ts": timezone.now(),
            "seq": 1,
        })
        self.assertFalse(res2.accepted)

    def test_span_fault_detection(self):
        result = inject_span_fault("P-TEST-02")
        self.assertEqual(result["affected_poles"], 1)

        incidents = Incident.objects.filter(status=Incident.Status.DETECTED)
        self.assertEqual(incidents.count(), 1)
        inc = incidents.first()
        self.assertEqual(inc.fault_type, Incident.FaultType.SPAN)
        self.assertEqual(inc.downstream_pole, self.p2)

    def test_transformer_fault_detection(self):
        result = inject_transformer_fault("D-TEST-01")
        self.assertEqual(result["affected_poles"], 2)

        incidents = Incident.objects.filter(status=Incident.Status.DETECTED)
        self.assertEqual(incidents.count(), 1)
        inc = incidents.first()
        self.assertEqual(inc.fault_type, Incident.FaultType.TRANSFORMER)

    def test_repair_and_auto_verification(self):
        inject_span_fault("P-TEST-02")
        inc = Incident.objects.get(downstream_pole=self.p2)

        # Mark repair reported
        inc.status = Incident.Status.REPAIR_REPORTED
        inc.save()

        # Simulate restoration telemetry
        repair_incident(inc.id)
        inc.refresh_from_db()
        self.assertEqual(inc.status, Incident.Status.CLOSED)
