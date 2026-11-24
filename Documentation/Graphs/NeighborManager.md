# Neighbor Manager
## Updating Neighbors based on received Hello message

## Events

```mermaid
---
title: 
---
flowchart TB
    style C fill:#0F0
    style D fill:#0F0
    style E fill:#0F0
    style F fill:#0F0
    style G fill:#0F0
    A([ReceivedMessage])
    B([Validate])
    C([HelloReceived])
    D([BackupSeen])
    E([2-WayReceived])
    F([1-WayReceived])
    G([NeighborChange])
    H([Kill])

    A-->B
    B-->C
    C-->D
    C-->E
    E-->G
    E-->F
    C-->F
```

## Pseudocode

    NB=neighbor whose message is processed
    ME=Receiving NetworkInterface

    Receive message

    if ME.InterfaceState.(DOWN | LOOPBACK | POINTTOPOINT):
    #Messages are not processed in these states
    #Loopback and point-to-point not included in our project
        Drop packet
        Exit


    Validate message
        IP headers:
            IP checksum
            Destination = ME.IP/ME.Destination
            IP protocol = OSPF = 89
        OSPF headers:
            Version = 2
            AreaID = ME.area_id
            IPdestination = AllDRouters #Routing related if ME is DR or BDR
            AuType = #Not included
            Authentication #Not included
            


    if MESSAGE.type == 1 #Hello
    >>> EVENT HelloReceived

        if NB.Network Mask, NB.HelloInterval, and NB.RouterDeadInterval are not same as ME...:
            drop packet
                Exit


    if ME.InterfaceState.WAITING and ((NB.id=NB.DR and NB.BDR=0) or (NB.id=NB.BDR)) :
    >>> EVENT BackupSeen	


    if (ME.id in NB.Neighbor-list):
    >>> EVENT 2-WayReceived. 

        #case NEW neighbor_ID:
        if neighbor_id not in ME.neighbors-list:
            create Neighbor instance #State is DOWN by default

        #Update that routers know each other
        if ME.NeighborState.(INIT | DOWN): 
            Set NB.NeighborState.TWOWAY


        #Priority has changed
        if NB.OLD_priority is not NB.NEW_priority:
    >>> EVENT NeighborChange

        #If neighbor was BDR or DR and says it is not anymore, or opposite
        if ((NB.OLD_DR is not NB.NEW_DR) and ((NB.OLD_DR=NB) or (NB.NEW_DR=NB))) or
        ((NB.OLD_BDR is not NB.NEW_BDR) and ((NB.OLD_BDR=NB) or (NB.NEW_BDR=NB))):
    >>> EVENT NeighborChange


        #Neighbor has differrent DR or BDR than me
        if (NB.BDR != ME.BDR) or (NB.DR != ME.DR):
    >>> EVENT NeighborChange (NOT defined in RFC)



        else (ME.id not in NB.Neighbor-list):
    >>> EVENT 1-WayReceived. 
        #Update state
        Set NeighborState.INIT
        If NB.id was ME.DR or ME.BDR:
        >>> EVENT NeighborChange (NOT defined in RFC)

        Exit #No need to process because 1ways are ignored in voting


## Process flow

```mermaid
---
title: Process flow
---
flowchart TB
    A([ReceivedMessage])
    style A fill:#0F0
    B([Validating 8.2])

    C1([New NeighborID])
    C2([Known NeighborID])

    I1[InterfaceState.WAITING]
    style I1 fill:#CCC
    I2[InterfaceState.DR/BR/OTHER]
    style I2 fill:#CCC
    I3[InterfaceState.DOWN]
    style I3 fill:#CCC

    R([Exit])

    D1([Has DR/BR])
    D2([No DR/BR])
    E1(((Create Neighbor)))
    style E1 fill:#0FF


    F1([Stop WaitTimer])
    F2(((Run Election)))
    style F2 fill:#FF0
    F3([Set InterfaceState.OTHER])

    J1([MyID on list])
    J2([MyID NOT on list])
    L1([Set NeighborState.INIT])
    L2([Set NeighborState.2WAY])

    G1[InterfaceState.DR/BR/OTHER]
    style G1 fill:#CCC

    H1([CheckChanges])
    K1([MyID on list])
    K2([MyID NOT on list])
    M1([Is now or not anymore DR/BR])
    N1([Priority changed])
    O1([Different DR/BR than mine])
    S1([Other changes, TTL])

    P1(((Update Neighbor)))
    style P1 fill:#0FF

    A---B
    A---I3
    I3---R
    B---C1
    B---C2
    C1---I1
    I1---D1
    I1---D2
    C1---I2
    I2---J2
    I2---J1
    J1===E1
    J1---L2
    J2===E1
    J2---L1
    D2===E1
 
    D1---F1
    D1---F2
    D1---F3
    D1===E1
    C2---G1
    G1---H1
    H1---K2
    K1---L2
    H1---K1
    K2---L1

    H1---M1
    H1---N1
    H1---O1
    H1---S1
    M1---F2
    N1---F2
    O1---F2

    M1===P1
    N1===P1
    O1===P1
    K1===P1
    K2===P1
    S1===P1

```