import numpy as np
import pandas as pd

lat_min, lat_max = 60.640, 60.650
lon_min, lon_max = 17.840, 17.850
num_lat = 15
num_lon = 15

np.random.seed(42)

lats = np.linspace(lat_min, lat_max, num_lat)
lons = np.linspace(lon_min, lon_max, num_lon)
lat_grid, lon_grid = np.meshgrid(lats, lons, indexing='ij')

lat_center = (lat_min + lat_max) / 2
lon_center = (lon_min + lon_max) / 2
lat_radius = (lat_max - lat_min) / 2 * 0.9
lon_radius = (lon_max - lon_min) / 2 * 0.7

angle_grid = np.arctan2(lat_grid - lat_center, lon_grid - lon_center)
radial_noise = 0.1 * np.sin(5 * angle_grid) + 0.05 * np.random.rand(*angle_grid.shape)

ellipse_mask = (((lat_grid - lat_center)/(lat_radius*(1+radial_noise)))**2 +
                ((lon_grid - lon_center)/(lon_radius*(1+radial_noise)))**2) <= 1

max_depth = 11
min_depth = 1.5
dist_center_norm = np.sqrt(((lat_grid - lat_center)/lat_radius)**2 +
                           ((lon_grid - lon_center)/lon_radius)**2)
dist_center_norm = np.clip(dist_center_norm, 0, 1)
depth_map = min_depth + (1 - dist_center_norm) * (max_depth - min_depth)

def noise(std): return np.random.normal(0, std)


data = []

for i in range(num_lat):
    for j in range(num_lon):
        if not ellipse_mask[i, j]:
            continue
        
        n_depths = np.random.randint(3, 6)
        depths = np.sort(np.random.uniform(0, depth_map[i, j], n_depths))
        
        for depth in depths:
            
            # Temperature (smooth transition using tanh for continuous)
            # Surface: 18°C, Deep: 4°C, with logical thermocline gradient
            T_surface = 18.0  # Temperature at surface
            T_deep = 4.0      # Temperature at deep layer
            thermocline_center = 6.0  # Center of thermocline
            thermocline_width = 2.5   # Controls steepness of transition
            
            # Smooth S-curve transition
            T_true = T_deep + (T_surface - T_deep) * 0.5 * (1 - np.tanh((depth - thermocline_center) / thermocline_width))
            T_true += noise(0.01)
            T = T_true + noise(0.05)

            # pH (depth + temperature correlation)
            pH_true = 7.6 - 0.03 * depth + 0.03 * (T - 25)
            pH = pH_true + noise(0.1)


            # Turbidity (slightly higher deeper, lower if warmer)
            turb_true = 5 + 0.3 * depth - 0.02 * (T - 16) 
            turbidity = turb_true + noise(0.2)


            DO_sat = 14.6 - 0.4 * T + 0.01 * T**2  #Approximation of DO table in Arduino
            DO_true = DO_sat - 0.3 * depth
            dissolved_oxygen = DO_true + noise(0.2)

            # TDS compensation
            TDS0 = 100 + 1.5 * depth  # base before compensation
            TDS_true = TDS0 / (1 + 0.02 * (T - 25))
            TDS = TDS_true + noise(10)

            num_sats = np.random.randint(7, 15)

            data.append([
                lat_grid[i, j], lon_grid[i, j], depth,
                round(pH, 2), round(T, 2),
                round(turbidity, 2), round(dissolved_oxygen, 2),
                round(TDS, 1), num_sats
            ])

df = pd.DataFrame(data, columns=[
    'latitude', 'longitude', 'depth', 'pH', 'temperature',
    'turbidity', 'dissolved_oxygen', 'TDS', 'num_sats'
])

print(df.head())
print("Total rows:", df.shape[0])

df.to_csv("synthetic_lake_final.csv", index=False)
