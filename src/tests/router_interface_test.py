import unittest
from unittest.mock import patch, MagicMock
from modules.router_interface import NetworkInterface, InterfaceState, InterfaceType

#Notice: Requires configuration test file config/config_test.ini


class TestRouterInterface(unittest.TestCase):
    def setUp(self):
        self.nw_if = NetworkInterface(10)

    def test_invalid_id(self):
        with self.assertRaises(ValueError):
            NetworkInterface("abc")

    def test_valid_new_interface(self):
        """Setting initial values"""
        self.nw_if.new_interface(1,4,"config_test.ini")
        self.assertEqual(InterfaceType.POINTTOPOINT, self.nw_if.get_interface_type())
        self.assertEqual(InterfaceState.DOWN, self.nw_if.get_interface_state())
        self.assertEqual(4, self.nw_if.get_ip_version())
        self.assertEqual("192.168.1.10", self.nw_if.get_address())
        self.assertEqual("255.255.255.0", self.nw_if.get_mask())
        self.assertEqual(11, self.nw_if.get_hello_interval())
        self.nw_if.set_router_dead_interval("200") #Integer conversion
        self.assertEqual(200, self.nw_if.get_router_dead_interval())
        self.assertEqual(8, self.nw_if.get_router_priority())
        self.assertEqual(2, self.nw_if.get_area_id())

    def test_valid_state(self):
            self.nw_if.set_interface_state(6)
            self.assertEqual(InterfaceState.DR, self.nw_if.get_interface_state())

    def test_invalid_state(self):
            self.assertFalse(self.nw_if.set_interface_state(-1))

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

    def test_invalid_hello_interval(self):
        self.nw_if.set_hello_interval(200) #Max limit 100
        self.assertEqual(10, self.nw_if.get_hello_interval()) #default 10

    def test_invalid_dead_interval(self):
        self.nw_if.set_router_dead_interval(2000) #Max limit 1000
        self.assertEqual(40, self.nw_if.get_router_dead_interval()) #default 40
        self.nw_if.set_router_dead_interval("a") #Integer conversion
        self.assertEqual(40, self.nw_if.get_router_dead_interval()) #default 40

    def test_invalid_router_priority(self):
        self.nw_if.set_router_priority(-2) #Min limit 1
        self.assertEqual(0, self.nw_if.get_router_priority()) #Default 0

    def test_invalid_area_id(self):
        self.nw_if.set_router_priority("a") #Integer
        self.assertEqual(0, self.nw_if.get_area_id()) #default 0


    @patch("modules.router_interface.threading.Thread")
    def test_interface_up_starts_thread(self, mock_thread):
        """Bringing the interface up starts the hello timer thread"""
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        self.nw_if._interface_up()
        mock_thread_instance.start.assert_called_once()

    def test_valid_designated_router(self):
        self.nw_if.set_designated_router("10.0.0.3")
        self.assertEqual("10.0.0.3", self.nw_if.get_designated_router())

    def test_ivalid_designated_router(self):
        self.assertFalse(self.nw_if.set_designated_router("3"))
        self.assertFalse(self.nw_if.set_designated_router("naapuri"))

    def test_valid_backup_router(self):
        self.nw_if.set_backup_router("10.0.0.4")
        self.assertEqual("10.0.0.4", self.nw_if.get_backup_router())

    def test_ivalid_backup_router(self):
        self.assertFalse(self.nw_if.set_backup_router("4"))
        self.assertFalse(self.nw_if.set_backup_router("vara"))
