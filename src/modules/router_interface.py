from enum import Enum

class InterfaceType(Enum):
    POINT-TO-POINT = 1
    BROADCAST = 2
    NBMA = 3
    POINT-TO-MULTIPOINT = 4
    VIRTUAL = 5
    UNDEFINED = 0 #TODO: default / is this needed?

class InterfaceState(Enum):
    DOWN = 0
    LOOPBACK = 1
    POINT-TO-POINT = 2
    WAITING = 3
    DR-OTHER = 4
    BACKUP = 5
    DR = 6

class NetworkInterface:
    def __init__(self, interface_type, ip_version):
        id = 0      #Unique before IPAddress is assigned
        interface_type = InterfaceType.BROADCAST    #enum
        interface_state = InterfaceState.DOWN        #state
        ip_version = 4              #int
        ip_address = "0.0.0.0"      #IPAddress
        ip_mask = "0.0.0.0/0"         #IPAddress
        hello_interval = 10         #Integer
        router_dead_interval = 40   #Integer
        router_priority = 0         #Integer
        hello_timer = 0             #Timer
        wait_timer = 0              #Timer
        designated_router = "0.0.0.0"        #IPAddress 
        backup_designated_router = "0.0.0.0" #IPAddress 

    def new_interface(self, interface_type, ip_version):
        pass

    def set_address(self, ip_address,ip_mask):
        pass

    def set_hello_interval(self, hello_interval):
        pass

    def get_hello_interval(self, hello_interval): 
        pass

    def set_router_dead_interval(self, router_dead_interval):
        pass

    def get_router_dead_interval(self, router_dead_interval):
        pass

    def receive_event(self, interface_event): #What is this?
        pass

    def interface_up(self):
        pass

    def backup_seen(self):
        pass

    def wait_timer_triggered(self):
        pass

    def neighbor_change(self):
        pass

    def interface_down(self):
        pass

    def loop_ind(self):
        pass

    def unloop_ind(self):
        pass

    def send_hello(self):
        pass

    def receive_hello(self):
        pass

    def sayhello(self):
        return "Hello! I am an interface instance."

    def __str__(self):
        """Creates a string which contains attribute values."""
        return (
            f"ID: {self.id}\n"
            f"Interface type: {self.interface_type}\n"
            f"Interface status:" {self.interface_state}\n"
            f"IP address: {self.ip_address}\n"
            #TODO: add rest
        )
