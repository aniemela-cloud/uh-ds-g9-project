# State Diagrams Used By The Nodes

## Interface States

The state diagram describes the states a network interface can be in.

```mermaid
---
title: Interface State Diagram
config:
    layout: dagre
---
stateDiagram-v2
    state "Point-to-point" as ptp
    state ptp_or_multicast <<choice>>
    state select <<choice>>

    [*] --> Down
    Loopback --> Down : UnloopInd
    Down --> ptp_or_multicast : InterfaceUp
    ptp_or_multicast --> Multicast : Multicast
    ptp_or_multicast --> ptp : Point-to-point
    state "Multicast operation" as Multicast {
        [*] --> Waiting
        Waiting --> select : WaitTimer / BackupSeen
%%    select --> fork_state
        select --> Backup
        Backup --> select : NeighborChange
        select --> DROther
        DROther --> select : NeighborChange
        select --> DR
        DR --> select : NeighborChange
    }
```
_Note: Events __InterfaceDown__ and __LoopInd__ have been omitted from the diagram for clarity. 
These events are possible in any state. Event InterfaceDown changes the interface state to Down, event 
LoopInd changes the interface state to Loopback._

### Description of Interface States

_(Paraphrased or copied from RFC2328 Section 9.1)_

#### Down

The initial interface state. Shows that the interface is currently unusable.
No protocol traffic will be sent or received on such an interface. In this state,
interface parameters should be set to their initial values. All interface timers
should be disabled, and there should be no adjacencies associated with the interface.

#### Loopback

The router's interface to the network is looped back. The interface will be unavailable for
regular data traffic.

#### Point-to-point

In this state, the interface is operational, and connects either to a physical point-to-point
network or to a virtual link. Upon entering this state, the router attempts to form
an adjacency with the neighboring router.  Hello Packets are sent to the neighbor every HelloInterval seconds.

#### Waiting

In this state, the router is trying to determine the identity of the (Backup) Designated Router
for the network. To do this, the router monitors the Hello Packets it receives.  The router is not
allowed to elect a Backup Designated Router nor a Designated Router until it transitions out of Waiting
state.  This prevents unnecessary changes of (Backup) Designated Router.

#### DR Other

The interface is to a broadcast or NBMA network on which another router has been selected to be
the Designated Router.  In this state, the router itself has not been selected Backup Designated Router
either.  The router forms adjacencies to both the Designated Router and the Backup Designated Router
(if they exist).

#### Backup

In this state, the router itself is the Backup Designated Router on the attached network.
It will be promoted to Designated Router when the present Designated Router fails. The router 
establishes adjacencies to all other routers attached to the network.  The Backup Designated 
performs slightly different functions during the Flooding Procedure, as compared to the
Designated Router (see RFC2328 Section 13.3).  

See RFC2328 Section 7.4 for more details on the functions performed by the Backup Designated Router.

#### DR

In this state, this router itself is the Designated Router on the attached network.
Adjacencies are established to all other routers attached to the network.  The router must originate
a network-LSA for the network node.  The network-LSA will contain links to all routers (including the
Designated Router itself) attached to the network.  See RFC2328 Section 7.3 for more details on the
functions performed by the Designated Router.

### Events Causing Interface State Changes

#### InterfaceUp

Lower-level protocols have indicated that the network interface is operational.  This enables the
interface to transition out of Down state. _(In our case we bring the interface up when a socket has been successfully bound, --Antti)_

#### WaitTimer

The Wait Timer has fired, indicating the end of the waiting period that is required before 
electing a (Backup) Designated Router.

#### BackupSeen

The router has detected the existence or non-existence of a Backup Designated Router for the
network.  This is done in one of two ways.  First, an Hello Packet may be received from a neighbor
claiming to be itself the Backup Designated Router.  Alternatively, an Hello Packet may be
received from a neighbor claiming to be itself the Designated Router, and indicating that there
is no Backup Designated Router.  In either case there must be bidirectional communication with
the neighbor, i.e., the router must also appear in the neighbor's Hello Packet.  This event signals
an end to the Waiting state.

#### NeighborChange

There has been a change in the set of bidirectional neighbors associated with the interface.
The (Backup) Designated Router needs to be recalculated.  The following neighbor changes lead
to the NeighborChange event.  For an explanation of neighbor states, see RFC2328 Section 10.1.

- Bidirectional communication has been established to  neighbor.  In other words, the state
of the neighbor has transitioned to 2-Way or higher.
- There is no longer bidirectional communication with a neighbor.  In other words, the state
of the neighbor has transitioned to Init or lower.
- One of the bidirectional neighbors is newly declaring itself as either Designated Router or
Backup Designated Router.  This is detected through examination of that neighbor's Hello Packets.
- One of the bidirectional neighbors is no longer declaring itself as Designated Router, or
is no longer declaring itself as Backup Designated Router.  This is again detected through
examination of that neighbor's Hello Packets.
- The advertised Router Priority for a bidirectional neighbor has changed.  This is again
detected through examination of that neighbor's Hello Packets.

#### LoopInd

An indication has been received that the interface is now looped back to itself.  This
indication can be received either from network management or from the lower level protocols.

#### UnloopInd

An indication has been received that the interface is no longer looped back.  As with the
LoopInd event, this indication can be received either from network management or from the 
lower level protocols.

#### InterfaceDown

Lower-level protocols indicate that this interface is no longer functional.  No matter 
what the current interface state is, the new interface state will be Down.

### Detailed Description of Interface State Changes

#### State: Down

> ##### Event: InterfaceUp
>
> **New State:** Depends upon action routine
>
> **Action:** Start the interval **Hello Timer**, enabling the periodic sending of Hello
> packets out of the interface. If the attached network is a physical point-to-point
> network, Point-to-MultiPoint network or virtual link, the interface state transitions
> to **Point-to-Point**. Else, if the Router is _not eligible_ to become Designated
> Router the interface transitions to **DR Other**.
>
> Otherwise, the attached network is a broadcast or NBMA network and the router is
> eligible to become Designated Router.  In this case, in an attempt to discover the
> attached network's Designated Router the interface state is set to **Waiting** and the
> single shot **Wait Timer** is started.  Additionally, if the network is an NBMA network
> examine the configured list of neighbors for this interface and generate the
> neighbor event Start for each neighbor that is also eligible to become Designated
> Router.

#### State: Waiting

> ##### Event: BackupSeen
>
> **New State:** Depends upon action routine
>
> **Action:** Calculate the attached network's Backup Designated Router and
> Designated Router, as shown in RFC2328 Section 9.4.  As a result of this
> calculation, the new state of the interface will be either **DR Other**, **Backup**
> or **DR**.

> ##### Event: WaitTimer
> 
> **New State:** Depends upon action routine
>
> **Action:** Calculate the attached network's Backup Designated Router and
> Designated Router, as shown in RFC2328 Section 9.4.  As a result of this
> calculation, the new state of the interface will be either **DR Other**, **Backup**
> or **DR**.

#### State: DR Other, Backup or DR

> ##### Event: NeighborChange
>
> **New State:** Depends upon action routine
>
> **Action:** Recalculate the attached network's Backup Designated Router and
> Designated Router, as shown in RFC2328 Section 9.4.  As a result of this
> calculation, the new state of the interface will be either **DR Other**, **Backup**
> or **DR**.

#### State: Any state

> ##### Event: InterfaceDown
>
> **New State:** Down
>
> **Action:** All interface variables are reset, and interface timers disabled.
> Also, all neighbor connections associated with the interface are destroyed.
> This is done by generating the event KillNbr on all associated neighbors (see
> RFC2328 Section 10.2).

> ##### Event: LoopInd
> 
> **New State:** Loopback
>
> **Action:** Since this interface is no longer connected to the attached network
> the actions associated with the above **InterfaceDown** event are executed.

#### State: Loopback

> ##### Event: UnloopInd
>
> **New State:** Down
>
> **Action:** No actions are necessary.  For example, the interface variables have
> already been reset upon entering the **Loopback** state. Note that reception of an
> InterfaceUp event is necessary before the interface again becomes fully functional.

## Neighbor States

The diagram describes the states a neighbor (or the state of a conversation being
held with a neighboring router) can have and their transitions. The states are 
considered to be ordered according to progressive functionality. When documentation
refers to a neighbor's state being "greater than" or "less than" something, refer to
the order the events are listed in the section **Descriptions of Neighbor States**.

```mermaid
---
title: Neighbor State Diagram (Hello Protocol)
---
stateDiagram-v2
    state "2-Way" as 2Way
    state select <<choice>>
    [*] --> Down
    Down --> Attempt : Start
    Down --> Init : HelloReceived
    Attempt --> Init: HelloReceived
    Init --> select : 2-Way Received
    select --> ExStart
    select --> 2Way
    2Way --> Init : 1-Way Received
```
_In addition to the state transitions pictured, Event KillNbr always forces Down
State, Event InactivityTimer always forces Down State, Event LLDown always forces
Down State_

Additionally, the **ExStart** state leads to the Neighbor States of the database
exchange process performed when neighbors count as adjacent. _(Note that this means
a neighbor is considered adjacent when it's state is one of the states shown in the
diagram below. --Antti)_

```mermaid
---
title: Neighbor State Diagram (Database Exchange)
---
stateDiagram-v2
    state ex_select <<choice>>
    [*] --> ExStart
    ExStart --> Exchange : NegotiationDone
    Exchange --> ex_select : ExchangeDone
    ex_select --> Full
    ex_select --> Loading
    Loading --> Full : LoadingDone    
```
_In addition to the state transitions pictured,_
- _Event SeqNumberMismatch forces ExStart state,_
- _Event BadLSReq forces ExStart state,_
- _Event 1-WayReceived forces Init state,_
- _Event KillNbr always forces Down State,_
- _Event InactivityTimer always forces Down State,_
- _Event LLDown always forces Down State,_
- _Event AdjOK? leads to adjacency forming/breaking_
  
### Descriptions of Neighbor States

_(Paraphrased or copied from RFC2328 Section 9.1)_

#### Down

This is the initial state of a neighbor conversation.  It indicates that there has
been no recent information received from the neighbor.  On NBMA networks, Hello 
packets may still be sent to "Down" neighbors, although at a reduced frequency (see 
RFC2328 Section 9.5.1).

#### Attempt

This state is only valid for neighbors attached to NBMA networks.  It indicates that
no recent information has been received from the neighbor, but that a more concerted 
effort should be made to contact the neighbor.  This is done by sending the neighbor 
Hello packets at intervals of HelloInterval (see RFC2328 Section 9.5.1).

#### Init

In this state, an Hello packet has recently been seen from the neighbor.  However,
bidirectional communication has not yet been established with the neighbor (i.e., the
router itself did not appear in the neighbor's Hello packet).  All neighbors in this 
state (or higher) are listed in the Hello packets sent from the associated interface.

#### 2-Way

In this state, communication between the two routers is bidirectional.  This has been
assured by the operation of the Hello Protocol.  This is the most advanced state short
of beginning adjacency establishment.  The (Backup) Designated Router is selected from
the set of neighbors in state 2-Way or greater. 

#### ExStart

This is the first step in creating an adjacency between the two neighboring routers.
The goal of this step is to decide which router is the master, and to decide upon the 
initial DD sequence number.  Neighbor conversations in this state or greater are called
adjacencies.

#### Exchange

In this state the router is describing its entire link state database by sending
Database Description packets to the neighbor.  Each Database Description Packet has a
DD sequence number, and is explicitly acknowledged.  Only one Database Description 
Packet is allowed outstanding at any one time.  In this state, Link State Request
Packets may also be sent asking for the neighbor's more recent LSAs. All adjacencies
in Exchange state or greater are used by the flooding procedure.  In fact, these a
djacencies are fully capable of transmitting and receiving all types of OSPF 
routing protocol packets.

#### Loading

In this state, Link State Request packets are sent to the neighbor asking for the 
more recent LSAs that have been discovered (but not yet received) in the Exchange 
state.

#### Full

In this state, the neighboring routers are fully adjacent. These adjacencies 
will now appear in router-LSAs and network-LSAs.

### Events Causing Neighbor State Changes

#### HelloReceived

An Hello packet has been received from the neighbor.

#### Start

This is an indication that Hello Packets should now be sent to the neighbor at
intervals of HelloInterval seconds.  This event is generated only for neighbors
associated with NBMA networks.

#### 2-WayReceived

Bidirectional communication has been realized between the two neighboring 
routers.  This is indicated by the router seeing itself in the neighbor's Hello
packet.

#### NegotiationDone

The Master/Slave relationship has been negotiated, and DD sequence numbers have
been exchanged.  This signals the start of the sending/receiving of Database 
Description packets.  For more information on the generation of this event, 
consult RFC 2328 Section 10.6.

#### ExchangeDone

Both routers have successfully transmitted a full sequence of Database 
Description packets.  Each router now knows what parts of its link state 
database are out of date.  For more information on the generation of this 
event, consult RFC 2328 Section 10.8.

#### BadLSReq

A Link State Request has been received for an LSA not contained in the 
database.  This indicates an error in the Database Exchange process.

#### LoadingDone

Link State Updates have been received for all out-of-date portions of the 
database.  This is indicated by the Link state request list becoming empty 
after the Database Exchange process has completed. 

#### AdjOk?

A decision must be made as to whether an adjacency should be 
established/maintained with the neighbor.  This event will start some 
adjacencies forming, and destroy others. 

_The following events cause well developed neighbors to revert to lesser 
states.  Unlike the above events, these events may occur when the neighbor
conversation is in any of a number of states._

#### SeqNumberMismatch

A Database Description packet has been received that either 
1. has an unexpected DD sequence number, 
2. unexpectedly has the Init bit set or 
3. has an Options field differing from the last Options field received in a 
Database Description packet.

Any of these conditions indicate that some error has occurred during adjacency
establishment.

#### 1-WayReceived

An Hello packet has been received from the neighbor, in which the router is not
mentioned.  This indicates that communication with the neighbor is not 
bidirectional.

#### KillNbr

This is an indication that all communication with the neighbor is now 
impossible, forcing the neighbor to revert  to Down state.

#### InactivityTimer

The inactivity Timer has fired.  This means that no Hello packets have been 
seen recently from the neighbor.  The neighbor reverts to Down state.

#### LLDown

This is an indication from the lower level protocols that the neighbor is now
unreachable.  For example, on an X.25 network this could be indicated by an
X.25 clear indication with appropriate cause and diagnostic fields.  This event
forces the neighbor into Down state.

### Detailed Description of Neighbor State Changes

#### State: Down

> ##### Event: Start
>
> **New State:** Attempt
>
> **Action:** Send an Hello Packet to the neighbor (this neighbor is always 
> associated with an NBMA network) and start the Inactivity Timer for the
> neighbor.  The timer's later firing would indicate that communication 
> with the neighbor was not attained.

#### State: Attempt

> ##### Event: HelloReceived
> 
> **New State:** Init
>
> **Action:** Restart the Inactivity Timer for the neighbor, since
> the neighbor has now been heard from.

#### State: Down

> ##### Event: HelloReceived
> 
> **New State:** Init
>
> **Action:** Restart the Inactivity Timer for the neighbor. The
> timer's later firing would indicate that the neighbor is dead.

#### States: Init or Greater

> ##### Event: HelloReceived
>
> **New State:** No state change.
>
> **Action:** Restart the Inactivity Timer for the neighbor, since
> the neighbor has again been heard from.

#### State: Init

> ##### Event: 2-WayReceived
>
> **New State:** Depends upon action routine.
>
> **Action:** Determine whether an adjacency should be established
> with the neighbor (see RFC2328 Section 10.4).  If not, the
> new neighbor state is **2-Way**.
>
> If an adjacency should be established, the neighbor state transitions
> to **ExStart**. Upon entering this state, the router increments the DD
> sequence number in the neighbor data structure.  If this is the first time
> that an adjacency has been attempted, the DD sequence number should be
> assigned some unique value (like the time of day clock).  It then declares
> itself master (sets the master/slave bit to master), and starts sending
> Database Description Packets, with the initialize (I), more (M) and
> master (MS) bits set.  This Database Description Packet should be otherwise
> empty.  This Database Description Packet should be retransmitted at
> intervals of RxmtInterval until the next state is entered
> (see RFC 2328 Section 10.8).


#### State: ExStart

> ##### Event: NegotiationDone
>
> **New State:** Exchange
>
> **Action:** Out of scope for this project, details found in
> [RFC 2328 Section 10.3 p.91](https://www.rfc-editor.org/info/rfc2328/#page-91)

#### State: Exchange

> ##### Event: ExchangeDone
>
> **New State:** Depends upon action routine.
>
> **Action:**  Out of scope for this project, details found in
> [RFC 2328 Section 10.3 p.92](https://www.rfc-editor.org/info/rfc2328/#page-92)

#### State: Loading

> ##### Event: LoadingDone
>
> **New State:** Full
>
> **Action:** No action required. This is an adjacency's final state.

#### State: 2-Way

> ##### Event: AdjOk?
>
> **New State:** Depends upon action routine.
>
> **Action:**  Determine whether an adjacency should be formed with the neighboring router
> (see [RFC2328 Section 10.4 p.95](https://www.rfc-editor.org/info/rfc2328/#page-95)).  If not,
> the neighbor state remains at 2-Way.
> Otherwise, transition the neighbor state to ExStart and perform the actions
> associated with the above state machine entry for state Init and event
> 2-WayReceived.

#### States: ExStart or greater

> ##### Event: AdjOk?
>
> **New State:** Depends upon action routine.
>
> **Action:** Determine whether the neighboring router should still be adjacent.
> If yes, there is no state change and no further action is necessary.
> 
> Otherwise, the (possibly partially formed) adjacency must be destroyed.  The
> neighbor state transitions to 2-Way.  The Link state retransmission list,
> Database summary list and Link state request list are cleared of LSAs.

#### States: Exchange or greater

> ##### Event: SeqNumberMismatch
>
> **New State:** ExStart
>
> **Action:** Out of scope for this project, details found in
> [RFC 2328 Section 10.3 p.93](https://www.rfc-editor.org/info/rfc2328/#page-93)

#### States: Exchange or greater

> ##### Event: BadLSReq
>
> **New State:** ExStart
>
> **Action:** Out of scope for this project, details found in
> [RFC 2328 Section 10.3 p.93](https://www.rfc-editor.org/info/rfc2328/#page-93)

#### States: Any state

> ##### Event: KillNbr
>
> **New State:** Down
>
> **Action:** The Link state retransmission list, Database summary list and
> Link state request list are cleared of LSAs.  Also, the Inactivity
> Timer is disabled.

> ##### Event: LLDown
>
> **New State:** Down
>
> **Action:** The Link state retransmission list, Database summary list and
> Link state request list are cleared of LSAs.  Also, the Inactivity
> Timer is disabled.

> ##### Event: InactivityTimer
>
> **New State:** Down
>
> **Action:** The Link state retransmission list, Database summary list and
> Link state request list are cleared of LSAs.  Also, the Inactivity
> Timer is disabled.

#### State: 2-Way or Greater

> ##### Event: 1-WayReveived
>
> **New State:** Init
>
> **Action:** The Link state retransmission list, Database summary list and
> Link state request list are cleared of LSAs.  Also, the Inactivity
> Timer is disabled.

> ##### Event: 2-WayReveived
>
> **New State:** No state change.
>
> **Action:** No action required.

#### State: Init

> ##### Event: 1-WayReveived
>
> **New State:** No state change.
>
> **Action:** No action required.
