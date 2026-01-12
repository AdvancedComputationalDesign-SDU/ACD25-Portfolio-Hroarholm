"""
Assignment 4: Agent-Based Model for Surface Panelization
Author: Hroar Holm Bertelsen

Agent Builder script
"""

import Rhino.Geometry as rg
import scriptcontext as sc
import math

# --------------------------------------------------
# Normalize surface to BrepFace
# --------------------------------------------------

if isinstance(surface, rg.Brep):
    brep = surface
elif isinstance(surface, rg.Surface):
    brep = rg.Brep.CreateFromSurface(surface)
else:
    brep = sc.doc.Objects.Find(surface).Geometry

face = brep.Faces[0]
u_dom = face.Domain(0)
v_dom = face.Domain(1)

# --------------------------------------------------
# Agent class (NO BEHAVIOR)
# --------------------------------------------------

class Agent:
    def __init__(self, u, v, face, u_dom, v_dom):
        self.u = u
        self.v = v
        self.face = face
        self.u_dom = u_dom
        self.v_dom = v_dom

    def surface_point(self):
        u_srf = self.u_dom.T0 + self.u * (self.u_dom.T1 - self.u_dom.T0)
        v_srf = self.v_dom.T0 + self.v * (self.v_dom.T1 - self.v_dom.T0)
        return self.face.PointAt(u_srf, v_srf)

    def slope_direction_uv(self, eps=0.01):
        """
        Approximate slope direction in UV space using finite differences.
        Returns a 2D vector (du, dv).
        """

        # Clamp UV to avoid domain issues
        u0 = max(0.0, min(1.0, self.u))
        v0 = max(0.0, min(1.0, self.v))

        # Offset samples
        u1 = min(1.0, u0 + eps)
        v1 = min(1.0, v0 + eps)

        # Map to surface domain
        U0 = self.u_dom.T0 + u0 * (self.u_dom.T1 - self.u_dom.T0)
        V0 = self.v_dom.T0 + v0 * (self.v_dom.T1 - self.v_dom.T0)
        U1 = self.u_dom.T0 + u1 * (self.u_dom.T1 - self.u_dom.T0)
        V1 = self.v_dom.T0 + v1 * (self.v_dom.T1 - self.v_dom.T0)

        # Sample points
        p = self.face.PointAt(U0, V0)
        pu = self.face.PointAt(U1, V0)
        pv = self.face.PointAt(U0, V1)

        # Height differences
        dz_du = pu.Z - p.Z
        dz_dv = pv.Z - p.Z

        return (dz_du, dz_dv)

    def distance_to(self, other):
        """3D distance between this agent and another agent"""
        p1 = self.surface_point()
        p2 = other.surface_point()
        return p1.DistanceTo(p2)    

    def edge_distance(self):
        """
        Returns the minimum normalized distance to any surface edge.
        """
        du_min = min(self.u, 1.0 - self.u)
        dv_min = min(self.v, 1.0 - self.v)
        return min(du_min, dv_min)    

    def near_edge(self, threshold):
        """
        Returns True if agent is closer than threshold to any edge.
        """
        return self.edge_distance() < threshold

    def sample_slope_uv(self, eps=0.01):
        """
        Approximates slope direction in UV space using finite differences.
        Returns a Vector2d (du, dv).
        """

        # Clamp sampling inside domain
        u1 = max(0.0, min(1.0, self.u + eps))
        v1 = max(0.0, min(1.0, self.v + eps))

        # Map to surface domain
        u0_srf = self.u_dom.T0 + self.u * (self.u_dom.T1 - self.u_dom.T0)
        v0_srf = self.v_dom.T0 + self.v * (self.v_dom.T1 - self.v_dom.T0)

        u1_srf = self.u_dom.T0 + u1 * (self.u_dom.T1 - self.u_dom.T0)
        v1_srf = self.v_dom.T0 + v1 * (self.v_dom.T1 - self.v_dom.T0)

        # Sample surface points
        p0 = self.face.PointAt(u0_srf, v0_srf)
        pu = self.face.PointAt(u1_srf, v0_srf)
        pv = self.face.PointAt(u0_srf, v1_srf)

        # Height differences
        du = pu.Z - p0.Z
        dv = pv.Z - p0.Z

        return rg.Vector2d(du, dv)

    def slope_vector_3d(self, scale=1.0):
        slope_uv = self.sample_slope_uv()
        vec = rg.Vector3d(slope_uv.X, slope_uv.Y, 0)
        vec.Unitize()
        return vec * scale

    def step(self, step_size=0.02, slope_weight=1.0):
        """
        Move agent in UV space according to slope.
        """

        # Do nothing if frozen
        if self.near_edge(EDGE_THRESHOLD):
            return

        # Sample slope
        slope = self.sample_slope_uv()

        if slope.Length < 1e-6:
            return

        slope.Unitize()

        # Move AGAINST slope = flow to valleys
        self.u -= slope.X * step_size * slope_weight
        self.v -= slope.Y * step_size * slope_weight

        # Clamp UV
        self.u = max(0.0, min(1.0, self.u))
        self.v = max(0.0, min(1.0, self.v))
# --------------------------------------------------
# Build regular grid
# --------------------------------------------------

agents = []
agent_pts = []

n = int(math.sqrt(agent_count))
n = max(n, 2)

for i in range(n):
    for j in range(n):
        if len(agents) >= agent_count:
            break

        u = float(i) / (n - 1)
        v = float(j) / (n - 1)

        a = Agent(u, v, face, u_dom, v_dom)
        agents.append(a)
        agent_pts.append(a.surface_point())

# # ------------------------------------------
# # DEBUG: sample slope vectors for first agents
# # ------------------------------------------

# slope_vectors = []

# for agent in agents[:5]:   # only first 5 agents
#     slope = agent.slope_direction_uv()
#     slope_vectors.append(slope)

# nearest_distances = []

# for agent in agents:
#     dists = []
#     for other in agents:
#         if agent is other:
#             continue
#         dists.append(agent.distance_to(other))
#     nearest_distances.append(min(dists))

# EDGE_THRESHOLD = edge_threshold  # Grasshopper slider (0.01–0.1)

# edge_agents = []
# free_agents = []

# for agent in agents:
#     if agent.near_edge(EDGE_THRESHOLD):
#         edge_agents.append(agent.surface_point())
#     else:
#         free_agents.append(agent.surface_point())

# slope_lines = []

# for agent in agents:
#     if agent.near_edge(EDGE_THRESHOLD):
#         continue  # skip frozen agents

#     pt = agent.surface_point()
#     vec = agent.slope_vector_3d(scale=1.5)
#     slope_lines.append(rg.Line(pt, pt + vec))

# for agent in agents:
#     agent.step(step_size=0.015)

# --------------------------------------------------
# Outputs
# --------------------------------------------------

a = agents
b = [agent.surface_point() for agent in agents]
