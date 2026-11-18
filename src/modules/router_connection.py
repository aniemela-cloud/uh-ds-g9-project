from abc import ABC, abstractmethod
import socket
import select

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
        For IPv4 it is a tuple consisting of the interface address and port 
        number: (address, port). The address can be given as a string using
        dot notation, e.g. '192.168.1.99' 
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
        
        Returns a tuple (sender_address: tuple, bytes), where the format
        of sender_address depends on the connection type. 
        """
    
    @abstractmethod
    def send_message(self, dest_address : tuple, message_bytes : bytes):
    # Send a message to dest_address consisting of bytes. The dest_address
    # data type depends on the underlying network (check comments for the
    # actual implementing subclass for more details)
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
    
    def connect_network(self, if_address, if_port):
        # wrap in a try-catch
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except Exception:
            return False
        # wrap in a try-catch
        try:
            self._sock.bind((if_address, if_port))
        except Exception:
            return False
        return True
    
    def check_message(self) -> bool:
        if self._sock is None:
            raise Exception("Attempted to check message without connecting first on SocketConnection") # Throw some error
            return
        # use select.select() to check if our sock is ready for reading
        # timeout value of 0 polls instead of blocking. 
        s_result = select.select([self._sock],[],[],0)
        if s_result is None or type(s_result) is not tuple:
            raise Exception("Got a malformed result when using select on socket")
        # If the sock is ready for reading, it will be included
        # in the list that is the first member of the 3-tuple returned
        # by select.select()
        if len(s_result[0] > 0):
            return True
        else:
            return False
    
    def get_message(self) -> (tuple, bytes):
        if self._sock is None:
            raise Exception("Attempted to get message without connecting first on SocketConnection") # Throw some error
            return
        #msg_tuple = self._sock.recvfrom()
    
    def send_message(self, dest_address, bytes):
        if self._sock is None:
            raise Exception("Attempted to send message without connecting first on SocketConnection") # Throw some error
            return
        self._sock.sendto(bytes, dest_address)
        pass
