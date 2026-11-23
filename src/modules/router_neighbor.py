from enum import Enum

class NeighborState(Enum):
    DOWN = 0 
    ATTEMPT = 1
    INIT = 2 #default when creating new
    TWO_WAY = 3
    EXSTART = 4
    EXCHANGE = 5
    LOADING = 6
    FULL = 7


class Neighbor:
    def __init__(self, given_id):
        try:
            self.neighbor_id = int(given_id)
        except ValueError:
            raise ValueError("ID must be an integer")
        self._neighbor_state= NeighborState.INIT
        self._ip_address = "0.0.0.0"
        self._priority = 0
        self._designated_router = "0.0.0.0"
        self._backup_designated_router = "0.0.0.0"

        # Routing related (not included in our project)
        self._leader_follower = 0 # Who sends initial Routing Database Description Packet
        self._dd_sequence_number = 0 # Routing Database Description Packet
        self._last_received_ddp = 0 # Routing Database Description Packet
        self._options = 0 #supported optional OSPF capabilities

    def new_neighbor(self, ip_address):
        if self.set_address(ip_address):
            print("New neighbor created, id:", self.neighbor_id, "IP:", self._ip_address)
            return True
        return False

    def get_neighbor_id(self)->int:
        return self.neighbor_id

    def set_neighbor_state(self, state:int)->bool:
        """Switches state"""
        try:
            self._neighbor_state = NeighborState(state)
            return True
        except ValueError:
            return False

    def get_neighbor_state(self)->NeighborState:
        return self._neighbor_state

    def set_address(self, ip_address:str):
        """Set IP address. Validated at NetworkInterface"""
        if ip_address:
            self._ip_address = ip_address
            return True
        return False

    def get_address(self)->str:
        return self._ip_address

    def set_priority(self, priority:int)->bool:
        try:
            value = int(priority)
            if not 0 <= value <= 17000: # Min and Max
                return False
            self._priority = value
            return True
        except ValueError:
            return False

    def get_priority(self)->int:
        return self._priority

    def set_designated_router(self, designated_router:str)->bool:
        if designated_router:
            self._designated_router = designated_router
            return True
        return False

    def get_designated_router(self)->str:
        return self._designated_router

    def set_backup_router(self, backup_router:str)->bool:
        if backup_router:
            self._backup_designated_router = backup_router
            return True
        return False

    def get_backup_router(self)->str:
        return self._backup_designated_router

    def receive_event(self, neighbor_event):
        pass
    def _hello_received(self):
        pass
    def _two_way_received(self):
        pass
    def _one_way_received(self):
        pass
    def _kill_neighbor(self):
        pass
    def _inactivity_timer_triggered(self):
        pass
    def _lower_level_down_received(self):
        pass
    def _adjacency_ok_check(self):
        pass

    # Routing related (not included in our project)
    def _start(self):
        pass
    def _sequence_number_mismatch(self):
        pass
    def _bad_link_state_request(self):
        pass 
    def _negotiation_done(self):
        pass
    def _exchange_done(self):
        pass
    def _loading_done(self):
        pass
