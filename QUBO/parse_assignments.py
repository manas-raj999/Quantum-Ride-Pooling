"""
Vehicle Route Parser for Ride-Pooling Assignments
"""

import json
import argparse
import pandas as pd
from typing import Dict, List, Tuple
from collections import defaultdict

# ======================
# Configuration
# ======================
NYC_DATA_PATH = "../Data/nyc_taxi/nyc_taxi_mapped.csv"
ASSIGNMENTS_FILE = "../Data/nyc_assignments.json"
OUTPUT_FILE = "../Data/routes_nyc.json"
GRID_TO_KM = 0.5  # Should match qubo_model.py
AVG_SPEED = 10     # m/s (should match qubo_model.py)

# ======================
# Data Loaders
# ======================
def load_nyc_data() -> pd.DataFrame:
    """Load and preprocess NYC taxi data"""
    df = pd.read_csv(NYC_DATA_PATH)
    # Convert grid coordinates to km
    for col in ['pickup_x', 'pickup_y', 'dropoff_x', 'dropoff_y']:
        df[col] = df[col] * GRID_TO_KM
    return df

def load_assignments(file_path: str) -> Dict[int, List[int]]:
    """Load vehicle assignments from solver output"""
    with open(file_path, 'r') as f:
        results = json.load(f)
    return results['assignments']

# ======================
# Route Optimization
# ======================
def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate Manhattan distance between two points"""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def optimize_route(pickups: List[Tuple[float, float]], 
                 dropoffs: List[Tuple[float, float]]) -> List[int]:
    """
    Simple route optimization using nearest neighbor algorithm
    Returns ordered list of rider indices for optimal pickup/dropoff sequence
    """
    if not pickups:
        return []
    
    # Combine all points with type (pickup=0, dropoff=1)
    points = [(p, 0, i) for i, p in enumerate(pickups)] + \
             [(d, 1, i) for i, d in enumerate(dropoffs)]
    
    route = []
    current_pos = (0, 0)  # Starting at origin (can be modified to vehicle's initial position)
    remaining_points = set(range(len(points)))
    
    while remaining_points:
        # Find nearest point
        nearest = min(
            remaining_points,
            key=lambda i: calculate_distance(current_pos, points[i][0])
        )
        
        route.append(nearest)
        current_pos = points[nearest][0]
        remaining_points.remove(nearest)
        
        # If this is a pickup, ensure we don't drop off before pickup
        if points[nearest][1] == 0:  # pickup
            # Find corresponding dropoff
            rider_idx = points[nearest][2]
            dropoff_idx = next(
                i for i, (_, typ, idx) in enumerate(points) 
                if typ == 1 and idx == rider_idx
            )
            if dropoff_idx in remaining_points:
                # Temporarily remove other dropoffs for this rider (shouldn't exist)
                remaining_points = {
                    i for i in remaining_points 
                    if not (points[i][1] == 1 and points[i][2] == rider_idx)
                }
                remaining_points.add(dropoff_idx)
    
    return route

# ======================
# Route Processing
# ======================
def process_vehicle_route(vehicle_id: int, 
                        rider_indices: List[int], 
                        df: pd.DataFrame) -> Dict:
    """Generate complete route information for one vehicle"""
    if not rider_indices:
        return {
            "vehicle_id": vehicle_id,
            "route": [],
            "total_distance": 0,
            "estimated_time": 0,
            "riders": []
        }
    
    # Get pickup and dropoff locations for each rider
    pickups = []
    dropoffs = []
    rider_data = []
    
    for rider_idx in rider_indices:
        row = df.iloc[rider_idx]
        pickups.append((row['pickup_x'], row['pickup_y']))
        dropoffs.append((row['dropoff_x'], row['dropoff_y']))
        rider_data.append({
            "rider_id": rider_idx,
            "pickup": {"x": row['pickup_x'], "y": row['pickup_y']},
            "dropoff": {"x": row['dropoff_x'], "y": row['dropoff_y']},
            "request_time": row['pickup_sec']
        })
    
    # Optimize route
    route_indices = optimize_route(pickups, dropoffs)
    
    # Reconstruct full route with points and actions
    route_points = []
    total_distance = 0
    current_pos = (0, 0)  # Starting at origin
    
    for idx in route_indices:
        point_type = "pickup" if idx < len(pickups) else "dropoff"
        rider_idx = idx if point_type == "pickup" else idx - len(pickups)
        point = pickups[rider_idx] if point_type == "pickup" else dropoffs[rider_idx]
        
        # Add distance to this point
        distance = calculate_distance(current_pos, point)
        total_distance += distance
        
        route_points.append({
            "type": point_type,
            "rider_id": rider_idx,
            "x": point[0],
            "y": point[1],
            "distance_from_previous": distance
        })
        
        current_pos = point
    
    estimated_time = total_distance * 1000 / AVG_SPEED  # Convert km to m and divide by speed
    
    return {
        "vehicle_id": vehicle_id,
        "route": route_points,
        "total_distance": total_distance,
        "estimated_time": estimated_time,
        "riders": rider_data
    }

# ======================
# Main Execution
# ======================
def main():
    parser = argparse.ArgumentParser(description="Generate vehicle routes from assignments.")
    parser.add_argument('--assignments', type=str, default=ASSIGNMENTS_FILE,
                       help="Path to assignments JSON file")
    parser.add_argument('--nyc-data', type=str, default=NYC_DATA_PATH,
                       help="Path to NYC taxi data CSV")
    parser.add_argument('--output', type=str, default=OUTPUT_FILE,
                       help="Output file path for routes")
    args = parser.parse_args()

    # Load data
    print("📊 Loading data...")
    df = load_nyc_data()
    assignments = load_assignments(args.assignments)
    
    # Process each vehicle's route
    print("🚗 Generating routes...")
    routes = []
    for vehicle_id, rider_indices in assignments.items():
        route = process_vehicle_route(int(vehicle_id), rider_indices, df)
        routes.append(route)
        print(f"  Vehicle {vehicle_id}: {len(rider_indices)} riders, "
              f"{route['total_distance']:.1f} km, {route['estimated_time']/60:.1f} min")
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(routes, f, indent=2)
    
    print(f"✅ Routes saved to {args.output}")

if __name__ == "__main__":
    main()
