(open for discussion)
# Objective
RTT as a performance indicator is of crucial importance for content and service delivery.
Congestion and routing changes are fundamental causes for RTT variation.
In order to have a continuous view on the Internet routing changes (from a date-plane perspective) and their consequence on RTT,
this project aims at detecting inter- and intra-domain routing changes for Atlas traceroute measurements streams.

# Interface
The interface allows one to subscribe to a traceroute measurement stream
and be informed of the moments and AS where the forwarding IP path experienced change due to inter- or intra-domain routing events.

# Approach
## Inter-domain routing change
Inter-domain routing changes are reflected in AS path changes.
In order to detect this kind of routing changes, it requires to first map IP hop to AS hop and then construct AS path.
Then change in AS path is detected.
In order to pinpoint the root cause for the observed change, BGP updates from RIPE RIS can as well be employed.
[Poiroot](http://www-bcf.usc.edu/~katzbass/papers/poiroot-sigcomm2013.pdf) is one of the stat-of-the-art research on this problem.

## Intra-domain routing change
Due to the presence of load balancing (LB), the forwarding path between a src-dst pair can change even when there is no routing change.
According to the publication giving birth to [Tokyo ping](http://conferences.sigcomm.org/imc/2013/papers/imc125s-pelsserA.pdf), the RTT difference across different flow-ids could reach 20msec.
It is then interesting to separate the IP path changes caused by intra-domain routing change and those due to LB.
We can infer inter-domain routing changes by detecting the change on IP paths associated to a same flow-id.

# Existing project
A previous award-wining projects [BGP traceroutes](https://github.com/wires/bgp-traceroutes.git) and [Traceroute-consistency-check](https://github.com/vdidonato/Traceroute-consistency-check) could be of use in constructing this project.

# Future extension
One promising extension is to first detect the moment of major RTT changes for streaming ping measurements.
The added-value compared to current [LatencyMoon](https://labs.ripe.net/Members/massimo_candela/new-ripe-atlas-tool-latencymon) is that one can be informed of RTT changes of statistical significance.
One online changepoint detection implementation is available here: [Bayesian Changepoint Detection](https://github.com/hildensia/bayesian_changepoint_detection.git).

Further, we can correlate the RTT changes with path changes to estimate, for individual case and group of src-dst pairs, the impact of routing changes on RTT.
