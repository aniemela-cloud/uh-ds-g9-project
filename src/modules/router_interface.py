from enum import Enum
from pathlib import Path
import configparser
import time
from modules.message import HelloMessage
import ipaddress
from modules.router_neighbor import Neighbor, NeighborState
from modules.router_connection import SocketConnection

debug = 1 #Set to 1 for debugging 

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
    class _ElectionMember():
        """ A simple data class for the (backup) designated router election.
        """
        def __init__(self, router_id: int, priority: int, ip_address: str, 
                     designated_router: str, backup_router: str):
            self.router_id = router_id
            self.priority = priority
            self.ip_address = ip_address
            self.designated_router = designated_router
            self.backup_router = backup_router
        
        def __str__(self):
            return (
                "_ElectionMember:"
                f"Router priority: {self.priority}\n"
                f"IP address {self.ip_address}\n"
                f"Reported designated router {self.designated_router}\n"
                f"Reported backup router {self.backup_router}\n"
            )

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
        self._port = None
        self._destination_ip = "0.0.0.0"
        self._area_id = 0 #Documentation says 32bit 0.0.0.0?
        self._hello_interval = 10
        self._router_dead_interval = 40
        self._router_priority = 0
        self._networkconnection = None

        #Timers are set at method _interface_up()
        self._hello_timer = None
        self._wait_timer = None
        self._receive_hello_timer = None

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
                    ("network", "port"), ("network", "destination"),
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
            self.set_port(config.getint("network", "port", fallback=None))
        except ValueError:
            self.set_port(None)
        try:
            self.set_destination_ip(config.get("network", "destination", fallback="0.0.0.0"))
        except ValueError:
            self.set_destination_ip("0.0.0.0")

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

        #Create Socket
        self._networkconnection = SocketConnection()

        #Starting the interface
        if start_interface:
            self._interface_up()


    #Methods for get and set init values

    def get_id(self) -> int:
        return self.id

    def get_interface_type(self) -> InterfaceType:
        return self._interface_type

    def set_interface_state(self, state:InterfaceState) -> bool:
        """Switches state"""
        if not isinstance(state, InterfaceState):
            return False
        try:
            self._interface_state = state
            return True
        except ValueError:
            return False

    def get_interface_state(self) -> InterfaceState:
        return self._interface_state

    def set_address(self, ip_address:str, ip_mask:str):
        """Set IP address and mask, validate given values"""
        if( (is_valid_ip(ip_address)) & (is_valid_network(ip_mask)) ):
            self._ip_address = ip_address
            self._ip_mask = ip_mask
        return False

    def get_ip_version(self) -> int:
        return self._ip_version

    def get_address(self) -> str:
        return self._ip_address

    def set_port(self, port:int) -> bool:
        try:
            self._port = int(port)
            return True
        except ValueError:
            return False

    def get_port(self) -> int:
        return self._port

    def set_destination_ip(self, destination:str) -> bool:
        if is_valid_ip(destination):
            self._destination_ip = destination
            return True
        return False

    def get_destination_ip(self) -> int:
        return self._destination_ip

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

    def stop_wait_timer(self)->bool:
        """Stops router dead interval timer before it expires"""
        self._wait_timer = None
        return True

    def _interface_up(self):
        """Looping Interface based on its status.
        Each status case calls methods it should be running.
        """
        print("Interface is getting up")
        if debug: state_log = self._interface_state

        while True:
            if debug:
                #Print the state changes
                if state_log!=self._interface_state: 
                    print("InterfaceStatus: ", self._interface_state.name)
                    state_log = self._interface_state

            match self._interface_state:
                case InterfaceState.DOWN:

                    #Connect Networkconnection thingy
                    if debug: print("Attempting connect_network on ",(self.get_address(),self._port))
                    if not self._networkconnection.connect_network((self.get_address(),self._port)):
                        ### Something went badly wrong
                        raise Exception("oh no the network did not connect")
                    
                    self.set_interface_state(InterfaceState.WAITING)
                    self._wait_timer = time.monotonic() + self._router_dead_interval

                case InterfaceState.LOOPBACK:
                    pass

                case InterfaceState.POINTTOPOINT:
                    pass

                case InterfaceState.WAITING:
                    # Get messages
                    #TODO if socket.check_messages:
                        # Received message 
                        # if it includes DR/BAckup changes status to DROTHER
                        # Or it runs election which changes status to
                        # either DR, DR_OTHER, or Backup

                    # Check if wait timer has expired
                    if time.monotonic() >= self._wait_timer:
                        #TODO run election
                        # the run_election_stuff will assign us a state
                        # either DR, DR_OTHER, or Backup

                        #Before election, this changes to next status
                        if debug: self.set_interface_state(InterfaceState.DROTHER)
                        pass

                    #In case state changed, initialize Hello timer
                    if self._interface_state != InterfaceState.WAITING:
                        self._hello_timer = time.monotonic() + self._hello_interval

                case InterfaceState.DROTHER | InterfaceState.BACKUP | InterfaceState.DR:
                    # First, we send out hello if the interval has expired
                    if time.monotonic() >= self._hello_timer:
                        if debug: print("Time to send a hello...")
                        self._send_hello()
                        # Reset timer
                        self._hello_timer = time.monotonic() + self._hello_interval
                        if debug:
                            print("Sent message")
                            break #Stop to send only one message

                    # Second, we take in one message if there are any
                    if self._networkconnection.check_message():
                    #    process_message(socket.get_message)
                    # Status can change based on processing
                        pass 

                        #Third, we check if any neighbor has died
                        for nb in self._neighbors:
                        #    neighbor.check_wait_timer
                            pass

                    #if no messages, sleep for a second
                    else:
                        if debug: print("Sleeping")
                        time.sleep(10)

                case _:
                    raise Exception("Interface is stateless")


    def _interface_down(self):
        """Set values to default. Stop timers. Remove adjacensies."""
        self._wait_timer = None
        self._hello_timer = None
        self.new_interface(2, 4, self._config_file, False)


# Methods for EVENT HANDLING, triggered from received message

    def receive_event(self, interface_event, message=None):
        """Actions based on events"""

        if interface_event=="HelloReceived":
            self._handle_received_message(message)
        elif interface_event=="BackupSeen":
            self._handle_backup_seen(message)
        elif interface_event=="2-WayReceived":
            self._handle_twoway(message)
        elif interface_event=="1-WayReceived":
            self._handle_oneway(message)
        elif interface_event=="NeighborChange":
            self._handle_neighbor_change(message)
        elif interface_event=="KillNbr":
            self._handle_neighbor_dead()
        else:
            raise Exception("Unknown Interface Event")

# Conditions for MESSAGE processing

    def _match_config_condition(self, message:HelloMessage) -> bool:
        """Validates if Hello message has same parameters as this interface"""
        #if debug: print("Conditions, mask:", message.network_mask , self._ip_mask,"Hellointerval:", message.hello_interval , self._hello_interval, "Deadinterval:", message.router_dead_interval , self._router_dead_interval)
        return (message.network_mask == self._ip_mask and 
                message.hello_interval == self._hello_interval and 
                message.router_dead_interval == self._router_dead_interval)

    def _backup_seen_condition(self, message:HelloMessage) -> bool:
        """Validates if after bootup received Hello has DR or BDR"""
        return (self._interface_state == InterfaceState.WAITING and 
            ((message.router_id == message.designated_router and 
              message.backup_designated_router == "0.0.0.0") or 
              (message.router_id == message.backup_designated_router)))

    def _new_neighbor_condition(self, message:HelloMessage) -> bool:
        """Validates if Hello message has a new (unknown) neighbor ID"""
        return message.router_id in self.get_neighbor_ids()

    def _twoway_condition(self, message:HelloMessage) -> bool:
        """Validates if this interface is included on neighbors list"""
        #TODO IP or ID?
        return self.id in message.neighbors

    def _priority_same_condition(self, message):
        """Validates if priority has changed"""
        nb = self.get_neighbor(message.router_id)
        return (message.router_priority == nb.get_priority())

    def _leaders_same_condition(self, message):
        """Validates if neighbors DR/BDR have changed"""
        nb = self.get_neighbor(message.router_id)
        return (message.designated_router==nb.get_designated_router() and
                message.backup_designated_router==nb.get_backup_router())

    def _conflict_condition(self, message):
        """Does it have other DR/BDR than in this interface"""
        return (message.designated_router == self.get_designated_router() and message.backup_designated_router == self.get_backup_router())



# Methods for MESSAGE HANDLING

    def _handle_received_message(self, message:HelloMessage):
        if debug: print("Handling received message")
        #Init sender neighbor
        nb = None

        # Check hello has same network and timer parameters
        if self._match_config_condition(message) == False:
            #Parameters do not match so message is not processed
            if debug: print("\tDid not match conditions")
            return

        # After bootup waiting if network has already selected leaders
        if self._backup_seen_condition(message):
            if debug: print("\tBackupSeen->>")
            self.receive_event("BackUpSeen", message)

        # Is the neighbor ID from new previously unknown router
        if self._new_neighbor_condition(message) or not self._neighbors:
            # Create new neighbor
            if debug: print("NEW neighbor detected")
            nb = Neighbor(message.router_id)
            self._neighbors.append(nb)

            # Does it know this inteface or not
            if self._twoway_condition(message):
                if debug: print("TRIGGER 2-WAY")
                self.receive_event("2-WayReceived", message)
            else:
                if debug: print("TRIGGER 1-WAY")
                self.receive_event("1-WayReceived", message)

            self.receive_event("NeighborChange", message)

        else:
            if debug: print("OLD neighbor detected", self._new_neighbor_condition(message))

            #This is a known neighbor
            nb = self.get_neighbor(message.router_id)

            # Does it know this inteface or not
            #TODO this repeats bc has to be done before other updates
            if self._twoway_condition(message):
                if debug: print("TRIGGER 2-WAY")
                self.receive_event("2-WayReceived", message)
            else:
                if debug: print("TRIGGER 1-WAY")
                self.receive_event("1-WayReceived", message)

            #Has its priority changed
            if not self._priority_same_condition(message):
                self.receive_event("NeighborChange", message)

            #Has it been DR/BDR and is not anymore, or is now declaring to be
            elif not self._leaders_same_condition(message):
                self.receive_event("NeighborChange", message)

            #Does it have other DR/BDR than in this interface
            elif self._conflict_condition(message):
                self.receive_event("NeighborChange", message)

            #Nothing has changed, just update timer
            self._update_neighbor_timer()
        if debug: print("End of handling")


    def _handle_backup_seen(self, message):
        if debug: print("BackUpSeen is handled")
        # TODO: not implemented yet
        pass

    def _handle_neighbor_change(self, message: HelloMessage)->bool:
        """Handling neighbor table"""
        if debug: print("Neighbor change\n")
        pass

    def _handle_twoway(self, message):
        nb = self.get_neighbor(message.router_id)
        if nb.set_neighbor_state(NeighborState.TWO_WAY):
            return True
        return False

    def _handle_oneway(self, message):
        nb = self.get_neighbor(message.router_id)
        print("Neighbor", self.get_neighbor_ids(), message.router_id)
        if nb.set_neighbor_state(NeighborState.INIT):
            return True
        return False

    def _handle_neighbor_dead():
        #TODO not implemented yet
        pass

    def _update_neighbor_timer(neighbor:Neighbor):
        if neighbor.set_timer():
            return True
        return False

    #Methods for Hello messages

    def _send_hello(self):
        """Triggers Message class to send a Hello message"""
        if debug: print("Sending hello from ", self._ip_address, ":", self._port, "to", self._destination_ip)
        message = HelloMessage.from_interface(self, self.id)
        message_bytes = message.to_bytes()
        self._networkconnection.send_message((self._destination_ip,self._port), message_bytes)

    def _receive_hello(self, connection):
        """Based on received message
        creates a neighbor or updates an old"""
        if not connection.check_message():
            return
        message_bytes, sender_address = connection.get_message()
        message = HelloMessage.from_bytes(message_bytes)
        if (message.message_type == 1):
            self.receive_event("HelloReceived", message)
        return

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

    def get_neighbor(self, router_id)->Neighbor:
        """Returns a neighbor instance based on its id"""
        for nb in self._neighbors:
            if nb.neighbor_id == router_id:
                return nb
        return None


# ELECTION

    def _run_election(self):
        """Runs the OSPF Designated Router election.
        
        Reference: https://www.rfc-editor.org/info/rfc2328/#page-75
        """
        # Store the current (backup) designated router for use later
        current_dr = self.get_designated_router()
        current_bdr = self.get_backup_router()
        
        # List of eligible routers (in general), that is, routers in the
        # 2-Way state that have router priority != 0, plus this router 
        # (assuming this router's router priority != 0)
        valid_list = []
        thisRouter = None
        if self.get_router_priority() > 0:
            # Start with this router, saving the _ElectionMember reference for 
            # later
            thisRouter = self._ElectionMember(
                self.id,
                self._router_priority,
                self._ip_address,
                self._designated_router,
                self._backup_designated_router,
            )
            valid_list.append(thisRouter)
        
        # Iterate through neighbors, adding eligible ones
        for member in self._neighbors:
            # Skip if the state is not at least 2-Way
            if member.get_neighbor_state().value < NeighborState.TWO_WAY.value:
                continue
            # Skip if the router priority indicates the neighbor does not
            # want to be a (B)DR
            if member.get_priority() == 0:
                continue
            # Otherwise the neighbor is eligible, and we add it to the
            # list:
            valid_list.append(
                self._ElectionMember(member.get_neighbor_id(),
                                member.get_priority(),
                                member.get_address(),
                                member.get_designated_router(),
                                member.get_backup_router()))
        # First we try to get a backup designated router selected
        # from the list of eligible candidates:
        maybe_backup = self._elect_backup(valid_list)
        maybe_designated = self._elect_designated(valid_list)
        
        # The backup election *must* find a prospective backup router. If none
        # is found, it means there are no routers in the network that we have
        # 2-Way with AND this router itself is ineligible to be the backup.
        if maybe_backup is None:
            raise Exception("Election error: No eligible routers found.")
            # We can think of using some other method for communicating the
            # failure later.
        
        # It is possible the DR election does not find a DR, because no router
        # has declared itself as the DR.
        if maybe_designated is None:
            # In this case we select the found backup DR as the actual DR,
            # basically "promoting" it.
            maybe_designated = maybe_backup
        
        # Check whether this router was selected as the DR through the above
        # AND that this router was NOT the DR before the calculations
        # + Same check for BDR
        if (self.id == maybe_designated.router_id and current_dr != self._ip_address) or \
            (self.id == maybe_backup.router_id and current_bdr != self._ip_address):
            if thisRouter is None:
                raise Exception("Election error: This router was selected as the (B)DR even though this router should not be eligible.")
            # We assign the DR/BDR IP addresses to this router's _ElectionMember
            # instance, so that in case it used to be the BDR and was elected
            # DR, it will be disqualified from the BDR selection
            thisRouter.designated_router = maybe_designated.ip_address
            thisRouter.backup_router = maybe_backup.ip_address
            maybe_backup = self._elect_backup(valid_list)
            maybe_designated = self._elect_designated(valid_list)
        
        # We now should have a designated router and backup designated router
        # selected. If we have somehow failed to find either, we assign
        # 0.0.0.0 as the DR/BDR address
        if maybe_backup is None:
            self.set_backup_router("0.0.0.0")
        else:
            self.set_backup_router(maybe_backup.ip_address)
        if maybe_designated is None:
            self.set_designated_router("0.0.0.0")
        else:
            self.set_designated_router(maybe_designated.ip_address)
        
        if self.get_designated_router() == self.get_address():
            self.set_interface_state(InterfaceState.DR)
        elif self.get_backup_router() == self.get_address():
            self.set_interface_state(InterfaceState.BACKUP)
        else:
            self.set_interface_state(InterfaceState.DROTHER)
        
    def _elect_backup(self, election_list:list[_ElectionMember])->_ElectionMember:
        """ Helper method for finding the backup designated router.
        
        Iterates through the election_list according to rules for the backup
        designated router selection for OSPFv2. 
        """
        # Note to self: This function could probably be abstracted so that
        # we don't have to perform basically the exact same checks for 
        # electing the *designated* router, but my brain isn't braining
        # enough to figure out how to do that, since the algorithms
        # check different members of the _ElectionMember objects. Don't have
        # the time to figure it out so copy paste coding GO
        
        if type(election_list) is not list:
            return None
        if len(election_list) == 0:
            return None
        # Filter out all members in the list that have declared themselves
        # as the _designated_ router
        backup_list = [member for member in election_list 
                       if member.designated_router != member.ip_address]
        elected_backup = None
        highest_prio = None
        
        for member in backup_list:
            # We use this for loop to find the member with the highest
            # router priority in case we need the information later. 
            if highest_prio is None:
                highest_prio = member
            elif highest_prio.priority < member.priority:
                highest_prio = member
            elif highest_prio.priority == member.priority:
                # Equal priorities, check router ID with higher
                # winning
                if highest_prio.router_id < member.router_id:
                    highest_prio = member
            
            # Check what the member declared as it's backup DR
            if member.backup_router == member.ip_address:
                # The router has declared itself as the backup
                if elected_backup is None:
                    # There is currently no prospective election winner,
                    # so this router declaring itself as backup gets the
                    # spot
                    elected_backup = member
                elif elected_backup.priority < member.priority:
                    # The currently prospective winner has lower priority
                    # than this router, so this router gets the spot
                    elected_backup = member
                elif elected_backup.priority == member.priority:
                    # Equal priorities, check router ID with higher
                    # winning
                    if elected_backup.router_id < member.router_id:
                        elected_backup = member
        
        if elected_backup is None:
            # The above iteration did not find a router that declares itself
            # the backup designated router. We use the alternative method:
            # Highest router priority wins (which is why we used the 
            # for loop above to find that, too)
            elected_backup = highest_prio
        
        return elected_backup
    
    def _elect_designated(self, election_list: list[_ElectionMember]) -> _ElectionMember:
        if type(election_list) is not list:
            return None
        if len(election_list) == 0:
            return None
        
        elected_router = None
        
        for member in election_list:
            # Check what the member declared as it's DR
            if member.designated_router == member.ip_address:
                # The router has declared itself as the DR
                if elected_router is None:
                    # There is currently no prospective election winner,
                    # so this router declaring itself as backup gets the
                    # spot
                    elected_router = member
                elif elected_router.priority < member.priority:
                    # The currently prospective winner has lower priority
                    # than this router, so this router gets the spot
                    elected_router = member
                elif elected_router.priority == member.priority:
                    # Equal priorities, check router ID with higher
                    # winning
                    if elected_router.router_id < member.router_id:
                        elected_router = member
        
        # It's possible that the above election loop did not find a router
        # that declares itself as the designated router, and thus no DR is
        # found. elected_router can thus be None. This is fine, and the
        # caller's problem, actually.
        return elected_router


#Methods with no use yet

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
            f"Interface status: {self._interface_state.name}\n"
            f"IP address: {self._ip_address}\n"
            f"IP mask: {self._ip_mask}\n"
            f"Port: {self._port}\n"
            f"Destination IP: {self._destination_ip}\n"
            f"Interval hello: {self._hello_interval}\n"
            f"Interval dead router: {self._router_dead_interval}\n"
            f"Router priority: {self._router_priority}\n"
        )

