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

def noise(std): 
    return np.random.normal(0, std)

# Seasonal parameters (month-dependent)
def get_seasonal_params(month):
    """
    Returns seasonal parameters for temperature and other factors
    month: 1-12 (Jan-Dec)
    """
    # Winter (Dec-Feb): months 12, 1, 2
    # Spring (Mar-May): months 3, 4, 5
    # Summer (Jun-Aug): months 6, 7, 8
    # Fall (Sep-Nov): months 9, 10, 11
    
    # Surface temperature varies seasonally
    if month in [12, 1, 2]:  # Winter
        T_surface = 4.0
        T_deep = 4.0
        thermocline_strength = 0.1  # weak stratification in winter
        DO_depletion = 0.1  # minimal oxygen depletion
    elif month in [3, 4, 5]:  # Spring
        T_surface = 10.0 + (month - 3) * 2.5  # warming up
        T_deep = 4.5
        thermocline_strength = 0.3 + (month - 3) * 0.1
        DO_depletion = 0.15
    elif month in [6, 7, 8]:  # Summer
        T_surface = 20.0 + (month - 6) * 1.5  # peak warmth
        T_deep = 6.0
        thermocline_strength = 0.7 + (month - 6) * 0.1  # strong stratification
        DO_depletion = 0.35 + (month - 6) * 0.05  # increasing hypoxia
    else:  # Fall (9, 10, 11)
        T_surface = 18.0 - (month - 9) * 3.0  # cooling down
        T_deep = 5.0
        thermocline_strength = 0.6 - (month - 9) * 0.15  # weakening
        DO_depletion = 0.3 - (month - 9) * 0.05
    
    return {
        'T_surface': T_surface,
        'T_deep': T_deep,
        'thermocline_strength': thermocline_strength,
        'DO_depletion': DO_depletion
    }

# Months to generate data for (e.g., Apr, Jun, Aug, Oct)
months = [4, 6, 8, 10]
year = 2024  # Base year for timestamps

data = []

# First, generate consistent sampling locations
sampling_locations = []
for i in range(num_lat):
    for j in range(num_lon):
        if not ellipse_mask[i, j]:
            continue
        
        # Fixed number of depths per location for consistency
        n_depths = np.random.randint(3, 6)
        depths = np.sort(np.random.uniform(0, depth_map[i, j], n_depths))
        
        for depth in depths:
            sampling_locations.append({
                'i': i,
                'j': j,
                'lat': lat_grid[i, j],
                'lon': lon_grid[i, j],
                'depth': depth
            })

# Now generate measurements for each month at the same locations
for month in months:
    params = get_seasonal_params(month)
    
    for loc in sampling_locations:
        i, j = loc['i'], loc['j']
        depth = loc['depth']
        lat, lon = loc['lat'], loc['lon']
        
        # Temperature with seasonal variation
        thermocline_center = 6.0
        thermocline_width = 2.5 / params['thermocline_strength']  # narrower in summer
        
        T_true = params['T_deep'] + (params['T_surface'] - params['T_deep']) * \
                 0.5 * (1 - np.tanh((depth - thermocline_center) / thermocline_width))
        T_true += noise(0.01)
        T = T_true + noise(0.05)

        # pH (depth + temperature correlation, slightly lower in summer due to decomposition)
        pH_base = 7.6 if month in [12, 1, 2, 3] else 7.5
        pH_true = pH_base - 0.03 * depth + 0.03 * (T - 25)
        pH = pH_true + noise(0.1)

        # Turbidity (higher in spring due to runoff, lower in winter)
        turb_base = 5.5 if month in [3, 4, 5] else 5.0
        turb_true = turb_base + 0.3 * depth - 0.02 * (T - 16)
        turbidity = turb_true + noise(0.2)

        # Dissolved Oxygen (temperature dependent + seasonal depletion)
        DO_sat = 14.6 - 0.4 * T + 0.01 * T**2
        DO_true = DO_sat - params['DO_depletion'] * depth * 2  # seasonal depth depletion
        dissolved_oxygen = DO_true + noise(0.2)

        # TDS (temperature compensated, slightly higher in summer)
        TDS0 = 100 + 1.5 * depth
        if month in [6, 7, 8]:
            TDS0 += 10  # slightly elevated in summer
        TDS_true = TDS0 / (1 + 0.02 * (T - 25))
        TDS = TDS_true + noise(10)

        num_sats = np.random.randint(7, 15)
        
        # Create timestamp with random day and time
        day = np.random.randint(1, 29)  # Use 28 to avoid month length issues
        hour = np.random.randint(0, 24)
        minute = np.random.randint(0, 60)
        second = np.random.randint(0, 60)
        timestamp = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

        data.append([
            lat, lon, depth,
            round(pH, 2), round(T, 2),
            round(turbidity, 2), round(dissolved_oxygen, 2),
            round(TDS, 1), num_sats, timestamp
        ])

df = pd.DataFrame(data, columns=[
    'latitude', 'longitude', 'depth', 'pH', 'temperature',
    'turbidity', 'dissolved_oxygen', 'TDS', 'num_sats', 'timestamp'
])

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Sort by timestamp and location for easier viewing
df = df.sort_values(['timestamp', 'latitude', 'longitude', 'depth']).reset_index(drop=True)

print(df.head(20))
print(f"\nTotal rows: {df.shape[0]}")
print(f"Locations sampled: {len(sampling_locations)}")
print(f"Months: {months}")
print(f"Measurements per month: {len(sampling_locations)}")
print("\nSummary by month:")
month_extract = df['timestamp'].dt.month
print(df.groupby(month_extract)[['temperature', 'dissolved_oxygen', 'pH']].mean())

df.to_csv("synthetic_lake_temporal.csv", index=False)
