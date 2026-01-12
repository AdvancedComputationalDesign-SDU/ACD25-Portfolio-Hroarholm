"""
Assignment 4: Agent-Based Model for Surface Panelization

Author: Hroar Holm Bertelsen

Surface Generator script

Description:
This file defines the structural outline for generating or preprocessing
surfaces and geometric signal fields for Assignment 4.

Note: This script is intended to be used within Grasshopper's Python
scripting component.
"""

# ------------------------------------------------------------------
# 1. Imports
# ------------------------------------------------------------------

import Rhino.Geometry as rg
import numpy as np

# ------------------------------------------------------------------
# 2. Heightmap generation
# ------------------------------------------------------------------

def generate_heightmap(shape, amplitude, frequency, phase, noise_strength=0.0):
    """Generate a sinusoidal heightmap with noise."""
    u = np.linspace(0, 1, shape[0])
    v = np.linspace(0, 1, shape[1])
    U, V = np.meshgrid(u, v)

    H = amplitude * np.sin(2*np.pi*frequency*U + phase) * \
                     np.cos(2*np.pi*frequency*V + phase)

    # optional noise (controlled externally)
    if noise_strength > 0:
        H += noise_strength * (np.random.rand(*H.shape) - 0.5)

    return H

# ------------------------------------------------------------------
# 3. Create flat XY grid
# ------------------------------------------------------------------

def sample_surface_uniform(shape=(50,50)):
    size_x = float(sizeX)
    size_y = float(sizeY)

    u = np.linspace(0, size_x, shape[0])
    v = np.linspace(0, size_y, shape[1])

    grid = []
    for i in range(shape[0]):
        row = []
        for j in range(shape[1]):
            row.append(rg.Point3d(u[i], v[j], 0))
        row = row
        grid.append(row)

    return np.array(grid)


# ------------------------------------------------------------------
# 4. Apply heightmap to Z-values
# ------------------------------------------------------------------

def manipulate_point_grid(heightmap, point_grid, scalar=1.0):
    grid = point_grid.copy()
    rows, cols = grid.shape

    if heightmap is None:
        raise ValueError("Heightmap is None — check U, V inputs")

    for i in range(rows):
        for j in range(cols):
            grid[i, j].Z += heightmap[i, j] * scalar
    
    return grid


# ------------------------------------------------------------------
# 5. Build surface using correct RhinoCommon API
# ------------------------------------------------------------------

def build_surface(point_grid):
    rows, cols = point_grid.shape

    flat = point_grid.reshape(rows * cols).tolist()

    surf = rg.NurbsSurface.CreateThroughPoints(
        flat,
        rows,
        cols,
        3, 3,
        False, False
    )

    return surf


# ------------------------------------------------------------------
# 6. Execution
# ------------------------------------------------------------------
U = int(U)
V = int(V)

H = generate_heightmap((U, V), amplitude, frequency, phase, noise_strength)
P = sample_surface_uniform((U, V))
Pm = manipulate_point_grid(H, P, scalar)
surface = build_surface(Pm)

U_norm = np.linspace(0, 1, U)
V_norm = np.linspace(0, 1, V)

# ------------------------------------------------------------------
# 7. Outputs
# ------------------------------------------------------------------

a = surface
b = H
c = (U, V)
d = (surface.Domain(0), surface.Domain(1))
e = (U_norm, V_norm)