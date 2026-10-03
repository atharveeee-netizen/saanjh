# SAANJH Digital Twin — Event Narrative Script

**00:00 - 00:10 | Hero Neighbourhood**
"This is a SAANJH-enabled neighbourhood distribution network. It is currently operating within normal parameters. The 100 kVA distribution transformer is handling steady baseline load."

**00:10 - 00:25 | Network Overview**
"We are looking at 60 individual households. 66% of these homes are equipped with rooftop solar and local battery storage, actively generating and consuming energy behind the meter."

**00:25 - 00:40 | Normal Operation**
"During the afternoon, solar generation meets local demand, and excess energy charges the household batteries. The feeder stress remains low, and the network operates comfortably below rating."

**00:40 - 00:55 | Solar Decline**
"As evening approaches, solar generation begins to decline. Simultaneously, residential demand naturally increases as families return home and evening activities commence."

**00:55 - 00:70 | Forecast Warning**
"At this point, the SAANJH predictive engine, powered by our real-data-trained XGBoost model, detects an impending anomaly. It forecasts that the feeder will exceed its thermal rating within the next 30 minutes."

**00:70 - 00:90 | Virtual Battery**
"Without SAANJH, the DISCOM would experience an outage or extreme transformer degradation. Instead, the SAANJH Edge Gateway begins communicating via LoRa to the active nodes, aggregating their available flexibility into a single Virtual Battery."

**00:90 - 01:15 | Dispatch**
"The stress event arrives. The network transitions into an active dispatch state. The control UI indicates that the required flexibility is being deployed. Selected homes intelligently discharge their batteries into the network, dynamically compensating for the missing solar power."

**01:15 - 01:35 | Transformer Relief**
"Observe the transformer stress visualization. The injected flexibility drops the peak demand on the transformer from a critical overload state back down to a safe operating band. The heatmap cools."

**01:35 - 01:50 | Recovery**
"As the evening peak subsides, the stress event concludes. The participating households exit dispatch mode and enter a staggered recovery phase, preventing a secondary rebound peak."

**01:50 - 02:10 | Baseline vs SAANJH**
"The final metrics confirm the operation. SAANJH successfully mitigated the transformer overload, proving that distributed flexibility can dynamically protect grid infrastructure without requiring expensive hardware upgrades."

**02:10 - 02:16 | Final Hero Shot**
"SAANJH: Securing the edge, one neighbourhood at a time."
