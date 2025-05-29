"""
Interactive Route Visualization for Quantum Ride-Pooling
"""

import json
import folium
from branca.colormap import linear
from typing import List, Dict
import argparse

# ======================
# Configuration
# ======================
DEFAULT_ROUTES_FILE = "../Data/routes_nyc.json"
DEFAULT_OUTPUT_FILE = "../Visualization/routes_map.html"
NYC_CENTER = [40.7128, -74.0060]  # Latitude, Longitude of NYC
GRID_SCALE = 0.01  # Degrees per grid unit (adjust based on your coordinate system)

# ======================
# Coordinate Conversion
# ======================
def grid_to_latlong(x: float, y: float) -> List[float]:
    """Convert grid coordinates to approximate lat/long (mock conversion)"""
    return [
        NYC_CENTER[0] + y * GRID_SCALE,  # Latitude
        NYC_CENTER[1] + x * GRID_SCALE   # Longitude
    ]

# ======================
# Route Processing
# ======================
def load_routes(routes_file: str) -> List[Dict]:
    """Load processed routes from JSON"""
    with open(routes_file, 'r') as f:
        return json.load(f)

def generate_vehicle_colors(num_vehicles: int) -> Dict[int, str]:
    """Generate distinct colors for each vehicle"""
    colormap = linear.viridis.scale(0, max(num_vehicles - 1, 1))
    return {i: colormap(i) for i in range(num_vehicles)}

# ======================
# Visualization
# ======================
def create_base_map() -> folium.Map:
    """Create folium map centered on NYC"""
    return folium.Map(
        location=NYC_CENTER,
        zoom_start=12,
        tiles="cartodbpositron",
        control_scale=True
    )

def add_route_to_map(m: folium.Map, route: Dict, color: str):
    """Add a single vehicle route to the map"""
    points = []
    pickup_icons = []
    dropoff_icons = []
    
    # Convert all route points to lat/long
    for stop in route['route']:
        latlong = grid_to_latlong(stop['x'], stop['y'])
        points.append(latlong)
        
        # Create markers for pickups/dropoffs
        if stop['type'] == 'pickup':
            pickup_icons.append(latlong)
        else:
            dropoff_icons.append(latlong)
    
    # Add the route line
    folium.PolyLine(
        points,
        color=color,
        weight=3,
        opacity=0.8,
        tooltip=f"Vehicle {route['vehicle_id']} - {len(route['riders'])} riders"
    ).add_to(m)
    
    # Add pickup markers
    for point in pickup_icons:
        folium.Marker(
            point,
            icon=folium.Icon(icon='arrow-up', color='green', prefix='fa'),
            tooltip="Pickup"
        ).add_to(m)
    
    # Add dropoff markers
    for point in dropoff_icons:
        folium.Marker(
            point,
            icon=folium.Icon(icon='arrow-down', color='red', prefix='fa'),
            tooltip="Dropoff"
        ).add_to(m)
    
    # Add start/end markers
    if points:
        folium.Marker(
            points[0],
            icon=folium.Icon(icon='play', color='blue', prefix='fa'),
            tooltip="Start"
        ).add_to(m)
        
        folium.Marker(
            points[-1],
            icon=folium.Icon(icon='stop', color='black', prefix='fa'),
            tooltip="End"
        ).add_to(m)

def add_legend(m: folium.Map, colors: Dict[int, str]):
    """Add color legend to the map"""
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 150px; 
                border:2px solid grey; z-index:9999; 
                font-size:14px; background-color:white;
                padding: 10px">
        <b>Vehicle Colors</b><br>
    '''
    
    for vehicle_id, color in colors.items():
        legend_html += f'''
        <i style="background:{color}; width:15px; height:15px; 
                   display:inline-block; margin-right:5px;"></i>
        Vehicle {vehicle_id}<br>
        '''
    
    legend_html += '</div>'
    
    m.get_root().html.add_child(folium.Element(legend_html))

# ======================
# Main Execution
# ======================
def main():
    parser = argparse.ArgumentParser(description="Visualize ride-pooling routes.")
    parser.add_argument('--routes', type=str, default=DEFAULT_ROUTES_FILE,
                       help="Path to routes JSON file")
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_FILE,
                       help="Output HTML file path")
    args = parser.parse_args()

    print("🌍 Loading routes data...")
    routes = load_routes(args.routes)
    
    print(f"🚗 Generating colors for {len(routes)} vehicles...")
    colors = generate_vehicle_colors(len(routes))
    
    print("🖌️ Creating map visualization...")
    m = create_base_map()
    
    for route in routes:
        # Defensive check: vehicle_id should be an integer and in colors keys
        vid = route.get('vehicle_id')
        color = colors.get(vid, '#000000')  # fallback black if missing
        add_route_to_map(m, route, color)
    
    add_legend(m, colors)
    
    print("💾 Saving map...")
    m.save(args.output)
    print(f"✅ Visualization saved to {args.output}")
    print(f"   Vehicles: {len(routes)}")
    print(f"   Total Riders: {sum(len(r['riders']) for r in routes)}")

if __name__ == "__main__":
    main()
