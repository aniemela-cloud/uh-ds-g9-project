import unittest
from modules.router_neighbor import Neighbor, NeighborState


class TestNeighbor(unittest.TestCase):
    def setUp(self):
        self.nb = Neighbor(2) #Id is integer

    def test_invalid_id(self):
        """Id is not integer"""
        with self.assertRaises(ValueError):
            Neighbor("abc")

    def test_valid_new_neighbor(self):
        """Setting initial values: IP address, others remain default"""
        self.nb.new_neighbor("10.0.10.2")
        self.assertEqual(NeighborState.INIT, self.nb.get_neighbor_state())
        self.assertEqual("10.0.10.2", self.nb.get_address())
        self.assertEqual(0, self.nb.get_priority())
        self.assertEqual(2, self.nb.get_neighbor_id())

    def test_valid_state(self):
            self.nb.set_neighbor_state(NeighborState.LOADING)
            self.assertEqual(NeighborState.LOADING, self.nb.get_neighbor_state())

    def test_invalid_state(self):
            self.assertFalse(self.nb.set_neighbor_state(-1))
