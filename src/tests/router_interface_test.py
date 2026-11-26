import unittest
from unittest.mock import patch, MagicMock
from modules.router_interface import NetworkInterface, InterfaceState, InterfaceType
from modules.message import HelloMessage
from modules.router_neighbor import Neighbor, NeighborState

#Notice: Requires configuration test file config/config_test.ini


class TestRouterInterface(unittest.TestCase):
    def setUp(self):
        self.nw_if = NetworkInterface(10)
        
        self.msg_ok = HelloMessage(
        router_id=1,
        area_id=2,
        network_mask="255.255.255.0",
        hello_interval=2,
        router_priority=2,
        router_dead_interval=4
        )


    def test_invalid_id(self):
        with self.assertRaises(ValueError):
            NetworkInterface("abc")

    def test_valid_new_interface(self):
        """Setting initial values"""
        self.nw_if.new_interface(1,4,"config_test.ini", start_interface=False)
        self.assertEqual(InterfaceType.POINTTOPOINT, self.nw_if.get_interface_type())
        self.assertEqual(InterfaceState.DOWN, self.nw_if.get_interface_state())
        self.assertEqual(4, self.nw_if.get_ip_version())
        self.assertEqual("192.168.1.10", self.nw_if.get_address())
        self.assertEqual("255.255.255.0", self.nw_if.get_mask())
        self.assertEqual(65435, self.nw_if.get_port())
        self.assertEqual("192.168.1.12", self.nw_if.get_destination_ip())
        self.assertEqual(2, self.nw_if.get_hello_interval())
        self.nw_if.set_router_dead_interval("5") #Integer conversion
        self.assertEqual(5, self.nw_if.get_router_dead_interval())
        self.assertEqual(8, self.nw_if.get_router_priority())
        self.assertEqual(2, self.nw_if.get_area_id())

    def test_valid_state(self):
            self.nw_if.set_interface_state(InterfaceState.DR)
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

    # def test_match_config_condition(self):
    #     self.nw_if.new_interface(1,4,"config_test.ini", start_interface=False)

    #     msg_diff_values = HelloMessage(
    #     router_id="192.168.1.12",
    #     area_id=2,
    #     network_mask="255.255.255.0",
    #     hello_interval=2,
    #     router_priority=2,
    #     router_dead_interval=499
    #     )

    #     self.assertTrue(self.nw_if._match_config_condition(self.msg_ok))
    #     self.assertFalse(self.nw_if._match_config_condition(msg_diff_values))


    def test_dr_backup_seen_condition(self):
        msg_dr = HelloMessage(
        router_id="192.168.1.12",
        area_id=2,
        network_mask="255.255.255.0",
        hello_interval=2,
        router_priority=2,
        router_dead_interval=4,
        designated_router= "192.168.1.12",
        backup_designated_router= "0.0.0.0"
        )
        self.nw_if.set_interface_state(InterfaceState.WAITING)
        self.assertTrue(self.nw_if._backup_seen_condition(msg_dr))

    def test_bdr_backup_seen_condition(self):
        msg_bdr = HelloMessage(
        router_id="192.168.1.12",
        area_id=2,
        network_mask="255.255.255.0",
        hello_interval=2,
        router_priority=2,
        router_dead_interval=4,
        designated_router= "0.0.0.0",
        backup_designated_router= "192.168.1.12"
        )
        self.nw_if.set_interface_state(InterfaceState.WAITING)
        self.assertTrue(self.nw_if._backup_seen_condition(msg_bdr))

    def test_bdr_backup_seen_not_waiting_condition(self):
        msg_bdr = HelloMessage(
        router_id="192.168.1.12",
        area_id=2,
        network_mask="255.255.255.0",
        hello_interval=2,
        router_priority=2,
        router_dead_interval=4,
        designated_router= "0.0.0.0",
        backup_designated_router= "192.168.1.12"
        )
        self.nw_if.set_interface_state(InterfaceState.LOOPBACK)
        self.assertFalse(self.nw_if._backup_seen_condition(msg_bdr))

    def test_new_neighbor_condition(self):
        #TODO fix message ip and id 

        nb = Neighbor(1)
        self.nw_if._neighbors.append(nb)
        self.assertTrue(self.nw_if._new_neighbor_condition(self.msg_ok))

    def test_not_new_neighbor_condition(self):
        #TODO fix message ip and id 
        nb = Neighbor(12)
        self.nw_if._neighbors.append(nb)
        self.assertFalse(self.nw_if._new_neighbor_condition(self.msg_ok))

    def test_empty_new_neighbor_condition(self):
        #TODO fix message ip and id 
        self.assertFalse(self.nw_if._new_neighbor_condition(self.msg_ok))


    def test_ok_twoway_condition(self):
        #TODO fix message ip and id 
        msg_nb = HelloMessage(
        router_id="192.168.1.12",
        area_id=2,
        network_mask="255.255.255.0",
        hello_interval=2,
        router_priority=2,
        router_dead_interval=4,
        neighbors= [2,3,10]
        )
        self.assertTrue(self.nw_if._twoway_condition(msg_nb))

    def test_nok_twoway_condition(self):
        #TODO fix message ip and id 
        msg_nb = HelloMessage(
        router_id="192.168.1.12",
        area_id=2,
        network_mask="255.255.255.0",
        hello_interval=2,
        router_priority=2,
        router_dead_interval=4,
        neighbors= [1,2,3]
        )
        self.assertFalse(self.nw_if._twoway_condition(msg_nb))

    def test_priority_same_condition(self):
        nb = Neighbor(1)
        self.nw_if._neighbors.append(nb)
        nb.set_priority(2)
        self.assertTrue(self.nw_if._priority_same_condition(self.msg_ok))

    # def test_leaders_same_condition(self):
    #     #TODO fix ips and ids
    #     msg_dr = HelloMessage(
    #     router_id=5,
    #     area_id=2,
    #     network_mask="255.255.255.0",
    #     hello_interval=2,
    #     router_priority=2,
    #     router_dead_interval=4,
    #     designated_router= "192.168.1.33",
    #     backup_designated_router= "192.168.1.11"
    #     )
    #     self.nw_if.set_designated_router("192.168.1.33")
    #     self.nw_if.set_backup_router("192.168.1.11")
    #     nb = Neighbor(5)
    #     nb.set_designated_router="192.168.1.33"
    #     nb.set_backup_router="192.168.1.11"
    #     self.nw_if._neighbors.append(nb)

    #     self.assertTrue(self.nw_if._leaders_same_condition(msg_dr))

    def test_conflict_condition(self):
        #TODO fix ips and ids
        msg_dr = HelloMessage(
        router_id=5,
        area_id=2,
        network_mask="255.255.255.0",
        hello_interval=2,
        router_priority=2,
        router_dead_interval=4,
        designated_router= "192.168.1.33",
        backup_designated_router= "192.168.1.11"
        )
        self.nw_if.set_designated_router("192.168.1.33")
        self.nw_if.set_backup_router("192.168.1.11")
        self.assertTrue(self.nw_if._conflict_condition(msg_dr))


    def test_handle_received_message(self):
        #TODO fix message ip and id 
        #Conditions and events are mainly tested elsewhere

        #New neighbor noticed and created
        self.nw_if.set_address("192.168.0.1", "255.255.255.0")
        self.nw_if.set_hello_interval(2)
        self.nw_if.set_router_priority(2)
        self.nw_if.set_router_dead_interval(4)
        self.nw_if._handle_received_message(self.msg_ok)
        self.assertIn(1, self.nw_if.get_neighbor_ids())

    def test_handle_backup_seen(self):
        pass

    def test_handle_twoway(self):
        pass

    def test_handle_neighbor_change(self):
        pass

    def test_handle_neighbor_dead(self):
        pass

