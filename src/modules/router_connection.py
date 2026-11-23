from abc import ABC, abstractmethod
import socket
import select
import struct

# This should probably be in a global config file, TODO LATER
MULTICAST_TTL = 2

class NetworkConnection(ABC):
    """Abstract superclass for connection objects for NetworkInterface.
    
    Provides methods for connecting the object to the underlying network
    and for polling for, reading, and sending messages.
    """
    def __init__(self):
        pass
    
    @abstractmethod
    def connect_network(self, if_address : tuple) -> bool:
        """Connect to the network on the given interface.
        
        The format of if_address depends on the underlying connection.
        Returns True if the connection was succesful, or False if the
        connection failed.
        """
    
    @abstractmethod
    def join_multicast(self, multicast_addr):
        """Join the given multicast group.
        
        The format of multicast_addr depends on the underlying connection.
        Raises an exception if any errors are encountered.
        """
    
    @abstractmethod
    def check_message(self) -> bool:
        """Checks the connection for pending messages.
        
        Returns True if there is a message that can be received using
        get_message(), or False if calling get_message() would block.
        """
    
    @abstractmethod
    def get_message(self) -> (tuple, bytes):
        """Read a message from the connection.
        
        Should only be called if check_message() indicates there is a message 
        waiting to be read. Will otherwise block until a message is received.
        
        Returns a tuple (sender_address, bytes), where the format
        of sender_address depends on the connection type. 
        """
    
    @abstractmethod
    def send_message(self, dest_address : tuple, message_bytes : bytes):
        """Sends a message consisting of given bytes to the given address.
        
        The format of if_address depends on the underlying connection.
        For IPv4 it is a tuple consisting of the destination address and port 
        number: (address, port). The address can be given as a string using
        dot notation, e.g. '192.168.1.99' (and can be a multicast address)
        """

class SocketConnection(NetworkConnection):
    _sock = None
    
    def __init__(self):
        super().__init__()
    
    def __del__(self):
        if self._sock is not None:
            self._sock.close()
    
    def dispose(self):
        """Disposes of this SocketConnection object.
        
        Intended for use in testing, this method closes the underlying socket
        object if one exists and then deletes the reference so that the
        destructor will not get confused and try to double-close it. 
        """
        if self._sock is not None:
            self._sock.close()
        self._sock = None
    
    def connect_network(self, if_address: tuple) -> bool:
        """Connect to the network on the given interface.
        
        The format of if_address depends on the underlying connection.
        For IPv4 it is a tuple consisting of the interface address and port 
        number: (address, port). The address can be given as a string using
        dot notation, e.g. '192.168.1.99' Returns True if the connection was
        succesful, or False if the connection failed.
        """
        # wrap connect_network_ex in a try-catch
        try:
            self.connect_network_ex(if_address)
        except Exception:
            return False
        return True
    
    def connect_network_ex(self, if_address: tuple) -> bool:
        """Connect to the network on the given interface, throwing an 
        exception from the underlying socket methods if they fail.
        
        Functions otherwise like connect_network().
        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(if_address)
        return True
    
    def join_multicast(self, multicast_addr):
        """Join the specified multicast group.
        
        For IPv4, multicast_addr should be a string representation of a 
        multicast group address using dot notation, e.g. '224.1.1.1'.
        A multicast group should only be joined after calling 
        connect_network(). 
        Raises an exception if the underlying socket has not been connected,
        or if there is an error joining the multicast group.
        """
        if self._sock is None:
            raise Exception(
                "Attempted to join multicast group without \
connecting first on SocketConnection.") # Throw some error
            return
        # Get the IP address this SocketConnection is bound to
        my_addr, my_port = self._sock.getsockname()
        # Turn the string dot notation addresses into a byte representation
        multi_addr_bytes = socket.inet.aton(multicast_addr)
        my_addr_bytes = socket.inet.aton(my_addr)
        # Pack the byte representation addresses into a struct, plus a 0 to 
        # indicate "any interface index".
        # See https://manpages.debian.org/trixie/manpages/ip.7.en.html#IP_ADD_MEMBERSHIP
        # for further information.
        opt_struct = struct.pack('=4s4sl', multi_addr_bytes, my_addr_bytes, 0)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, 
                              opt_struct)
        # We'll probably be sending to the multicast group, too, so we'll set
        # this socket's MULTICAST_TTL to limit how far our multicast messages
        # travel. 
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 
                              MULTICAST_TTL)
    
    def check_message(self) -> bool:
        """Checks the connection for pending messages.
        
        Returns True if there is a message that can be received using
        get_message(), or False if calling get_message() would block.
        Raises an exception if the underlying socket has not been connected.
        """
        if self._sock is None:
            raise Exception("Attempted to check message without connecting \
first on SocketConnection.") # Throw some error
            return
        # use select.select() to check if our sock is ready for reading
        # timeout value of 0 polls instead of blocking. 
        s_result = select.select([self._sock],[],[],0)
        if s_result is None or type(s_result) is not tuple:
            raise Exception(
                "Got a malformed result when using select on socket")
        # If the sock is ready for reading, it will be included
        # in the list that is the first member of the 3-tuple returned
        # by select.select()
        if len(s_result[0]) > 0:
            return True
        else:
            return False
    
    def get_message(self) -> (tuple, bytes):
        """Read a message from the connection.
        
        Should only be called if check_message() indicates there is a message 
        waiting to be read. Will otherwise block until a message is received.

        Returns a tuple (sender_address, bytes), where the format
        of sender_address depends on the connection type. 
        Raises an exception if the underlying socket has not been connected,
        or if there is an error in receiving the message.
        """
        if self._sock is None:
            raise Exception("Attempted to get message without connecting \
first on SocketConnection.") # Throw some error
            return
        # This is an ugly maximum size for a recv() call, but Python thankfully
        # will only allocate and return the amount of bytes that were actually 
        # present in the datagram, and not a bunch of 0's. I think. I hope.
        # Magic number pulled from Wikipedia: 
        # (65,535 bytes − 8-byte UDP header − 20-byte IP header).
        msg_tuple = self._sock.recvfrom(65507)
        if msg_tuple is None or type(msg_tuple) is not tuple:
            raise Exception(
                "Got a malformed result when using recvfrom on socket.")
        if len(msg_tuple[0]) == 0:
            raise Exception(
                "Calling recvfrom on socket read 0 bytes. Socket likely dead.")
        return msg_tuple

    
    def send_message(self, dest_address, bytes):
        """Sends a message consisting of given bytes to the given address.
        
        The format of if_address depends on the underlying connection.
        For IPv4 it is a tuple consisting of the destination address and port 
        number: (address, port). The address can be given as a string using
        dot notation, e.g. '192.168.1.99' (and can be a multicast address)
        Raises an exception if the underlying socket has not been connected.
        """
        #print("In socketconnection send_message sending to ",dest_address)
        if self._sock is None:
            raise Exception("Attempted to send message without connecting \
first on SocketConnection.") # Throw some error
            return
        self._sock.sendto(bytes, dest_address)
        pass
