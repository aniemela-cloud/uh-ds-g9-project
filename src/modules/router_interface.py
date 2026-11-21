from enum import Enum
from pathlib import Path
import configparser
import threading
from modules.message import HelloMessage
import ipaddress
from modules.periodic_timer import PeriodicTimer
from modules.router_neighbor import Neighbor, NeighborState

debug = 0 #Set to 1 for debugging / Add one neighbor at start

class InterfaceType(Enum):
    POINTTOPOINT = 1
    BROADCAST = 2 #default
    NBMA = 3
    POINTTOMULTIPOINT = 4
    VIRTUAL = 5

class InterfaceState(Enum):
    DOWN = 0 #default
    LOOPBACK = 1
    POINTTOPOINT = 2
    WAITING = 3
    DROTHER = 4
    BACKUP = 5
    DR = 6

def is_valid_ip(ip):
    """Validates that IPv4 or IPv6 address is right format"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def is_valid_network(network):
    """Validates that IPv4 or IPv6 network mask address is right format"""
    try:
        ipaddress.ip_network(network)
        return True
    except ValueError:
        return False

class NetworkInterface:
    def __init__(self, given_id):
        try:
            self.id = int(given_id)
        except ValueError:
            raise ValueError("ID must be an integer")
        self._interface_type = InterfaceType.BROADCAST
        self._interface_state = InterfaceState.DOWN
        self._ip_version = 4
        self._ip_address = "0.0.0.0"
        self._ip_mask = "0.0.0.0"
        self._area_id = 0
        self._hello_interval = 10
        self._router_dead_interval = 40
        self._router_priority = 0

        #Timers are set at method _interface_up()
        self._hello_timer = None
        self._hello_thread = None
        #self._wait_timer = None
        self._wait_thread = None

        self._designated_router = "0.0.0.0"        #IPAddress NOT READY
        self._backup_designated_router = "0.0.0.0" #IPAddress NOT READY

        self.next_neighbor_id = 1
        self._neighbors = [] #List of neighbor instances NOT READY

    def new_interface(self, interface_type, ip_version, config_file, start_interface=False):
        """Method reads configuration data from given file and 
        checks all data is found before updating values. 
        If data is incorrect falls back to default values."""

        #Setting type and IP version
        try:
            self._interface_type = InterfaceType(interface_type)
        except ValueError:
            raise ValueError(f"Invalid interface type [{interface_type}]")
        if ip_version not in (4, 6):
            raise ValueError(f"Invalid IP version [{ip_version}]")
        self._ip_version = ip_version

        #Reading values from config file
        config = configparser.ConfigParser()
        config_file = Path(__file__).parent.parent / "config" / config_file
        if not config.read(config_file):
            raise FileNotFoundError(f"Config file not found: {config_file}")

        required = [("network", "ip_address"), ("network", "ip_mask"), ("network", "area_id"),
        ("interval", "hello"), ("interval", "dead"), ("router", "priority")]

        for section, key in required:
            if section not in config:
                raise ValueError(f"Missing section [{section}]")
            if key not in config[section]:
                raise ValueError(f"Missing key '{key}' in section [{section}]")

        #Setting values from config file
        try:
            self.set_address(config.get("network", "ip_address", fallback="0.0.0.0"),
                                config.get("network", "ip_mask", fallback="0.0.0.0"))
        except ValueError:
            self.set_address("0.0.0.0", "0.0.0.0")
        try:
            self.set_area_id(config.getint("network", "area_id", fallback="0"))
        except ValueError:
            self.set_area_id("0")
        try:
            self.set_hello_interval(config.getint("interval", "hello", fallback="10"))
        except ValueError:
            self.set_hello_interval("10")
        try:
            self.set_router_dead_interval(config.getint("interval", "dead", fallback="40"))
        except ValueError:
            self.set_router_dead_interval("40")
        try:
            self.set_router_priority(config.getint("router", "priority", fallback="0"))
        except ValueError:
            self.set_router_priority("0")

        if start_interface:
            self._interface_up()


    def get_id(self):
        return self.id

    def get_interface_type(self):
        return self._interface_type

    def set_interface_state(self, state):
        """Switches state, state is given as integer"""
        try:
            self._interface_state = InterfaceState(state)
        except ValueError:
            return False

    def get_interface_state(self):
        return self._interface_state

    def set_address(self, ip_address, ip_mask):
        """Set IP address and mask"""
        if( (is_valid_ip(ip_address)) & (is_valid_network(ip_mask)) ):
            self._ip_address = ip_address
            self._ip_mask = ip_mask
        return False

    def get_ip_version(self):
        return self._ip_version

    def get_address(self):
        return self._ip_address

    def get_mask(self):
        return self._ip_mask

    def set_area_id(self, area_id):
        try:
            self._area_id = int(area_id)
        except ValueError:
            return False

    def get_area_id(self):
        return self._area_id

    def set_hello_interval(self, hello_interval):
        try:
            value = int(hello_interval)
            if not 1 <= value <= 100: # Min and Max
                return False
            self._hello_interval = value
        except ValueError:
            return False

    def get_hello_interval(self):
        return self._hello_interval

    def set_router_dead_interval(self, router_dead_interval):
        try:
            value = int(router_dead_interval)
            if not 1 <= value <= 1000: # Min and Max
                return False
            self._router_dead_interval = value
        except ValueError:
            return False

    def get_router_dead_interval(self):
        return self._router_dead_interval

    def set_router_priority(self, router_priority):
        try:
            value = int(router_priority)
            if not 1 <= value <= 17000: # Min and Max
                return False
            self._router_priority = value
        except ValueError:
            return False

    def get_router_priority(self):
        return self._router_priority

    def set_designated_router(self, designated_router):
        """Seting Designated router IP address and its validation"""
        if(is_valid_ip(designated_router)):
            self._designated_router = designated_router
        return False

    def get_designated_router(self):
        return self._designated_router

    def set_backup_router(self, backup_router):
        """Seting Designated backup router IP address and its validation"""
        if(is_valid_ip(backup_router)):
            self._backup_designated_router = backup_router
        return False

    def get_backup_router(self):
        return self._backup_designated_router

    def get_neighbors(self):
        """Returns a list of neighbor IP addresses"""
        neighbor_ips = []
        for member in self._neighbors:
        #TODO add validation that appends only active neighbors based on NeighborState
             neighbor_ips.append(member.get_address())
        return neighbor_ips

    def receive_event(self, interface_event):
        pass

    def stop_wait_timer(self):
        self._wait_thread.set()

    def _interface_up(self):
        """Switching to UP status
        Stop and remove old timers before starting new"""

        #Remove old hello timer if exists
        if self._hello_timer:
            self._hello_timer.stop()
            self._hello_timer = None

        #Create new timer
        self._hello_timer = PeriodicTimer(self._hello_interval, self.sayhello)

        #Remove old Hello thread if exists
        if self._hello_thread:
            self._hello_thread.join() #Wait for thread to finnish

        #Remove old Wait thread if exists
        if self._wait_thread:
            self._wait_thread.join() #Wait for thread to finnish

        #Set state to waiting
        self.set_interface_state(3)
        self._wait_thread = threading.Event()

        # Waiting timer
        # Can be stopped by calling stop_wait_timer()
        if debug: print("Wait timer starts: ", self._router_dead_interval)
        self._wait_thread.wait(timeout=self._router_dead_interval)
        if debug: print("Wait timer stops")

        #If state has not changed from waiting something is wrong
        if (self.get_interface_state()==InterfaceState.WAITING):
            self._interface_down()

        #Create new thread and start
        self._hello_thread = threading.Thread(target=self._hello_timer.start, daemon=True)
        self._hello_thread.start()

        #Test to add one neighbor
        if debug:
            self._neighbor_change("new", None)
            print("List of neighbors: ", self.get_neighbors())

    def _backup_seen(self):
        pass

    def _wait_timer_triggered(self):
        pass

    def _neighbor_change(self, changetype, values=None):
        """Handling neighbor table"""
        #TODO not ready at all
        #Create new
        if debug: print("Neighbor change\n")
        if(changetype=="new" and len(self._neighbors)==0):
            new_nb = Neighbor(self.next_neighbor_id)
            self.next_neighbor_id += 1
            if new_nb.new_neighbor("10.0.0.7"):
                new_nb.set_neighbor_state(2) #Init
                self._neighbors.append(new_nb)

    def _interface_down(self):
        pass

    def _loop_ind(self):
        pass

    def _unloop_ind(self):
        pass

    def _send_hello(self, connection, destination, router_id):
        """Triggers Message class to send a Hello message"""
        message = HelloMessage.from_interface(self, router_id)
        message_bytes = message.to_bytes()
        connection.send_message(destination, message_bytes)

    def _receive_hello(self, connection):
        """Based on received message
        creates a neighbor or updates an old"""
        if not connection.check_message():
            return
        message_bytes, sender_address = connection.get_message()
        message = HelloMessage.from_bytes(message_bytes)
        # Later: validate the message and update the neighbor.

    def sayhello(self):
        """Method for testing this class"""
        print(f"Hello! I am an interface instance id: {self.id} Hello interval {self._hello_interval}")


    def __str__(self):
        """Creates a string which contains attribute values."""
        return (
            f"ID: {self.id}\n"
            f"Interface type: {self._interface_type}\n"
            f"Interface status: {self._interface_state}\n"
            f"IP address: {self._ip_address}\n"
            f"IP mask: {self._ip_mask}\n"
            f"Interval hello: {self._hello_interval}\n"
            f"Interval dead router: {self._router_dead_interval}\n"
            f"Router priority: {self._router_priority}\n"
        )

