(open for discussion)
# Objective
In order to have a continous view on the Internet data-plane dyanmics,
this project aims at detecting inter- and intra-domain routing changes for built-in Atlas traceroute measurements.

# Interface
The interface allows one to subscribe to a traceroute measurement stream.
One is then informed of the moments and AS where the forwarding IP path experienced change due to inter- or intra-domain routing events.

# Approach
## Inter-domain routing change
Inter-domain routing changes are refelcted in AS path changes.
In order to detect this kind of routing changes, it requires to first map IP hop to AS hop and then construct AS path.

## Intra-domain routing change
IP path change due to load balancing and intra-domain routing change should be distinguished.
The later can be inferred by detecting IP patch changes of same flow-id.

# Existing project
A previsou award-wining project [Traceroute-consistency-check](https://github.com/vdidonato/Traceroute-consistency-check) could be of use in constructing this project.

# Future extension
One possibility is to first detect major RTT changes for streaming ping measurements and then correlate RTT changes and routing events for a same source destination pair.
The results are expected to 1/ provider real-time alert for RTT changes of statistical significance; 2/ reveal the contribution of routing events to RTT variation.
