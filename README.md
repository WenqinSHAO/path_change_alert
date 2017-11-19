# Online detection of RTT changes and congestion

## The demo
The repository provides a working demo/toy for this project.
It plots streaming RTT measurements collected from [RIPE Atlas](https://atlas.ripe.net) and marks the moment of change with a short delay.
The project is mainly built with python. R library *changpoint* is used to do the real detection. 
[bokeh](http://bokeh.pydata.org) is employed to plot streaming data.
The toy can be run by first executing the following command:
```
bokeh serve main.py  --address=0.0.0.0 --port=8080 --host='*'
```

If you are runing the project within a python virtual environment, use the following command:
 ```
 BOKEH_DEV=true BOKEH_RESOURCES=server-dev bokeh serve main.py  --address=0.0.0.0 --port=8080 --host='*'

```
Then visit this url [http://127.0.0.1:8080/main](http://127.0.0.1:8080/main) in you favorite browser.
![Example](/online_cpt.gif)

## Background and motivation
Network congestion is one major factor that impacts the transmission performance over the internet. 
It increases transmission delay and decreases goodput.

In order to avoid congestion, ones has to detect it in first place.
From an end host point of view, packet loss is a sign of congestion and triggers
TCP to slow down the transmission rate.
This approach doesn't avoid congestion. 
It rather controls the level of congestion before it goes wild.
Each participant TCP connection is supposed to get a fair/reasonable 
bandwidth portion of the shared link.
More demand there is, less resource each connection eventually gets.
It is because the total capacity remains the same.

While seen by a network operator, congestion can be avoided, 
as one can actually increase the allocable network capacity.
First, a network operator can augment the capacity of congested link, which
happens on a time scale of several months or even longer.
Second, a network operator can as well carefully plan the routing of traffic
 to make better use of currently available network capacity before next upgrade.

However, detecting congestion could be challenging from that a network operator perspective, 
when congestion happens outside one's network, somewhere in Internet.
In such case, the network operator lacks the bandwidth or queuing information that is
only locally available to deduce the the existence of remote congestion.

A part of the solution is already available. [1,2] proposed a method to detect
reoccurring congestion caused by under-provisioning using only RTT measurements.
Under the assumption that congestion is driving by the underlying traffic which has a diurnal
pattern, the method checks for a RTT time series whether it demonstrates as well such
 diurnal pattern via spectrum analysis. 

The shortcoming of this approach is two-fold: 1/ not being able to tell if currently 
the measured path is congested not; it analyzes RTT over a relatively long duration, say one week,
and tells if during this period there is congestion happens once per day; 
2/ the detection is not robust if the spectrum is
'polluted' by long term trends (e.g. path changes) or transient congestion.
Transient congestion mainly caused by traffic fluctuation apparently can not be timely detected by
this method.
Yet, it is not less harmful, as it is indeed more common and sometimes can dure quite long, say an entire day.
The pursuit of this project is therefore to explore the possible methods detecting
congestion, transient and reoccurring, in quasi real-time using mainly RTT measurements.
Once congestion is recognized right after its occurrence, network operators can make more
reactive and dynamic routing decisions to avoid the congested link, and offer better transmission quality.

## The approach
The occurrence of congestion changes the characters of RTT measurements.
Straightforwardly, congestion can be inferred by detecting such changes in RTT measurements.
### The signature of congestion in RTT
RTT measurements during congestion differ from normal cases in following two aspects.
First, the average RTT shall rise.
Over one same path, RTT is mainly decided by the queue length as the propagation delay remain unchanged.
During congestion, queue length naturally increases with the traffic demand and hence augments as well RTT.
Second, the variability of RTT shall as well increase. (why exactly?)
TCP overreacts to congestion on a microscopic time scale: increase sending rate util packet loss;
once packet lost, half the sending rate.
This puts the traffic demand in constant fluctuation which alters as well the queue length.
On the contrary, if un-congested, traffic is immediately consumed and therefore queue won't even establish.
The resulting RTT is thus very close to physical minimum and remain stable.
### Detect changes in RTT
Statistical tool *changepoint analysis* [3,4] can be leveraged to detect significant changes in RTT measurements.


## Reference
1. M. Luckie, A. Dhamdhere, D. Clark, B. Huffaker, and K. Claffy, “Challenges in Inferring Internet Interdomain Congestion,” in Proceedings of the 2014 Conference on Internet Measurement Conference - IMC ’14, 2014, pp. 15–22.
2. B. Chandrasekaran, A. Berger, and M. Luckie, “A Server-to-Server View of the Internet,” CoNext, 2015.
3. I. A. Eckley, P. Fearnhead, and R. Killick, “Analysis of Changepoint Models,” Bayesian Time Ser. Model., no. January, pp. 205–224, 2011.
4. R. Killick and I. Eckley, “changepoint: An R Package for changepoint analysis,” Lancaster Univ., vol. 58, no. 3, pp. 1–15, 2013.