# uh-ds-g9-project
Repository for Uni of Helsinki Distributed Systems 2026 project g9

## Project description
This project implements an OSPF-inspired designated router mechanism. 

Routers exchange Hello messages to discover neighbors, verify 
reachability, and elect a designated router (DR) 
and backup designated router (BDR). 

If the DR fails, the BDR automatically takes over to maintain network 
operation. Each router manages its own neighbor table.
