from dataclasses import dataclass, field

@dataclass
class HelloMessage:
    router_id: str
    area_id: int
    network_mask: str
    hello_interval: int
    router_priority: int
    router_dead_interval: int
    designated_router: str = "0.0.0.0"
    backup_designated_router: str = "0.0.0.0"
    neighbors: list[str] = field(default_factory=list)
    version: int = 2
    message_type: int = 1

    @classmethod
    def from_interface(cls, interface, router_id):
        return cls(
            router_id=router_id,
            area_id=interface.get_area_id(),
            network_mask=interface.get_mask(),
            hello_interval=interface.get_hello_interval(),
            router_priority=interface.get_router_priority(),
            router_dead_interval=interface.get_router_dead_interval(),
            designated_router=interface.get_designated_router(),
            backup_designated_router=interface.get_backup_router(),
            # TODO: Replace IP addresses with recently heard neighbor router IDs.
            neighbors=interface.get_neighbors(),
        )
    def to_bytes(self) -> bytes:
        raise NotImplementedError("Hello message encoding is not implemented yet")
    @classmethod
    def from_bytes(cls, data: bytes):
        raise NotImplementedError("Hello message decoding is not implemented yet")
