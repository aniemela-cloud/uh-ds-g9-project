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
        self.assertEqual(11, message.hello_interval)
        self.assertEqual(8, message.router_priority)
        self.assertEqual(41, message.router_dead_interval)
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
            self.interface, "get_neighbors", return_value=["2.2.2.2", "3.3.3.3"]
        ):
            message = HelloMessage.from_interface(self.interface, "1.1.1.1")

        self.assertEqual(["2.2.2.2", "3.3.3.3"], message.neighbors)