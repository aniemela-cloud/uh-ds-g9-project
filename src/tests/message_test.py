import unittest

from modules.message import HelloMessage
from modules.router_interface import NetworkInterface


class TestHelloMessage(unittest.TestCase):
    def setUp(self):
        self.interface = NetworkInterface(10)
        self.interface.new_interface(1, 4, "config_test.ini")

    def test_from_interface_copies_expected_values(self):
        message = HelloMessage.from_interface(
            self.interface,
            router_id="1.1.1.1",
        )

        self.assertEqual("1.1.1.1", message.router_id)
        self.assertEqual(2, message.area_id)
        self.assertEqual("255.255.255.0", message.network_mask)
        self.assertEqual(2, message.hello_interval)
        self.assertEqual(8, message.router_priority)
        self.assertEqual(4, message.router_dead_interval)
        self.assertEqual("0.0.0.0", message.designated_router)
        self.assertEqual("0.0.0.0", message.backup_designated_router)
        self.assertEqual([], message.neighbors)
        self.assertEqual(2, message.version)
        self.assertEqual(1, message.message_type)

    def test_from_interface_copies_dr_and_bdr(self):
        self.interface.set_designated_router("192.168.1.1")
        self.interface.set_backup_router("192.168.1.2")

        message = HelloMessage.from_interface(self.interface, "1.1.1.1")

        self.assertEqual("192.168.1.1", message.designated_router)
        self.assertEqual("192.168.1.2", message.backup_designated_router)

    def test_from_interface_copies_neighbor_ids(self):
        from unittest.mock import patch

        with patch.object(
            self.interface, "get_neighbor_ids", return_value=["2.2.2.2", "3.3.3.3"]
        ):
            message = HelloMessage.from_interface(self.interface, "1.1.1.1")

        self.assertEqual(["2.2.2.2", "3.3.3.3"], message.neighbors)


class TestHelloEncoding(unittest.TestCase):
    def test_round_trip_with_neighbors(self):
        message = HelloMessage(
            router_id="1.1.1.1",
            area_id=2,
            network_mask="255.255.255.0",
            hello_interval=11,
            router_priority=8,
            router_dead_interval=41,
            neighbors=["2.2.2.2", "3.3.3.3"],
        )

        packet = message.to_bytes()

        self.assertEqual(len(packet), 52)
        self.assertEqual(HelloMessage.from_bytes(packet), message)