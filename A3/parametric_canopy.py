"""
Assignment 3: Parametric Structural Canopy — Pseudocode Scaffold

Author: Hroar Holm Bertelsen
Date: November 2025
"""
# ------------------------------
# 1. Imports 
# ------------------------------

# r: numpy
import numpy as np
import random
import Rhino.Geometry as rg
import scriptcontext as sc
import ghpythonlib.components as gh
import ghpythonlib.treehelpers as th
import math
import System.Drawing as SD

# ------------------------------
# 2. Config
# ------------------------------

MIN_TREE_SPACING = 4.0

TREE_BASE_OFFSET = z_offset

PANEL_OPENING_THRESHOLD = panel_threshold

TRUNK_RADIUS = trunk_radius

RADIUS_REDUCTION = branch_reduction

COLOR_BY_LEVEL = True


# ------------------------------
# 3. Helper functions
# ------------------------------

# Seed Generation
def seed_everything(seed):
    if seed is None:
        return
    try:
        seed = int(seed)  # force to int, fixes the Grasshopper float issue
        random.seed(seed)
        np.random.seed(seed)
    except Exception as e:
        raise RuntimeError(f"Failed to set random seeds: {e}")

# Grid generation
def uv_grid(divU, divV):
    u = np.linspace(0.0, 1.0, divU)
    v = np.linspace(0.0, 1.0, divV)
    U, V = np.meshgrid(u, v, indexing='xy')
    return U, V

# Generates the heighmap
def heightmap(U, V, amplitude=1.0, frequency=2.0, phase=0.0, noise_strength=0.0):
    H = amplitude * np.sin(2 * np.pi * frequency * U + phase) \
        * np.cos(2 * np.pi * frequency * V + phase)

    if noise_strength > 0:
        H += noise_strength * (np.random.rand(*U.shape) - 0.5)

    return H

# Gets lowerst points of surface
def lowest_points(points, count=4):
    """
    Return the 'count' number of lowest Z-elevation points.
    """
    sorted_pts = sorted(points, key=lambda p: p.Z)
    return sorted_pts[:count]

# Culls trees in close poximity
def cull_by_distance(points, min_dist):
    culled = []
    for p in points:
        too_close = False
        for c in culled:
            if p.DistanceTo(c) < min_dist:
                too_close = True
                break
        if not too_close:
            culled.append(p)
    return culled

# Connects branches to canopy
def nearest_grid_point(pt, grid_points):
    """ Returns (closest_point, distance)"""
    best = None
    best_dist = float("inf")
    for g in grid_points:
        d = pt.DistanceTo(g)
        if d < best_dist:
            best = g
            best_dist = d
    return best, best_dist

def mesh_pipe_from_line(line, radius, sides=24):
    """
    Creates a cylindrical mesh around a line.
    Works as a fast 'MeshPipe' replacement.
    """
    if line.Length == 0:
        return None

    from_pt = line.From
    to_pt = line.To

    axis = rg.Line(from_pt, to_pt)
    height = axis.Length

    # Cylinder axis plane
    plane = rg.Plane(from_pt, axis.Direction)
    circle = rg.Circle(plane, radius)
    cylinder = rg.Cylinder(circle, height)

    # Create mesh from cylinder
    mesh = rg.Mesh.CreateFromCylinder(cylinder, sides, 1)
    mesh.Normals.ComputeNormals()
    mesh.Compact()

    return mesh

def color_for_level(level):
        """Color mapping per branching level"""
        # Colors can be changed
        colors = [
        SD.Color.FromArgb(200, 50, 50),    # trunk = red
        SD.Color.FromArgb(50, 200, 50),    # level 1 = green
        SD.Color.FromArgb(50, 50, 200),    # level 2 = blue
        ]
        return colors[level % len(colors)]


# ------------------------------------ #
# 3.1 Surface Sampling & Mesh Helpers  #
# ------------------------------------ #

# Grid sampling
def sample_uniform_grid(surface, U, V):
    """Returns a (U+1)x(V+1) list-of-lists of points and coordinates sampled from surface."""
    u0, u1 = surface.Domain(0)
    v0, v1 = surface.Domain(1)

    pu = [u0 + (u1 - u0)*(i/float(U)) for i in range(U+1)]
    pv = [v0 + (v1 - v0)*(i/float(V)) for i in range(V+1)]

    coords = []
    pts = []
    for ui, u in enumerate(pu):
        row_pts = []
        row_uv = []
        for vj, v in enumerate(pv):
            pt = surface.PointAt(u, v)
            row_pts.append(pt)
            row_uv.append((u, v))
        pts.append(row_pts)
        coords.append(row_uv)

    return pts, coords

# Quad-Mesh edges
def quad_edges_from_points(pts):
    """Creates a mesh of quads from a 2D list of points."""
    U = len(pts)-1
    V = len(pts[0])-1

    lines = []
    for i in range(U+1):
        for j in range(V+1):
            if i < U:
                l = rg.Line(pts[i][j], pts[i+1][j]).ToNurbsCurve()
                lines.append(l)
            if j < V:
                l = rg.Line(pts[i][j], pts[i][j+1]).ToNurbsCurve()
                lines.append(l)
    return lines
    
# Quad-Mesh 
def quad_mesh_from_points(pts):
    rows = len(pts)
    cols = len(pts[0])

    mesh = rg.Mesh()

    # Add vertices
    for row in pts:
        for p in row:
            mesh.Vertices.Add(p)

    # Add faces
    for i in range(rows-1):
        for j in range(cols-1):
            a = i * cols + j
            b = a + 1
            c = b + cols
            d = c - 1
            mesh.Faces.AddFace(a, b, c, d)

    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh

# ------
# 3.2 Panels
# ----

import System.Drawing as SD

def map_K_to_color(K, K_min, K_max):
    """
    Maps curvature to color:
    valleys  (K low) = blue
    mid      (mid)   = yellow
    ridges   (K high)= red
    """
    if K_max == K_min:
        t = 0
    else:
        t = (K - K_min) / float(K_max - K_min)

    # Gradient: Blue → Yellow → Red
    # Blue  = (0, 0, 255)
    # Yellow= (255, 255, 0)
    # Red   = (255, 0, 0)

    if t < 0.5:
        # Blue → Yellow
        f = t * 2.0
        r = int(0   + f * 255)
        g = int(0   + f * 255)
        b = int(255 - f * 255)
    else:
        # Yellow → Red
        f = (t - 0.5) * 2.0
        r = 255
        g = int(255 - f * 255)
        b = 0

    return SD.Color.FromArgb(r, g, b)

# ------------------------------ #
# 4. Grid, Heightmap and Surface #
# ------------------------------ #
"""Force integer to avoid bug"""
divU = int(divU)
divV = int(divV)

# UV grid and heightmap
U, V = uv_grid(divU, divV)
H = heightmap(
    U, V,
    amplitude=amplitude,
    frequency=frequency,
    phase=phase,
    noise_strength=noise_strength
)

# Scale UV to actual XY size
X = U * size_x
Y = V * size_y
Z = H + z_offset

# Flatten points 
flat_points = [rg.Point3d(X[i,j], Y[i,j], Z[i,j]) for i in range(U.shape[0]) for j in range(U.shape[1])]

# Create NURBS surface through points
surface = rg.NurbsSurface.CreateThroughPoints(
    flat_points,
    U.shape[0],  # points in U direction (rows)
    U.shape[1],  # points in V direction (columns)
    3, 3,        # degree in U and V
    False, False  # non-periodic
)

# Add to Rhino document
if surface:
    sc.doc.Objects.AddSurface(surface)
    sc.doc.Views.Redraw()


# --------------------------------- #
# 5. Tree generation functions      #
# --------------------------------- #

def grow_tree(base_pt,
              parent_vec, 
              levels,
              min_branches, 
              max_branches,
              length_factor, 
              randomness,
              out_lines,
              out_pipes,
              out_colors,
              tilt_rad,
              radius,
              level
              ):
    """
    Generates branches recursively. 
    Snaps  last branches to grid geometry.
    Appends line geometry to output.
    Thickening of branches
    Per-level coloring
    """

    # STOP if no more levels
    if levels == 0:
        return

    branch_count = random.randint(min_branches, max_branches)
    L = parent_vec.Length * length_factor
    vertical = rg.Vector3d(0,0,1)

    for i in range(branch_count):

        # Base child direction
        child_vec = rg.Vector3d(parent_vec)
        child_vec.Unitize()
        child_vec *= L

        # tilt away from vertical
        tilt_axis = rg.Vector3d.CrossProduct(vertical, child_vec)
        if tilt_axis.IsZero:
            tilt_axis = rg.Vector3d(1,0,0)
        tilt_axis.Unitize()
        child_vec.Rotate(tilt_rad, tilt_axis)

        # jitter
        child_vec.X += (random.random()-0.5)*randomness
        child_vec.Y += (random.random()-0.5)*randomness
        child_vec.Z += (random.random()-0.5)*randomness*0.3

        # enforce upward
        if child_vec.Z < 0:
            child_vec.Z *= -1

        child_vec.Unitize()
        child_vec *= L
        child_pt = base_pt + child_vec

        # -------------------------------------------
        #  SNAP LAST-LEVEL BRANCHES TO GRID POINTS
        # -------------------------------------------
        if levels == 1:
            nearest_pt, dist = nearest_grid_point(child_pt, flat_points)
            line = rg.Line(base_pt, nearest_pt)

            # add line to nearest UV-grid point
            out_lines.append(rg.Line(base_pt, nearest_pt))

            # do NOT add original child line
            # do NOT recurse further

            # Pipe for last segment
            pipe = mesh_pipe_from_line(line, radius)
            out_pipes.append(pipe)
            out_colors.append(color_for_level(level))

            continue

        # Otherwise: normal branch
        line = rg.Line(base_pt, child_pt)
        out_lines.append(line)

        # Mesh pipe
        pipe = mesh_pipe_from_line(line, radius)
        out_pipes.append(pipe)
        out_colors.append(color_for_level(level))

                # recursion
        grow_tree(child_pt, 
                  child_vec, 
                  levels-1,
                  min_branches, 
                  max_branches,
                  length_factor, 
                  randomness,
                  out_lines, 
                  out_pipes,
                  out_colors,
                  tilt_rad,
                  radius * RADIUS_REDUCTION,
                  level + 1
                  )



def fractal_tree_radial(base_pt,
                        trunk_length=5.0,
                        first_level_min_branches=3,
                        first_level_max_branches=4,
                        first_level_angle_min=10,
                        first_level_angle_max=15,
                        levels=3,
                        min_branches=2,
                        max_branches=4,
                        angle_min=20,
                        angle_max=40,
                        length_factor=0.7,
                        randomness=0.2,
                        trunk_radius=1.0):
    """
    Builds a radial fractal tree:
    - Creates trunk
    - First-level radial branches
    - Calls grow_tree() for deeper levels
    Returns list of Line geometry.
    """

    # Empty lists
    lines = []
    pipes = []
    colors = []


    # Trunk
    trunk_vec = rg.Vector3d(0,0,1)*trunk_length
    trunk_top = base_pt + trunk_vec
    trunk_line = rg.Line(base_pt, trunk_top)

    lines.append(trunk_line)

    trunk_mesh = mesh_pipe_from_line(trunk_line, trunk_radius)
    pipes.append(trunk_mesh)
    colors.append(color_for_level(0))

    # First-level radial branches
    branch_count = random.randint(first_level_min_branches, first_level_max_branches)
    theta_deg = random.uniform(first_level_angle_min, first_level_angle_max)
    theta = math.radians(theta_deg)
    vertical_axis = rg.Vector3d(0,0,1)

    for i in range(branch_count):
        phi = 2*math.pi*i/branch_count  # evenly distributed
        rot_around_trunk = rg.Transform.Rotation(phi, vertical_axis, trunk_top)

        # start vector
        branch_vec = rg.Vector3d(trunk_vec)
        branch_vec.Unitize()
        branch_vec *= trunk_length*0.6  # first branch length


        # rotate from vertical
        perp_axis = rg.Vector3d.CrossProduct(vertical_axis, branch_vec)
        if perp_axis.IsZero:
            perp_axis = rg.Vector3d(1,0,0)
        perp_axis.Unitize()

        rot_from_vertical = rg.Transform.Rotation(theta, perp_axis, trunk_top)
        branch_vec.Transform(rot_from_vertical)
        branch_vec.Transform(rot_around_trunk)

        branch_end = trunk_top + branch_vec
        branch_line = rg.Line(trunk_top, branch_end)

        lines.append(branch_line)
        branch_mesh = mesh_pipe_from_line(branch_line, trunk_radius * RADIUS_REDUCTION)
        pipes.append(branch_mesh)
        colors.append(color_for_level(1))

        # Compute fixed tilt for first-level branches
        theta_deg = random.uniform(first_level_angle_min, first_level_angle_max)
        tilt_rad = math.radians(theta_deg)

        # ------------------------------
        # Recursive continuation
        # ------------------------------
        grow_tree(
            branch_end,
            branch_vec,
            levels - 1,
            min_branches,
            max_branches,
            length_factor,
            randomness,
            lines,
            pipes,
            colors,
            tilt_rad,
            trunk_radius * RADIUS_REDUCTION,
            2    # recursion level
        )
                

    return lines, pipes, colors



# --------------------------------- #
# 6. Main                           #
# --------------------------------- #

# ----------------------------------
# 6.1 Seed
seed_everything(seed)
# ----------------------------------

# ----------------------------------
# 6.2 Surface sampling and compute Gaussian curvature
# ----------------------------------
pts, uv_coords = sample_uniform_grid(surface, divU, divV)
pts_tree = th.list_to_tree(pts)

curvature_grid = [[0]*(divV+1) for _ in range(divU+1)]

for i in range(divU + 1):
    for j in range(divV + 1):
        u, v = uv_coords[i][j]
        curv = surface.CurvatureAt(u,v)
        if curv:
            curvature_grid[i][j] = curv.Gaussian

        else:
            curvature_grid[i][j] = 0.0

# ----------------------------------
# 6.3 Compute quad panel values of curvature
# ----------------------------------

panel_values = []

for i in range(divU):
    for j in range(divV):
        c1 = curvature_grid[i][j]
        c2 = curvature_grid[i+1][j]
        c3 = curvature_grid[i+1][j+1]
        c4 = curvature_grid[i][j+1]
        K = (c1 + c2 + c3 + c4) / 4.0
        panel_values.append(K)

# List for indexing of panels
base_quads = [None] * len(panel_values)
opening_panels = [None] * len(panel_values)

# Normalize curvature opening to         
allK = np.array(panel_values)
K_min, K_max = allK.min(), allK.max()

def map_curvature_to_opening(K):
    """
    Maps curvature K to a normalized opening size
    0 = Valley
    1 = Ridge
    """
    if K_max == K_min:
        return 0
    return (K - K_min) / (K_max - K_min)




edges = quad_edges_from_points(pts)
mesh = quad_mesh_from_points(pts)

# ----------------------------------
# 6.4 Quad corner calculations
# ----------------------------------
idx = 0

def lerp(a, b, t):
    """Linear interpolation between two 3d points"""
    return rg.Point3d(
                      a.X + (b.X - a.X) * t,
                      a.Y + (b.Y - a.Y) * t,
                      a.Z + (b.Z - a.Z) * t
                    )

for i in range(divU):
    for j in range (divV):

        quad_id = idx           
        K = panel_values[idx]
        t = map_curvature_to_opening(K)
        idx += 1

        # Generate quad corners
        p1 = pts[i][j]
        p2 = pts[i+1][j]
        p3 = pts[i+1][j+1]
        p4 = pts[i][j+1]

        #Store original quad
        base_quads[quad_id] = rg.Polyline([p1, p2, p3, p4, p1])

        # Cull panels based on threshold
        if t < PANEL_OPENING_THRESHOLD:
            opening_panels[quad_id] = None
            continue

        
        # Center point
        center = rg.Point3d(
                            (p1.X + p2.X + p3.X + p4.X)/4,
                            (p1.Y + p2.Y + p3.Y + p4.Y)/4,
                            (p1.Z + p2.Z + p3.Z + p4.Z)/4
        )
    
        # Inset (opening) quad
        q1 = lerp(p1, center, t)
        q2 = lerp(p2, center, t)
        q3 = lerp(p3, center, t)
        q4 = lerp(p4, center, t)

        opening_panels[quad_id] = rg.Polyline([q1, q2, q3, q4, q1])



# ----------------------------------
# 6.5 Color each quad based on curvature
# ----------------------------------

colored_quad_colors = []

for i, quad in enumerate(base_quads):
    if quad is None:
        colored_quad_colors.append(SD.Color.Black)
        continue

    K = panel_values[i]
    color = map_K_to_color(K, K_min, K_max)
    colored_quad_colors.append(color)

# ----------------------------------
# 6.6 Anchor finding
# ----------------------------------
anchors = lowest_points(flat_points, count=14)

# ----------------------------------
# 6.7 Tree base preperations
# ----------------------------------
treeBases_raw = []
for pt in anchors:
    base_pt = rg.Point3d(pt.X, pt.Y, pt.Z - TREE_BASE_OFFSET)
    treeBases_raw.append(base_pt)


treeBases = cull_by_distance(treeBases_raw, MIN_TREE_SPACING)

# ----------------------------------
# 6.8 Generation of trees
# ----------------------------------
all_trees_lines = []
all_trees_pipes = []
all_trees_colors = []


for base_pt in treeBases:
    tree_lines, tree_pipes, tree_colors = fractal_tree_radial(
        base_pt=base_pt,
        trunk_length=trunk_length,
        first_level_min_branches=first_level_min_branches,
        first_level_max_branches=first_level_max_branches,
        first_level_angle_min=first_level_angle_min,
        first_level_angle_max=first_level_angle_max,
        levels=levels,
        min_branches=min_branches,
        max_branches=max_branches,
        angle_min=angle_min,
        angle_max=angle_max,
        length_factor=length_factor,
        randomness=randomness,
        trunk_radius=TRUNK_RADIUS
    )


    all_trees_lines.extend(tree_lines)
    all_trees_pipes.extend(tree_pipes)
    all_trees_colors.extend(tree_colors)   

# ---------------------------------- #
# 7. Output channels                 #
# ---------------------------------- #
a = surface                             # canopy surface
b = anchors                             # anchor points
c = opening_panels                      # curvature-based openings
d = base_quads                          # base quad panels
e = colored_quad_colors                 # quad colors

fractal_supports = all_trees_lines      
tree_meshes = all_trees_pipes          
tree_mesh_color = all_trees_colors     