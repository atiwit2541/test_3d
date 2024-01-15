import ee
import folium
import numpy as np
import datetime
import ee

# Authenticate using OAuth2
ee.Authenticate()

# Set the desired project
project_id = 'atiwit-bd383'  # Replace with your actual project ID
ee.Initialize(project=project_id)
# Initialize the Earth Engine API
ee.Initialize()

# Define the asset path for your ROI
roi_asset_path = 'projects/atiwit/assets/North'
roi = ee.FeatureCollection(roi_asset_path)

# Calculate the centroid of the ROI
centroid = roi.geometry().centroid()
centroid_coords = centroid.getInfo()['coordinates'][::-1]  # Reverse the coordinates for Folium
st_date = '2024-01-01'
# Get the current date and time
current_datetime = datetime.datetime.now()
# Format the date and time as a string
formatted_datetime = current_datetime.strftime("%Y-%m-%d")
# Load a MODIS image
modis = (ee.ImageCollection('MODIS/061/MCD19A2_GRANULES')
         .filterBounds(roi)
         .filterDate(st_date, formatted_datetime)
         .select('Optical_Depth_047')
         .median())

# Clip MODIS with the ROI
clipped_modis = modis.clip(roi)

# Extract MODIS values as an Earth Engine list
modis_list_ee = clipped_modis.reduceRegion(
    reducer=ee.Reducer.toList(),
    geometry=roi,
    scale=10000,  # Increase the scale to aggregate at a coarser resolution
    maxPixels=1e9  # Set maxPixels to a suitable value
).get('Optical_Depth_047')

# Convert the Earth Engine list to a Python list
modis_list = ee.List(modis_list_ee).getInfo()

# Convert the list to a NumPy array
modis_np = np.array(modis_list)

# Multiply
modis_multiply = modis_np * 0.001

# Cubic regression
y = 20.442691 + 73.706255 * modis_multiply + 119.795299 * modis_multiply**2 - 137.620216 * modis_multiply**3

# Create a Folium map
my_map = folium.Map(location=centroid_coords, zoom_start=8)  # Set the location to the centroid of the ROI

# Add a layer to the map
map_id_dict = clipped_modis.getMapId({'min': 0, 'max': 200, 'palette': ['blue', 'green', 'yellow', 'orange', 'red']})
folium.TileLayer(
    tiles=map_id_dict['tile_fetcher'].url_format,
    attr='Google Earth Engine',
    overlay=True,
    name='MODIS Optical Depth'
).add_to(my_map)

# Display the map
my_map
# Save the map to an HTML file
my_map.save(f"exported_map_{formatted_datetime}.html")
