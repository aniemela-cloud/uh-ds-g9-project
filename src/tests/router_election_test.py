import unittest
from modules.router_interface import NetworkInterface
from modules.router_neighbor import Neighbor

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
            THIS_ROUTER_ID,
            1,
            THIS_ROUTER_ADDRESS,
            "0.0.0.0",
            "0.0.0.0")
        self.election_list = [self.thisRouter]
        for i in range(len(NEIGHBORS_A_ID)):
            self.election_list.append(
                NetworkInterface._ElectionMember(
                    NEIGHBORS_A_ID[i],
                    NEIGHBORS_A_PRIORITIES[i],
                    NEIGHBORS_A_ADDRESSES[i],
                    "0.0.0.0",
                    "0.0.0.0")
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
                5,
                1,
                "192.168.0.5",
                "0.0.0.0",
                "192.168.0.5"))
        backup_result = self.interface._elect_backup(self.election_list)
        self.assertIsNotNone(backup_result,
                             "Backup election returned None when it shouldn't have")
        self.assertEqual(backup_result.ip_address, "192.168.0.5",
                          "Router declaring itself as backup not elected as backup.")
        
    def test_backup_election_two_declared(self):
        pass