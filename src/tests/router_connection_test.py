import unittest
from modules.router_connection import SocketConnection

LOOPBACK_ADDRESS = '127.0.0.1'
INVALID_IP_ADDRESS = '999.99.9.1'
CONNECTION_A_PORT = 12987
CONNECTION_B_PORT = 12876
TEST_MESSAGE_A = b'Hello'

class TesRouterSocketConnection_BeforeConnection(unittest.TestCase):
    def setUp(self):
        self.routerconnection = SocketConnection()
    
    def tearDown(self):
        ### Have the routerconnection close the socket, freeing up the
        ### port if one has been reserved by connecting it to the network.
        self.routerconnection.dispose()
    
    # test that connecting to the network using a valid address works
    def test_valid_address(self):
        success = self.routerconnection.connect_network(
            (LOOPBACK_ADDRESS,CONNECTION_A_PORT))
        self.assertTrue(success)
    
    # test that connecting to the network using an invalid address fails
    def test_invalid_address(self):
        success = self.routerconnection.connect_network(
            (INVALID_IP_ADDRESS,CONNECTION_A_PORT))
        self.assertFalse(success)
    
    # test that using check_message without connecting fails
    @unittest.expectedFailure
    def test_unconnected_check(self):
        success = self.routerconnection.check_message()
        self.assertTrue(success)
    
    # test that using get_message without connecting fails
    @unittest.expectedFailure
    def test_unconnected_read(self):
        message = self.routerconnection.get_message()
        self.assertIsInstance(message,tuple)
    
    # test that using send_message without connecting fails
    @unittest.expectedFailure
    def test_unconnected_send(self):
        self.routerconnection.send_message(
            (LOOPBACK_ADDRESS,CONNECTION_B_PORT),b'Hello World')

# Tests for a Socket Connection 
class TesRouterSocketConnection_AfterConnection(unittest.TestCase):
    def setUp(self):
        self.routerconnection = SocketConnection()
        self.routerconnection.connect_network(('127.0.0.1',12987))
    
    def tearDown(self):
        # Have the routerconnection close the socket, freeing up the
        # port if one has been reserved by connecting it to the network.
        self.routerconnection.dispose()
    
    # test that calling check_message after connecting gives a result
    def test_connected_check(self):
        check_result = self.routerconnection.check_message()
        self.assertIsInstance(check_result,bool)
    
    # test that calling send_message after connecting does not fail
    def test_connected_send(self):
        self.routerconnection.send_message(
            (LOOPBACK_ADDRESS,CONNECTION_B_PORT),b'Hello World')
        # No assertion since send_message() does not return a value, only
        # raises an exception on an error state

# Bi-directional communication tests, requiring two socket connection objects
class TesRouterSocketConnection_Bidirectional(unittest.TestCase):
    def setUp(self):
        self.routerconnection_a = SocketConnection()
        self.routerconnection_b = SocketConnection()
        self.routerconnection_a.connect_network(
            (LOOPBACK_ADDRESS,CONNECTION_A_PORT))
        self.routerconnection_b.connect_network(
            (LOOPBACK_ADDRESS,CONNECTION_B_PORT))
    
    def tearDown(self):
        self.routerconnection_a.dispose()
        self.routerconnection_b.dispose()
    
    def test_message_received(self):
        self.routerconnection_a.send_message(
            (LOOPBACK_ADDRESS,CONNECTION_B_PORT), TEST_MESSAGE_A)
        b_sees_message = self.routerconnection_b.check_message()
        self.assertTrue(b_sees_message)
        message = self.routerconnection_b.get_message()
        self.assertIsInstance(message, tuple)
        message_bytes, sendaddress = message
        self.assertEqual(sendaddress, (LOOPBACK_ADDRESS, CONNECTION_A_PORT),
                          "Sender address vs routerconnection_a mismatch")
        self.assertEqual(message_bytes, TEST_MESSAGE_A,
                          "Message received does not match message sent")