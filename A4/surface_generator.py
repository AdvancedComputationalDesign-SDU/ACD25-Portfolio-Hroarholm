"""
Assignment 4: Agent-Based Model for Surface Panelization

Author: Your Name

Surface Generator Template

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
import scriptcontext as sc

# ------------------------------------------------------------------
# 2. Heightmap
# ------------------------------------------------------------------

def generate_heightmap(shape=(50,50), amplitude=1.0, frequency=2.0, phase=0.0):
    u = np.linspace(0,1,shape[0])
    v = np.linspace(0,1,shape[1])
    U,V = np.meshgrid(u,v)

    H = amplitude * np.sin(2*np.pi*frequency*U + phase) * \
        np.cos(2*np.pi*frequency*V + phase)

    H += (0.1 * amplitude * np.random.rand(*H.shape) - 0.05)
    return H


# ------------------------------------------------------------------
# 3. Sampling grid (base plane)
# ------------------------------------------------------------------

def sample_surface_uniform(surface=None, shape=(50,50)):
    size_x = float(sizeX)
    size_y = float(sizeY)
    
    u = np.linspace(0,size_x,shape[0])
    v = np.linspace(0,size_y,shape[1])
    
    grid = []

    for i in range(shape[0]):
        row = []
        for j in range(shape[1]):
            row.append(rg.Point3d(u[i], v[j], 0))
        grid.append(row)

    return np.array(grid)


# ------------------------------------------------------------------
# 4. Apply heightmap
# ------------------------------------------------------------------

def manipulate_point_grid(heightmap, point_grid, scalar=1.0):
    grid = point_grid.copy()
    
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            grid[i,j].Z += heightmap[i,j] * scalar

    return grid


# ------------------------------------------------------------------
# 5. Build surface
# ------------------------------------------------------------------

def build_surface(point_grid):

    rows, cols = point_grid.shape
    flat = point_grid.flatten().tolist()

    return rg.NurbsSurface.CreateThroughPoints(
        flat,
        rows,
        cols,
        3, 3,
        False, False
    )


# ------------------------------------------------------------------
# 6. Execution
# ------------------------------------------------------------------

H = generate_heightmap((U,V), amplitude, frequency, phase)
P = sample_surface_uniform(None, (U,V))
Pm = manipulate_point_grid(H, P, scalar)
surface = build_surface(Pm)

a = surface
h = H
shape = (U, V)
domain = (surface.Domain(0), surface.Domain(1))