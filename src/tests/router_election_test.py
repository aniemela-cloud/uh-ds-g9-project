import unittest
from modules.router_interface import NetworkInterface
from modules.router_neighbor import Neighbor, NeighborState

THIS_ROUTER_ID = 1
THIS_ROUTER_ADDRESS = "192.168.0.1"
NEIGHBORS_A_ID = [2,3,4]
NEIGHBORS_A_ADDRESSES = ["192.168.0.2", "192.168.0.3", "192.168.0.4"]
NEIGHBORS_A_PRIORITIES = [2,3,4]
class TestElection_SubElections(unittest.TestCase):
    def setUp(self):
        self.interface = NetworkInterface(THIS_ROUTER_ID)
        self.thisRouter = \
        NetworkInterface._ElectionMember(
            router_id=THIS_ROUTER_ID,
            priority=1,
            ip_address=THIS_ROUTER_ADDRESS,
            designated_router="0.0.0.0",
            backup_router="0.0.0.0")
        self.election_list = [self.thisRouter]
        for i in range(len(NEIGHBORS_A_ID)):
            self.election_list.append(
                NetworkInterface._ElectionMember(
                    router_id=NEIGHBORS_A_ID[i],
                    priority=NEIGHBORS_A_PRIORITIES[i],
                    ip_address=NEIGHBORS_A_ADDRESSES[i],
                    designated_router="0.0.0.0",
                    backup_router="0.0.0.0")
            )

    def tearDown(self):
        pass
    
    def test_backup_election_none_declared(self):
        # Run backup election
        backup_result = self.interface._elect_backup(self.election_list)
        # Neighbors A has "192.168.0.4" with priority 4
        self.assertIsNotNone(backup_result,
                             "Backup election returned None when it shouldn't have")
        self.assertEqual(backup_result.ip_address, "192.168.0.4",
                          "Router with address 192.168.0.4 not selected as backup.")
        
    def test_backup_election_one_declared(self):
        self.election_list.append(
            NetworkInterface._ElectionMember(
                router_id=5,
                priority=1,
                ip_address="192.168.0.5",
                designated_router="0.0.0.0",
                backup_router="192.168.0.5"))
        backup_result = self.interface._elect_backup(self.election_list)
        self.assertIsNotNone(backup_result,
                             "Backup election returned None when it shouldn't have")
        self.assertEqual(backup_result.ip_address, "192.168.0.5",
                          "Router declaring itself as backup not elected as backup.")
        
    def test_backup_election_two_declared(self):
        self.election_list.append(
            NetworkInterface._ElectionMember(
                router_id=5,
                priority=1,
                ip_address="192.168.0.5",
                designated_router="0.0.0.0",
                backup_router="192.168.0.5"))
        self.election_list.append(
            NetworkInterface._ElectionMember(
                router_id=6,
                priority=10,
                ip_address="192.168.0.6",
                designated_router="0.0.0.0",
                backup_router="192.168.0.6"))

        backup_result = self.interface._elect_backup(self.election_list)
        self.assertIsNotNone(backup_result,
                             "Backup election returned None when it shouldn't have")
        self.assertEqual(backup_result.ip_address, "192.168.0.6",
                          "Router with highest priority declaring itself as backup not elected as backup.")
    
    def test_designated_election_none_declared(self):
        election_result = self.interface._elect_designated(self.election_list)
        self.assertIsNone(election_result,
                          "DR election elected a router even though none declared itself as DR")
    
    def test_designated_election_one_declared(self):
        self.election_list.append(
            NetworkInterface._ElectionMember(
                router_id=5,
                priority=1,
                ip_address="192.168.0.5",
                designated_router="192.168.0.5",
                backup_router="0.0.0.0"))
        election_result = self.interface._elect_designated(self.election_list)
        self.assertIsNotNone(election_result,
                             "Designated election returned None when it shouldn't have")
        self.assertEqual(election_result.ip_address, "192.168.0.5",
                          "Router declaring itself as DR not elected as DR.")
    
    def test_designated_election_two_declared(self):
        self.election_list.append(
            NetworkInterface._ElectionMember(
                router_id=5,
                priority=1,
                ip_address="192.168.0.5",
                designated_router="192.168.0.5",
                backup_router="0.0.0.0"))
        self.election_list.append(
            NetworkInterface._ElectionMember(
                router_id=6,
                priority=10,
                ip_address="192.168.0.6",
                designated_router="192.168.0.6",
                backup_router="0.0.0.0"))
        election_result = self.interface._elect_designated(self.election_list)
        self.assertIsNotNone(election_result,
                             "Designated election returned None when it shouldn't have")
        self.assertEqual(election_result.ip_address, "192.168.0.6",
                          "Router with highest priority declaring itself as DR not elected as DR.")
    
    def test_backup_high_priority_designated(self):
        self.election_list.append(
            NetworkInterface._ElectionMember(
                router_id=5,
                priority=100,
                ip_address="192.168.0.5",
                designated_router="192.168.0.5",
                backup_router="0.0.0.0"))
        backup_result = self.interface._elect_backup(self.election_list)
        self.assertIsNotNone(backup_result,
                             "Backup election returned None when it shouldn't have")
        self.assertNotEqual(backup_result.ip_address, "192.168.0.5",
                          "Router declaring itself as DR also elected as backup.")

class TestElection_FullElections(unittest.TestCase):
    def setUp(self):
        self.interface = NetworkInterface(THIS_ROUTER_ID)
        self.interface.set_address(THIS_ROUTER_ADDRESS,"255.255.255.0")
        self.interface.set_router_priority(1)
        for i in range(len(NEIGHBORS_A_ID)):
            neighbor = Neighbor(NEIGHBORS_A_ID[i])
            neighbor.set_address(NEIGHBORS_A_ADDRESSES[i])
            neighbor.set_priority(NEIGHBORS_A_PRIORITIES[i])
            neighbor.set_neighbor_state(NeighborState.TWO_WAY)
            # designated router and backup DR are left as "0.0.0.0"
            self.interface._neighbors.append(neighbor)

    def tearDown(self):
        pass
    
    def test_election_has_results(self):
        self.interface._run_election()
        self.assertNotEqual(self.interface.get_designated_router(), "0.0.0.0",
                         "Election failed to select DR")
        self.assertNotEqual(self.interface.get_backup_router(), "0.0.0.0",
                         "Election failed to select BDR")
     
    def test_this_router_elected_as_dr_but_not_bdr(self):
        self.interface.set_router_priority(10)
        self.interface._run_election()
        self.assertNotEqual(self.interface.get_designated_router(), "0.0.0.0",
                         "Election failed to select DR")
        self.assertNotEqual(self.interface.get_backup_router(), "0.0.0.0",
                         "Election failed to select BDR")
        