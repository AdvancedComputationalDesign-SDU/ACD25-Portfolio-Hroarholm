"""
Assignment 4: Agent-Based Model for Surface Panelization
Author: Your Name

Agent Simulator Template

Description:
This file defines the structural outline for stepping and visualizing
agents within Grasshopper. No simulation logic is implemented. All behavior
(update, responding to signals, movement, etc.) must be
implemented inside your Agent class in `agent_builder.py`.

Note: This script is intended to be used within Grasshopper's Python
scripting component.
"""

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
        agent.step(step_size=step_size)

# --------------------------------------------------
# Main
# --------------------------------------------------

agent_points = []

for agent in agents:
    agent_points.append(agent.surface_point())


# --------------------------------------------------
# Outputs
# --------------------------------------------------

a = agents
b = agent_points