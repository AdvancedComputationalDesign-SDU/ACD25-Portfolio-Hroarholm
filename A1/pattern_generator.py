import numpy as np
import matplotlib.pyplot as plt

# Parameters for the sinusoidal wave pattern
center_x, center_y = 2, 1  # Emission point (center)
wavelength = 0.5  # Wavelength of the waves
num_waves = 10  # Approximate number of waves (controlled by extent/wavelength)
grid_size = 400  # Size of the 2D array (square grid)

# Create a meshgrid for x and y coordinates
x = np.linspace(-4, 4, grid_size)
y = np.linspace(-4, 4, grid_size)
X, Y = np.meshgrid(x, y)

# Calculate radial distance from the emission point
r = np.sqrt((X - center_x)**2 + (Y - center_y)**2)

# Generate the sinusoidal wave pattern: sin(2π r / λ)
# This creates concentric waves emanating from the center
wave_pattern = np.sin(2 * np.pi * r / wavelength)

# The resulting 2D NumPy array representing the sinusoidal wave pattern
sinusoidal_wave_array = wave_pattern

# Function to manipulate RGB channels for depth visualization
# - High values (peaks): warmer colors (more red)
# - Low values (troughs): cooler colors (more blue)
# - This simulates 'depth' with color gradient
def wave_to_rgb(wave):
    # Normalize wave to 0-1 range for RGB (wave is -1 to 1)
    norm_wave = (wave + 1) / 2  # 0 (trough/deep) to 1 (peak/shallow)
    
    # Manipulate channels:
    # Red: increases with height (shallow)
    r = norm_wave
    
    # Green: subtle in the middle for transition
    g = 0.3 * norm_wave
    
    # Blue: increases with depth (low height)
    b = 1 - norm_wave
    
    # Stack into RGB array (0-1 float)
    return np.stack([r, g, b], axis=-1)

# Create RGB array for visualization
rgb_wave = wave_to_rgb(sinusoidal_wave_array)

# Visualize the depth using the RGB-manipulated array
plt.figure(figsize=(8, 8))
plt.imshow(rgb_wave)
plt.axis('off')
# No colorbar needed for RGB, but axes for context
plt.show()

# Optional: Also show grayscale version for comparison
plt.figure(figsize=(8, 8))
plt.imshow(sinusoidal_wave_array, cmap='gray', extent=(-5, 5, -5, 5))
plt.title('Grayscale Wave Pattern (for reference)')
plt.xlabel('X')
plt.ylabel('Y')
plt.colorbar(label='Wave Amplitude')
plt.show()

# Print array info
print(f"Wave Array shape: {sinusoidal_wave_array.shape}")
print(f"Wave Array dtype: {sinusoidal_wave_array.dtype}")
print(f"Wave Array min/max: {sinusoidal_wave_array.min():.2f} / {sinusoidal_wave_array.max():.2f}")
print(f"RGB Array shape: {rgb_wave.shape}")
# # Generate patterns

# vertical stripes
stripes_v = np.zeros_like(array1)
stripes_v[:, ::2] = 1
plt.figure()
plt.imshow(stripes_v, cmap='bone')
plt.title('Vertical stripes')
plt.axis('off')
plt.show()