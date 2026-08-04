import unittest
from datetime import datetime, timezone
from apps.simulator.services.noise_generator import NoiseGenerator


class PureTelemetryGenerator:
    _sequence_counters = {}

    @classmethod
    def get_next_sequence(cls, device_id: str, is_boot: bool = False) -> int:
        if is_boot:
            cls._sequence_counters[device_id] = 0
            return 0
        current = cls._sequence_counters.get(device_id, 100) + 1
        cls._sequence_counters[device_id] = current
        return current

    @classmethod
    def build_payload(cls, device_id: str, pole_id: str, event: str, energized: bool, firmware: str = '1.4', custom_seq: int = None):
        seq = custom_seq if custom_seq is not None else cls.get_next_sequence(device_id, is_boot=(event == 'boot'))
        return {
            "device_id": device_id,
            "pole_id": pole_id,
            "event": event,
            "energized": energized,
            "ts": datetime.now(timezone.utc).isoformat(),
            "seq": seq,
            "battery_mv": 3480 if energized else 2900,
            "rssi": -91,
            "fw": firmware
        }


class TestSimulatorEngine(unittest.TestCase):
    """
    Unit test suite for the Simulator Engine and Noise Generator.
    """

    def test_noise_generator_rules(self):
        """Tests that NoiseGenerator enforces packet drop and sequence manipulation rules."""
        # FW 1.2 quiet fleet mode drops 100% of power_lost packets
        self.assertTrue(NoiseGenerator.should_drop_dying_packet('power_lost', firmware='1.2'))

        # Heartbeat packets are never dropped regardless of FW
        self.assertFalse(NoiseGenerator.should_drop_dying_packet('heartbeat', firmware='1.2'))
        self.assertFalse(NoiseGenerator.should_drop_dying_packet('heartbeat', firmware='1.4'))

    def test_duplicate_and_out_of_order_payloads(self):
        """Tests duplicate and out-of-order sequence packet generation."""
        original = PureTelemetryGenerator.build_payload('DEV-P1', 'P1', 'power_lost', False, custom_seq=100)

        dup = NoiseGenerator.generate_duplicate_payload(original)
        self.assertEqual(dup['seq'], 100)
        self.assertEqual(dup['device_id'], 'DEV-P1')

        stale = NoiseGenerator.generate_out_of_order_payload(original)
        self.assertLess(stale['seq'], 100)

    def test_sequence_counter_boot_reset(self):
        """Tests that sequence numbers reset to 0 on 'boot' event."""
        seq1 = PureTelemetryGenerator.get_next_sequence('DEV-TEST-01')
        self.assertGreaterEqual(seq1, 100)

        boot_seq = PureTelemetryGenerator.get_next_sequence('DEV-TEST-01', is_boot=True)
        self.assertEqual(boot_seq, 0)

        next_seq = PureTelemetryGenerator.get_next_sequence('DEV-TEST-01')
        self.assertEqual(next_seq, 1)


if __name__ == '__main__':
    unittest.main()
