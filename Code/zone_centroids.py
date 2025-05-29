import geopandas as gpd
from pyproj import CRS

# Load shapefile in its original CRS (EPSG:2263)
zones = gpd.read_file("../data/nyc_taxi/taxi_zones/taxi_zones.shp")

# Project to a suitable projected CRS (e.g., EPSG:2263 if not already)
zones_proj = zones.to_crs(CRS("EPSG:2263"))

# Calculate centroids in projected CRS
zones_proj['centroid'] = zones_proj.geometry.centroid

# Convert centroids to WGS84
centroids_wgs84 = gpd.GeoSeries(zones_proj['centroid'], crs="EPSG:2263").to_crs("EPSG:4326")

# Extract lon/lat
zones['lon'] = centroids_wgs84.x
zones['lat'] = centroids_wgs84.y

# Save to CSV
zones[['LocationID', 'lon', 'lat']].to_csv("../data/nyc_taxi/zone_centroids.csv", index=False)
