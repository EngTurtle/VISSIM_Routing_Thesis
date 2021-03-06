# Micro-Simulation of Autonomous Ride-Sharing Route Choice

As ride-sharing services [1] and autonomous vehicles [2] gain market share in the road transportation market, so does the possibility of these services utilizing centralized route planning for large regions. Where as currently, most drivers independently choose their route to minimize their travel time. One of the key advantages of centralized route planning is the ability to enforce route choice on the controlled vehicles. This is will allow for vehicles to travel in routes closer to System Equilibrium (SE) rather than the current User Equilibrium (UE) [3]. However, as ride-sharing providers are private entities, they would not have the incentive to minimize total travel time for the whole road network, as is done in classic SE, but only optimize for the total travel time of their fleet.

Prior research has analysed the interaction between UE and SE routing through the use of Advanced Traveller Information Systems [4] and Connected vehicle systems [5]. However, the previous research all assumed a person will make the final route choice decision, which requires concessions towards UE routing. This is not a necessary assumption if level 4+ autonomous vehicles [6] are used, as all driving operations will be under computer control. Additionally, the SE routing in previous research optimizes total travel time for whole network, not for just a subset of vehicles. This indicate a gap in using existing traffic routing models to predict traffic patterns in the coming decades.

My primary goal is to address this gap by determining the road network levels of service under automated ride-sharing route planning at various levels of market share, by using micro-simulation of road traffic. Additionally, my secondary goal will be to analyze the interaction of multiple centralized route planners in the same micro-simulation network, to predict the effects of multiple ride sharing companies competing in the same city.

This will be accomplished through the following steps. Firstly, I will conduct a literature review of existing research on UE vs SE routing. Then I will determine a method to calculate marginal cost for a subset of vehicles. Afterwards, I will program a route assignment system for dynamically assigning UE, SE, or automated ride-sharing routes. UE routes will be computed for minimal travel time, SE routes will be computed for minimal marginal cost on the network, and automated ride-sharing routes will be computed for minimal marginal cost for the fleet under its control. Then I will construct a small test road network in simulation. The route assignment system will be run on the test network to determine if there is a difference in level of service between whole system equilibrium vs optimizing for a subset of vehicles. Once experiments on the small test network is complete, the route assignment system will be applied to a simulated road network of Toronto (or a large region of), where the effects of automated ride-sharing route planning will be determined at different market share. And if time permits, I will create a more advanced route assignment system for simulating multiple independent automated ride-sharing route planners and observe its effects on the simulated Toronto network.

The results of this research will help predict the effect of ride sharing and autonomous vehicle growth on city road networks. In addition, the methods developed will assist ride sharing companies in choosing the best routing algorithm for their future fleets of autonomous vehicles.

## References

|  |  |
|-----|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [1] | Daedal Research, "Global Ride-Sharing Market: Size, Trends & Forecast (2018-2022)," Research and Markets, Global, 2018. |
| [2] | Catapult Transport Systems, "Market Forecast for Connected and Autonomous Vehicles," Government of United Kingdom, 2017. |
| [3] | J. G. Wardrop, "Some theoretical aspects of road traffic research.," Inst Civil Engineers Proc London/UK/, pp. Part Ii, VoL 1, 2, PP 325-378, 1952. |
| [4] | P. D. Site, "A mixed-behaviour equilibrium model under predictive and static Advanced Traveller Information Systems (ATIS) and state-dependent route choice," Transportation Research Part C-emerging Technologies, vol. 86, no. , pp. 549-562, 2018.  |
| [5] | L. . Du, L. . Han and S. . Chen, "Coordinated online in-vehicle routing balancing user optimality and system optimality through information perturbation," Transportation Research Part B-methodological, vol. 79, no. , pp. 121-133, 2015.  |
| [6] | SAE International, Taxonomy and Definitions for Terms Related to Driving Automation Systems for On-Road Motor Vehicles, SAE International, 2018.  |
| [7] | H. . Yang and Q. . Meng, "Departure time, route choice and congestion toll in a queuing network with elastic demand," Transportation Research Part B-methodological, vol. 32, no. 4, pp. 247-260, 1998.  |

Copyright 2021 Oliver Liang

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
