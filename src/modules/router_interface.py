from enum import Enum
from pathlib import Path
import configparser
import threading
from modules.message import HelloMessage
import ipaddress
from modules.periodic_timer import PeriodicTimer
from modules.router_neighbor import Neighbor, NeighborState
from modules.router_connection import SocketConnection

debug = 0 #Set to 1 for debugging / Add one neighbor at start
DEFAULT_PORT = 65435

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
    def __init__(self, given_id:int):
        try:
            self.id = int(given_id)
        except ValueError:
            raise ValueError("ID must be an integer")
        self._interface_type = InterfaceType.BROADCAST
        self._interface_state = InterfaceState.DOWN
        self._config_file = None
        self._ip_version = 4
        self._ip_address = "0.0.0.0"
        self._ip_mask = "0.0.0.0"
        self._area_id = 0 #Documentation says 32bit 0.0.0.0?
        self._hello_interval = 10
        self._router_dead_interval = 40
        self._router_priority = 0
        self._networkconnection = None

        #Timers are set at method _interface_up()
        self._hello_timer = None
        self._hello_thread = None
        self._wait_thread = None
        self._receive_hello_timer = None
        self._receive_hello_thread = None

        self._designated_router = "0.0.0.0"
        self._backup_designated_router = "0.0.0.0"

        self.next_neighbor_id = 1
        self._neighbors = [] #List of neighbor instances NOT READY

    def new_interface(self, interface_type:int, ip_version:int, config_file:str, start_interface=False):
        """Method reads configuration data from given file and 
        checks all data is found before updating values. 
        If data is incorrect falls back to default values.
        Start_interface parameter defines if interface is turned up or not in the end."""

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
        self._config_file = config_file
        config_path = Path(__file__).parent.parent / "config" / config_file
        if not config.read(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

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
        self._networkconnection = SocketConnection()
        #Starting the interface
        if start_interface:
            self._interface_up()


    #Methods for get and set init values

    def get_id(self) -> int:
        return self.id

    def get_interface_type(self) -> InterfaceType:
        return self._interface_type

    def set_interface_state(self, state:int) -> bool:
        """Switches state, state is given as integer"""
        try:
            self._interface_state = InterfaceState(state)
            return True
        except ValueError:
            return False

    def get_interface_state(self) -> InterfaceState:
        return self._interface_state

    def set_address(self, ip_address:str, ip_mask:str):
        """Set IP address and mask, validate given values"""
        if( (is_valid_ip(ip_address)) & (is_valid_network(ip_mask)) ):
            if(self._ip_address != ip_address):
                if self._networkconnection != None:
                    self._networkconnection.dispose()
                    self._networkconnection = None
            self._ip_address = ip_address
            self._ip_mask = ip_mask
        return False

    def get_ip_version(self) -> int:
        return self._ip_version

    def get_address(self) -> str:
        return self._ip_address

    def get_mask(self) -> str:
        return self._ip_mask

    def set_area_id(self, area_id:int):
        try:
            self._area_id = int(area_id)
            return True
        except ValueError:
            return False

    def get_area_id(self) -> int:
        return self._area_id

    def set_hello_interval(self, hello_interval:int)->bool:
        try:
            value = int(hello_interval)
            if not 1 <= value <= 100: # Min and Max
                return False
            self._hello_interval = value
            return True
        except ValueError:
            return False

    def get_hello_interval(self)->int:
        return self._hello_interval

    def set_router_dead_interval(self, router_dead_interval:int) ->bool:
        try:
            value = int(router_dead_interval)
            if not 1 <= value <= 1000: # Min and Max
                return False
            self._router_dead_interval = value
            return True
        except ValueError:
            return False

    def get_router_dead_interval(self)->int:
        return self._router_dead_interval

    def set_router_priority(self, router_priority:int)->bool:
        try:
            value = int(router_priority)
            if not 0 <= value <= 17000: # Min and Max
                return False
            self._router_priority = value
            return True
        except ValueError:
            return False

    def get_router_priority(self)->int:
        return self._router_priority

    def set_designated_router(self, designated_router:str)->bool:
        """Seting Designated router IP address and its validation"""
        if(is_valid_ip(designated_router)):
            self._designated_router = designated_router
            return True
        return False

    def get_designated_router(self)->str:
        return self._designated_router

    def set_backup_router(self, backup_router:str)->bool:
        """Setting Designated backup router IP address and its validation"""
        if(is_valid_ip(backup_router)):
            self._backup_designated_router = backup_router
            return True
        return False

    def get_backup_router(self)->str:
        return self._backup_designated_router


    #Methods for running and timers

    def delete_timers_and_threads(self)->bool:
        """Stop and remove old timers and threads"""
        #Remove Wait thread if exists
        if self._wait_thread:
            self._wait_thread.set() #Wait for thread to finnish

        #Remove Hello timer if exists
        if self._hello_timer:
            self._hello_timer.stop()
            self._hello_timer = None

        #Remove Hello thread if exists
        if self._hello_thread:
            self._hello_thread.join() #Wait for thread to finnish

        #Remove Receive Hello timer if exists
        if self._receive_hello_timer:
            self._receive_hello_timer.stop()
            self._receive_hello_timer = None

        #Remove Receive Hello thread if exists
        if self._receive_hello_thread:
            self._receive_hello_thread.join() #Wait for thread to finnish

        return True

    def stop_wait_timer(self)->bool:
        """Stops router dead interval timer before it expires"""
        self._wait_thread.set()
        return True

    def _interface_up(self):
        """Switching Interface to running status: DR, BR, DROTHER
        First deleting old timers and threads before creating new.
        Wait while dead router interval and then start sending
        and receiving Hello messages.
        """
        #Delete all ghost timers and threads
        self.delete_timers_and_threads()

        #Connect Networkconnection thingy
        print("attempting connect_network on ",(self.get_address(),DEFAULT_PORT))
        if not self._networkconnection.connect_network((self.get_address(),DEFAULT_PORT)):
            ### Something went badly wrong
            raise Exception("oh no the network did not connect")
        #Set state to waiting
        self.set_interface_state(InterfaceState.WAITING)
        self._wait_thread = threading.Event()

        # Waiting timer
        # Can be stopped by calling stop_wait_timer()
        if debug: print("Wait timer starts: ", self._router_dead_interval)
        self._wait_thread.wait(timeout=self._router_dead_interval)
        if debug: print("Wait timer stops")

        #TODO: Activate these after Election works
        # If state has not changed from waiting something is wrong
        #if (self.get_interface_state()==InterfaceState.WAITING):
        #    self._interface_down()

        #Create new Hello timer
        #TODO: Change from Mockup method to _receive_hello
        #self._hello_timer = PeriodicTimer(self._hello_interval, self.sayhello)
        self._hello_timer = PeriodicTimer(self._hello_interval, self._send_hello)

        #Create new Hello thread and start sending hello messages
        self._hello_thread = threading.Thread(target=self._hello_timer.start, daemon=True)
        self._hello_thread.start()

        #Create new Receive Hello timer
        #TODO: Change from Mockup method to _receive_hello
#        self._receive_hello_timer = PeriodicTimer(self._hello_interval, self._receive_hello)
#        self._receive_hello_timer = PeriodicTimer(self._hello_interval, self.sayhello2)

        #Create new Receive Hello thread and start receiving Hello messages
#        self._receive_hello_thread = threading.Thread(target=self._receive_hello_timer.start, daemon=True)
#        self._receive_hello_thread.start()

        #Test to add one neighbor
        #TODO remove after Messages and Neighbors are running
        if debug:
            self._neighbor_change("new", None)
            print("List of neighbors: ", self.get_neighbors())
            print("IDs", self.get_neighbor_ids())

    def _interface_down(self):
        """Set values to default. Stop timers and threads. Remove adjacensies."""
        self.delete_timers_and_threads()
        if self._networkconnection != None:
            self._networkconnection.dispose()
        self.new_interface(2, 4, self._config_file, False)


    #Methods for Hello messagess

    def _send_hello(self):
        """Triggers Message class to send a Hello message"""
        #print("Sending hello from ",112)
        message = HelloMessage.from_interface(self, 1)
        message_bytes = message.to_bytes()
        self._networkconnection.send_message(("10.112.28.0",DEFAULT_PORT), message_bytes)

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

    def sayhello2(self):
        """Method for testing this class"""
        print(f"Hello from thread 2!")

    #Methods for Neighboring

    def get_neighbor_ids(self)->list:
        """Returns a list of neighbor IDs"""
        #TODO Improve eg. add validation that appends only active neighbors based on NeighborState
        neighbor_ids = []
        for member in self._neighbors:
             neighbor_ids.append(member.get_neighbor_id())
        return neighbor_ids

    def get_neighbors(self)->list:
        """Returns a list of neighbor IPs"""
        neighbor_ips = []
        for member in self._neighbors:
        #TODO add validation that appends only active neighbors based on NeighborState
             neighbor_ips.append(member.get_address())
        return neighbor_ips

    def _neighbor_change(self, changetype:str, values=None)->bool:
        """Handling neighbor table"""
        #TODO This is just a mockup, not ready at all
        #Create new
        if debug: print("Neighbor change\n")
        if(changetype=="new" and len(self._neighbors)==0):
            new_nb = Neighbor(self.next_neighbor_id)
            self.next_neighbor_id += 1
            if new_nb.new_neighbor("10.0.0.7"):
                new_nb.set_neighbor_state(2) #Init
                self._neighbors.append(new_nb)
                return True
        return False

    def _backup_seen(self):
        pass

#Methods with no use yet

    def receive_event(self, interface_event):
        pass

    def _wait_timer_triggered(self):
        pass

    def _loop_ind(self):
        """Not used in our project"""
        pass

    def _unloop_ind(self):
        """Not used in our project"""
        pass


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

