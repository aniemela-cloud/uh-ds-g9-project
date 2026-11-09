# Base Network Topologies and Node Roles

## Basic Network Architecture

The network architecture consists of similar nodes all connected to a shared multicast network.

```mermaid
---
title: Network Topology
---
flowchart TB
    A((Node 1))
    B((Node 2))
    C((Node 3))
    Net@{ "shape": "datastore", "label":"Broadcast network" }
    D((Node 4))
    E((Node 5))
    A---Net
    B---Net
    C---Net
    Net---D
    Net---E
```

## Hello Messages in the Network

All nodes send Hello messages as multicast messages in the network. The Hello messages are delivered to and processed by all nodes in the network. Hello messages are used to select the Designated Router (DR) and Backup Designated Router (BDR)

```mermaid
---
title: Nodes send Hello messages as multicast
---
flowchart TB
    A((Node 1))
    B((Node 2))
    C((Node 3))
    Net@{ "shape": "datastore", "label":"Broadcast network" }
    D((Node 4))
    E((Node 5))
    A == Hello ==> Net
    Net --> B
    Net --> C
    Net --> D 
    Net-->E
```

## Adjacencies After Designated Router and Backup Designated Router Selection

Once a Designated Router (DR) and Backup Designated Router (BDR) have been selected, both the DR and the BDR create adjacencies with all the other nodes in the network. 

```mermaid
---
title: Adjacencies after DR and BDR selection
---
flowchart TB
    A((Node 1))
    B((Node 2))
    C(("Node 3 <br>[DR]"))
    %%Net@{ "shape": "datastore", "label":"Broadcast network" }
    D((Node 4))
    E(("Node 5 <br>[BDR]"))
    C --- A
    C --- B
    C --- D
    A -.- E
    B -.- E
    D -.- E
    C === E
```

_The normal lines represent adjacencies formed by the Designated Router, and the dashed lines represent adjacencies formed by the Backup Designated Router. The adjacency formed between the DR and the BDR is shown as a thick line._
