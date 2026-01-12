"""
Assignment 4: Agent-Based Model for Surface Panelization
Author: Hroar Holm Bertelsen

Agent Builder script
"""

# ------------------------------------------------------------------
# 1. Imports
# ------------------------------------------------------------------

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
# Agent class
# --------------------------------------------------

class Agent:
    def __init__(self, u, v, face, u_dom, v_dom):
        self.u = u
        self.v = v
        self.face = face
        self.u_dom = u_dom
        self.v_dom = v_dom
        self.trail = []

        self.frozen = False

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

    def step(self, agents, step_size=0.02, slope_weight=1.0, separation_weight=1.0, min_dist=0.05):

        if self.frozen:
            return

        # --- slope force ---
        slope = self.sample_slope_uv()
        if slope.Length > 1e-6:
            slope.Unitize()
        slope_vec = rg.Vector2d(-slope.X, -slope.Y)  # downhill

        # --- separation force ---
        sep = self.separation_force_uv(agents, min_dist)

        # --- combine forces ---
        move = rg.Vector2d(
            slope_weight * slope_vec.X + separation_weight * sep.X,
            slope_weight * slope_vec.Y + separation_weight * sep.Y
        )

        if move.Length < 1e-6:
            return

        move.Unitize()

        self.u += move.X * step_size
        self.v += move.Y * step_size

        # Clamp UV
        self.u = max(0.0, min(1.0, self.u))
        self.v = max(0.0, min(1.0, self.v))

        self.trail.append(self.surface_point())

    def separation_force_uv(self, agents, min_dist):
        """
        Computes repulsion vector in UV space
        based on nearby agents.
        """
        fx = 0.0
        fy = 0.0
        count = 0

        for other in agents:
            if other is self:
                continue

            du = self.u - other.u
            dv = self.v - other.v
            dist = math.sqrt(du*du + dv*dv)

            if dist < min_dist and dist > 1e-6:
                fx += du / dist
                fy += dv / dist
                count += 1

        if count == 0:
            return rg.Vector2d(0, 0)

        v = rg.Vector2d(fx, fy)
        v.Unitize()
        return v    
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

# --------------------------------------------------
# Outputs
# --------------------------------------------------

a = agents
b = [agent.surface_point() for agent in agents]
