# Rough first draft of the DR / BDR election

[See RFC 2328 Section 9.4 p.75](https://www.rfc-editor.org/info/rfc2328/#page-75)

## Terms: 
thisRouter = this router

2wayNeighbors = the neighbors (this router currently has knowledge of) on this
network that have state 2Way or greater

possibleRouters = (2wayNeighbors + thisRouter) - (any routers with router
priority 0)

## Algorithm:

1. store current values of thisRouter.designated_router and 
thisRouter.backup_designated_router for later

2. calculate new BACKUP designated router from possibleRouters:
    1. filter out routers that have advertised themselves as DR
	  2. if one or more members of filtered possibleRouters have declared themselves as BDR, from among those routers:
		  - select the router with the highest router priority as BDR
		  - if there is a router priority tie, select router with highest router ID as BDR.
	  3. if no members of filtered possibleRouters have declared themselves as BDR:
		  - choose router with highest router priority from filtered possibleRouters as BDR
		  - if there is a router priority tie, select router with highest router ID as BDR.

3. calculate new actual designated router from possibleRouters:
	  1. if one or more members of possibleRouters have declared
		themselves as DR, from among those routers:
		  - select the router with the highest router priority as DR
		  - if there is a router priority tie, select router with highest
		router ID as DR.
	  2. if no members of possibleRouters have declared themselves
		as DR:
		  - select the router with the highest router priority as DR
		  - if there is a router priority tie, select router with highest
		  router ID as DR.

4. if thisRouter is now
	- newly selected Designated Router, or
	- newly selected Backup Designated Router, or
	- is no longer the Designated Router, or
	- is no longer the Backup Designated Router
	**then** repeat steps 2 and 3, then proceed to step 5

5. Check interface state for thisRouter based on results: thisRouter can now
be DR, BDR, or neither. This can cause interface state changes 
(see state diagrams, states DROther, Backup, and DR)

6. This is for non-broadcast multi-access networks, and out of our scope.

7. if the DR or BDR have changed as a result of these calculations, the set
of adjacencies associated with this interface will need to be modified. Use
the AdjOk? event on all neighbors whose state is at least 2-Way.
