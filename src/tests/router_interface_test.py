import unittest
from unittest.mock import MagicMock
from modules.router_interface import NetworkInterface, InterfaceState, InterfaceType

#Notice: Requires configuration test file config/config_test.ini


class TestRouterInterface(unittest.TestCase):
    def setUp(self):
        self.nw_if = NetworkInterface(10)

    def test_valid_new_interface(self):
        """Setting initial values"""
        self.nw_if.new_interface(1,4,"config_test.ini")
        self.assertEqual(InterfaceType.POINTTOPOINT, self.nw_if.get_interface_type())
        self.assertEqual(InterfaceState.DOWN, self.nw_if.get_interface_state())
        self.assertEqual(4, self.nw_if.get_ip_version())
        self.assertEqual("192.168.1.10", self.nw_if.get_address())
        self.assertEqual("255.255.255.0", self.nw_if.get_mask())
        self.assertEqual(11, self.nw_if.get_hello_interval())
        self.assertEqual(41, self.nw_if.get_router_dead_interval())
        self.assertEqual(8, self.nw_if.get_router_priority())
        self.assertEqual(2, self.nw_if.get_area_id())

    def test_valid_set_address(self):
        """Testing IP address change"""
        self.nw_if.set_address("10.0.0.2", "255.0.0.0/20")
        self.assertEqual("10.0.0.2", self.nw_if.get_address())
        self.assertEqual("255.0.0.0/20", self.nw_if.get_mask())

    def test_invalid_set_address(self):
        """Invalid IP address falls back to default values"""
        self.nw_if.set_address("10.0.1", "255.0.0.0/13")
        self.assertEqual("0.0.0.0", self.nw_if.get_address())
        self.assertEqual("0.0.0.0", self.nw_if.get_mask())


    def test_interface_up_starts_thread(self):
        """Bringing the interface up starts the hello timer thread"""
        self.nw_if._hello_thread.start = MagicMock()
        self.nw_if._interface_up()
        self.nw_if._hello_thread.start.assert_called_once()
