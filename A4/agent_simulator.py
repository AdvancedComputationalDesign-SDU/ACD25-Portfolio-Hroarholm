"""
Assignment 4: Agent Simulator (Minimal Pass Version)

Author: Hroar Holm Bertelsen

Description:
Updates agents over time using geometric signals:
- slope (heightmap gradient)
- separation (agent-agent spacing)
Outputs agent trajectories for panelization logic.
"""

# --------------------------------------------------
# Imports
# --------------------------------------------------

import Rhino.Geometry as rg
import scriptcontext as sc
import numpy as np
import math

# --------------------------------------------------
# Persistent storage (Grasshopper)
# --------------------------------------------------

if reset or not hasattr(sc.sticky, "agents"):
    sc.sticky["agents"] = agents

agents_sim = sc.sticky["agents"]

# --------------------------------------------------
# Freeze edge agents once
# --------------------------------------------------

for agent in agents:
    if agent.near_edge(edge_threshold):
        agent.frozen = True

# --------------------------------------------------
# Simulation loop
# --------------------------------------------------

for _ in range(iterations):
    for agent in agents:
        agent.step(
            agents,
            step_size=step_size,
            slope_weight=1.0,
            separation_weight=1.2,
            min_dist=min_dist
        )


# --------------------------------------------------
# Main
# --------------------------------------------------

agent_points = []

for agent in agents:
    agent_points.append(agent.surface_point())

trajectories = []

for agent in agents:
    if len(agent.trail) > 1:
        trajectories.append(rg.Polyline(agent.trail))

# --------------------------------------------------
# Outputs
# --------------------------------------------------

a = agents
b = agent_points
c = trajectories