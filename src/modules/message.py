from dataclasses import dataclass, field
import struct
from ipaddress import IPv4Address

HEADER = struct.Struct("!BBH4sIHH8s")
HELLO = struct.Struct("!4sHBBI4s4s")


def _checksum(packet: bytes) -> int:
    # OSPF excludes the 8-byte authentication field from the checksum.
    data = packet[:16] + packet[24:]
    if len(data) % 2:
        data += b"\x00"

    total = sum(
        int.from_bytes(data[i:i + 2], "big")
        for i in range(0, len(data), 2)
    )
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


debug = 1 # Set to 1 for testing the sending of message

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
            neighbors=interface.get_neighbor_ids(),
        )

    def to_bytes(self) -> bytes:
        if self.version != 2 or self.message_type != 1:
            raise ValueError("Expected an OSPFv2 Hello message")

        neighbors = b"".join(IPv4Address(n).packed for n in self.neighbors)
        length = HEADER.size + HELLO.size + len(neighbors)
        if length > 65535:
            raise ValueError("Hello packet exceeds the maximum packet length")

        header = HEADER.pack(
            self.version,
            self.message_type,
            length,
            IPv4Address(self.router_id).packed,
            self.area_id,
            0,          # checksum, filled in below
            0,          # no authentication
            b"\x00" * 8,
        )
        body = HELLO.pack(
            IPv4Address(self.network_mask).packed,
            self.hello_interval,
            0,          # options
            self.router_priority,
            self.router_dead_interval,
            IPv4Address(self.designated_router).packed,
            IPv4Address(self.backup_designated_router).packed,
        )

        packet = header + body + neighbors
        checksum = _checksum(packet)
        return packet[:12] + struct.pack("!H", checksum) + packet[14:]

    @classmethod
    def from_bytes(cls, data: bytes):
        if len(data) < HEADER.size + HELLO.size:
            raise ValueError("Hello packet is too short")

        version, message_type, length, router_id, area_id, _, auth_type, _ = (
            HEADER.unpack_from(data)
        )
        if version != 2 or message_type != 1:
            raise ValueError("Expected an OSPFv2 Hello message")
        if length != len(data) or (length - HEADER.size - HELLO.size) % 4:
            raise ValueError("Invalid Hello packet length")
        if auth_type != 0:
            raise ValueError("Authentication is not supported")
        if _checksum(data) != 0:
            raise ValueError("Invalid packet checksum")

        mask, interval, options, priority, dead, dr, bdr = HELLO.unpack_from(
            data, HEADER.size
        )
        if options != 0:
            raise ValueError("Hello options are not supported")

        neighbor_data = data[HEADER.size + HELLO.size:]
        neighbors = [
            str(IPv4Address(neighbor_data[i:i + 4]))
            for i in range(0, len(neighbor_data), 4)
        ]

        return cls(
            router_id=str(IPv4Address(router_id)),
            area_id=area_id,
            network_mask=str(IPv4Address(mask)),
            hello_interval=interval,
            router_priority=priority,
            router_dead_interval=dead,
            designated_router=str(IPv4Address(dr)),
            backup_designated_router=str(IPv4Address(bdr)),
            neighbors=neighbors,
            version=version,
            message_type=message_type,
        )
