from abc import ABC, abstractmethod
import socket
import select

class NetworkConnection(ABC):
    def __init__(self):
        pass
    
    # The if_address is defined in the configuration or possibly
    # automatically figured out. In any case, the NetworkInterface object
    # needs to know it's own (IP) address, and it uses it here.
    # The if_port is defined in the configuration, and needs to be the same
    # for all the nodes running in this network
    @abstractmethod
    def connect_network(self, if_address, if_port):
        """Connect to the network on the given interface using the given port."""
    
    # For checking whether there is a message waiting to be read
    # from the underlying technology (e.g. the socket). Non-blocking.
    @abstractmethod
    def check_message(self) -> bool:
        """Checks the connection for pending messages"""
    
    # Reads a message/datagram from the socket. Should only be called
    # if check_message() indicates there is a message waiting to be read.
    # Will otherwise block until a message is received.
    @abstractmethod
    def get_message(self) -> (tuple, bytes):
        """Read message"""
    
    # Send a message to dest_address consisting of bytes. The dest_address
    # data type depends on the underlying network (check comments for the
    # actual implementing subclass for more details)
    @abstractmethod
    def send_message(self, dest_address, bytes):
        """Sends message"""

class SocketConnection(NetworkConnection):
    _sock = None
    
    def __init__(self):
        super().__init__()
    
    def connect_network(self, if_address, if_port):
        # wrap in a try-catch
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # wrap in a try-catch
        self._socket.bind((if_address, if_port))
        
        pass
    
    def check_message(self) -> bool:
        if self._sock is None:
            # Throw some error
            return
        # use select.select() to check if our sock is ready for reading
        # timeout value of 0 polls instead of blocking. 
        s_result = select.select([self._sock],[],[],0)
        if s_result is None or type(s_result) is not tuple:
            # We got a bad result! Probably need to throw an error
            return False
        # If the sock is ready for reading, it will be included
        # in the list that is the first member of the 3-tuple returned
        # by select.select()
        if len(s_result[0] > 0):
            return True
        else:
            return False
    
    def get_message(self) -> (tuple, bytes):
        if self._sock is None:
            # Throw some error
            return
        #msg_tuple = self._sock.recvfrom()
    
    def send_message(self, dest_address, bytes):
        if self._sock is None:
            # Throw some error
            return
        self._sock.sendto(bytes, dest_address)
        pass
