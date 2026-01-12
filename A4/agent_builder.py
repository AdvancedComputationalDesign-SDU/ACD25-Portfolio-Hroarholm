"""
Assignment 4: Agent-Based Model for Surface Panelization
Author: Hroar Holm Bertelsen

Agent Builder script
"""

# --------------------------------------------------
# Imports
# --------------------------------------------------

import Rhino.Geometry as rg
import scriptcontext as sc
import random
import math

# --------------------------------------------------
# Normalize surface input to BrepFace
# --------------------------------------------------

if isinstance(surface, rg.Brep):
    brep = surface
elif isinstance(surface, rg.Surface):
    brep = rg.Brep.CreateFromSurface(surface)
else:
    brep = sc.doc.Objects.Find(surface).Geometry

# Assume single-face surface
face = brep.Faces[0]

# Cache domains
u_dom = face.Domain(0)
v_dom = face.Domain(1)

# --------------------------------------------------
# Agent class
# --------------------------------------------------

class Agent:
    def __init__(self, u, v, speed, face, u_dom, v_dom):
        # Normalized UV position
        self.u = u
        self.v = v

        self.face = face
        self.u_dom = u_dom
        self.v_dom = v_dom

        # Random initial velocity in UV space
        angle = random.uniform(0, 2 * math.pi)
        self.du = speed * math.cos(angle)
        self.dv = speed * math.sin(angle)

        self.alive = True

    def uv_position(self):
        return (self.u, self.v)

    def surface_point(self):
        """Map normalized UV to 3D surface point"""
        u_srf = self.u_dom.T0 + self.u * (self.u_dom.T1 - self.u_dom.T0)
        v_srf = self.v_dom.T0 + self.v * (self.v_dom.T1 - self.v_dom.T0)
        return self.face.PointAt(u_srf, v_srf)

    def sample_height(self):
        """Return height (Z) at agent location"""
        pt = self.surface_point()
        return pt.Z

    
# --------------------------------------------------
# Initialization
# --------------------------------------------------

random.seed(int(seed))

grid_u = int(math.sqrt(agent_count))
grid_v = grid_u

agents = []
agent_pts = []
agent_heights = []

for i in range(grid_u):
    for j in range(grid_v):
        if len(agents) >= agent_count:
            break

        u = float(i) / (grid_u - 1)
        v = float(j) / (grid_v - 1)

        agent = Agent(u, v, init_speed, face, u_dom, v_dom)
        agents.append(agent)

        agent_pts.append(agent.surface_point())
        agent_heights.append(agent.sample_height())

# --------------------------------------------------
# Outputs
# --------------------------------------------------

a = agents
b = agent_pts
c = agent_heights