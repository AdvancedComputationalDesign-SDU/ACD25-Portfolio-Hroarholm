"""
Assignment 2: Fractal Generator

Author: Hroar Holm Bertelsen

Description:
This script generates fractal patterns using recursive functions and geometric transformations.
"""

# Import necessary libraries
import math
import matplotlib.pyplot as plt
from shapely.geometry import LineString, MultiLineString, Point
from shapely.affinity import rotate, translate
from shapely.affinity import scale, translate, rotate
from shapely.geometry import box  
import random


"""---Parameters for this run"""
SEED = 28
iterations = 5     # L-system depth
ANGLE = 45          # turning angle
STEP = 6            # step length
INFLUENCES = ['attractor', 'obstacle']

random.seed(SEED)

"--- Define constraint box ---"
constraint_box = box(50, 225, 75, 240)  


"--- L-system definition ---"
def apply_rules(ch):
    if ch == 'X':
        return "F+[[X]-X]-F[-FX]+X"
    elif ch == 'F':
        return "FF"
    else:
        return ch

def process_string(s):
    return ''.join(apply_rules(ch) for ch in s)

def create_l_system(iterations, axiom):
    result = axiom
    for _ in range(iterations):
        result = process_string(result)
    return result

"--- Return a new heading slightly adjusted toward the attractor point.--- "
def steer_toward_attractor(x, y, heading, attractor, strength=0.1):
    ax, ay = attractor
    dx, dy = ax - x, ay - y
    target_angle = math.degrees(math.atan2(dy, dx))
    diff = (target_angle - heading + 540) % 360 - 180  # shortest signed rotation
    return heading + diff * strength

"--- Draw the L-system into Shapely geometry ---"
def draw_l_system_shapely(instructions, angle=ANGLE, step=STEP):
    attractor = (100,300)
    attract_strength = 0.05
    stack = []
    x, y = 0.0, 0.0
    heading = 90.0  # start pointing up
    lines = []
    stem_ids = []
    current_stem = 0
    color_map = {0: (0, 0.6, 0)}  # base stem color


    for cmd in instructions:
        if cmd == 'F':
            # slightly steer toward an attractor point
             if attractor is not None:
                heading = steer_toward_attractor(x, y, heading, attractor, attract_strength)

                # compute endpoint
                rad = math.radians(heading)
                step_variation = step * random.uniform(0.85, 1.15)
                x2 = x + step_variation * math.cos(rad)
                y2 = y + step_variation * math.sin(rad)


                # Check if the new line intersects the constraint box
                candidate_line = LineString([(x, y), (x2, y2)])
                if not candidate_line.intersects(constraint_box):
                    lines.append(candidate_line)
                    stem_ids.append(current_stem)
                    x, y = x2, y2
                else:

                    continue

        elif cmd == '+':
            heading -= angle + random.uniform(-2,2)  # add slight randomness
        elif cmd == '-':
            heading += angle + random.uniform(-2,2) 
        elif cmd == '[':
            stack.append((x, y, heading, current_stem))
            current_stem += 1
            # Assign color for new stem
            color_map[current_stem] = (0, 0.4 + random.uniform(0.2, 0.6), 0)
        elif cmd == ']':
            x, y, heading, current_stem = stack.pop()
    return MultiLineString(lines), stem_ids, color_map


"--- Generate ---"
axiom = "X"
angle = ANGLE
step = STEP

instructions = create_l_system(iterations, axiom)
attractor = (100,325)
attract_strength = 0.08


geometry, stem_ids, color_map = draw_l_system_shapely(instructions, angle, step)

"--- Apply transformations ---"
geometry = scale(geometry, xfact=1, yfact=1)


"--- Visualization with Matplotlib including Attractor ---"
fig, ax = plt.subplots(figsize=(8, 8))
num_lines = len(geometry.geoms)
for line, stem_id in zip(geometry.geoms, stem_ids):
    x, y = line.xy
    color = color_map.get(stem_id, (0, 0.6, 0))  # default green
    ax.plot(x, y, color=color, linewidth=1.2)

"---Draw forbidden box---"
x_min, y_min, x_max, y_max = constraint_box.bounds
ax.add_patch(plt.Rectangle((x_min, y_min),
                           x_max - x_min,
                           y_max - y_min,
                           color='red', alpha=0.3, label='Forbidden zone'))



"""--- Draw attractor point ---"""
ax.plot(attractor[0], attractor[1], 'yo', markersize=8, label='Attractor')
ax.set_aspect("equal", "datalim")
ax.axis("off")

"""--- Final clean export ---"""
ax.set_aspect("equal", adjustable="box")
ax.axis("off")
plt.margins(0)

"""---Ensure output folder exists---"""
import os
print("Current working directory:", os.getcwd())
os.makedirs("images", exist_ok=True)

"""---Save tightly cropped, high-resolution image--"""
plt.savefig("images/fractal_output.png", bbox_inches="tight", pad_inches=0, dpi=300)
plt.close(fig)
