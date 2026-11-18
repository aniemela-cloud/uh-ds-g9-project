from enum import Enum
from pathlib import Path
import configparser

debug = 0 #Set to 1 for debugging prints

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

class NetworkInterface:
    def __init__(self, given_id):
        self.id = given_id      #Unique/Given
        self._interface_type = InterfaceType.BROADCAST    #enum/Given
        self._interface_state = InterfaceState.DOWN        #state/Given
        self._ip_version = 4              #int/Given
        self._ip_address = "0.0.0.0"      #IPAddress/Config
        self._ip_mask = "0.0.0.0"         #IPAddress/Config
        self._hello_interval = 10         #Integer/Config
        self._router_dead_interval = 40   #Integer/Config
        self._router_priority = 0         #Integer/Config
        self._hello_timer = 0             #Timer
        self._wait_timer = 0              #Timer
        self._designated_router = "0.0.0.0"        #IPAddress
        self._backup_designated_router = "0.0.0.0" #IPAddress
        self._neighbors = [] #List of neighbors

    def new_interface(self, interface_type, ip_version, config_file):
        """Method reads configuration data from given file and 
        checks all data is found before updating values."""
        #self._interface_type = InterfaceType(interface_type)
        try:
            self._interface_type = InterfaceType(interface_type)
        except ValueError:
            raise ValueError(f"Invalid interface type [{interface_type}]")
        if ip_version not in (4, 6):
            raise ValueError(f"Invalid IP version [{ip_version}]")
        self._ip_version = ip_version

        config = configparser.ConfigParser()
        config_file = Path(__file__).parent.parent / "config" / config_file
        config.read(config_file)

        required = [("network", "ip_address"), ("network", "ip_mask"),
        ("interval", "hello"), ("interval", "dead"), ("router", "priority")]

        for section, key in required:
            if section not in config:
                raise ValueError(f"Missing section [{section}]")
            if key not in config[section]:
                raise ValueError(f"Missing key '{key}' in section [{section}]")

        #If values are not accepted, fallback values are set as default
        try:
            self.set_address(config.get("network", "ip_address", fallback="0.0.0.0"),
                                config.get("network", "ip_mask", fallback="0.0.0.0"))
        except ValueError:
            self.set_address("0.0.0.0", "0.0.0.0")
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

    def get_id(self):
        return self.id

    def get_interface_type(self):
        return self._interface_type

    def get_interface_state(self):
        return self._interface_state

    def set_address(self, ip_address, ip_mask):
        """Set IP address and mask"""
        #TODO validation
        self._ip_address = ip_address
        self._ip_mask = ip_mask

    def get_ip_version(self):
        return self._ip_version

    def get_address(self):
        return self._ip_address

    def get_mask(self):
        return self._ip_mask

    def set_hello_interval(self, hello_interval): #private?
        self._hello_interval = hello_interval

    def get_hello_interval(self):
        return self._hello_interval

    def set_router_dead_interval(self, router_dead_interval):
        self._router_dead_interval = router_dead_interval

    def get_router_dead_interval(self):
        return self._router_dead_interval

    def set_router_priority(self, router_priority):
        self._router_priority = router_priority

    def get_router_priority(self):
        return self._router_priority

    def receive_event(self, interface_event): #What is this?
        pass

    def _interface_up(self):
        pass

    def _backup_seen(self):
        pass

    def _wait_timer_triggered(self):
        pass

    def _neighbor_change(self):
        pass

    def _interface_down(self):
        pass

    def _loop_ind(self):
        pass

    def _unloop_ind(self):
        pass

    def _send_hello(self):
        """Triggers Message class to send a Hello message"""
        pass

    def _receive_hello(self):
        """Based on received message
        creates a neighbor or updates an old"""
        pass

    def sayhello(self):
        """Method for testing this class"""
        return f"Hello! I am an interface instance id: {self.id}"

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
