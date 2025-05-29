"""
QUBO Model with Real-World NYC Taxi Data Integration
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from pyqubo import Array, Constraint
import re

# ======================
# Configuration
# ======================
NYC_DATA_PATH = "../Data/nyc_taxi/nyc_taxi_mapped.csv"
DEFAULT_PENALTY = 5000
MAX_CAPACITY = 4
MAX_WAIT_TIME = 600   # seconds (10 minutes)
AVG_SPEED = 10        # m/s
GRID_TO_KM = 0.5
GRID_SIZE = 20        # For spatial normalization if needed

# ======================
# Data Loaders
# ======================
def load_distance_matrix(riders: int, vehicles: int) -> np.ndarray:
    df = pd.read_csv(NYC_DATA_PATH).head(riders)
    distances = [
        (abs(row['pickup_x'] - row['dropoff_x']) + abs(row['pickup_y'] - row['dropoff_y'])) * GRID_TO_KM
        for _, row in df.iterrows()
    ]
    return np.tile(distances, (vehicles, 1)).T

def load_wait_time_matrix(riders: int, vehicles: int) -> np.ndarray:
    df = pd.read_csv(NYC_DATA_PATH).head(riders)
    base_time = df['pickup_sec'].median()
    wait_times = np.abs(df['pickup_sec'] - base_time)
    return np.tile(wait_times, (vehicles, 1)).T

# ======================
# Helper: Extract indices from pyqubo var names like 'x[3][5]'
# ======================
def extract_indices(var_name: str):
    """
    Extract integer indices from variable name string.
    Example: 'x[3][5]' -> (3, 5)
    """
    matches = re.findall(r'\[(\d+)\]', var_name)
    return tuple(int(m) for m in matches)

# ======================
# Format QUBO keys to stringified tuples
# ======================
def format_qubo_keys(qubo: dict) -> dict:
    """
    Convert QUBO dict keys like 'x[i][j]' or tuples to string keys like '(i, j)'.
    """
    formatted_qubo = {}
    for key, val in qubo.items():
        if isinstance(key, tuple):
            # Keys already tuples - convert to string
            formatted_key = str(key)
        elif isinstance(key, str):
            # Extract indices from string keys
            indices = extract_indices(key)
            formatted_key = str(indices)
        else:
            # Fallback: convert key to string
            formatted_key = str(key)
        formatted_qubo[formatted_key] = val
    return formatted_qubo

# ======================
# QUBO Model Builder
# ======================
def build_qubo_model(riders: int, vehicles: int, use_real_data: bool = False):
    x = Array.create('x', shape=(riders, vehicles), vartype='BINARY')

    if use_real_data:
        distance_matrix = load_distance_matrix(riders, vehicles)
        time_matrix = load_wait_time_matrix(riders, vehicles)
    else:
        np.random.seed(42)
        distance_matrix = np.random.randint(1, 10, size=(riders, vehicles))
        time_matrix = np.random.randint(0, 600, size=(riders, vehicles))

    # Objective: Minimize total distance
    distance_term = sum(
        distance_matrix[i][j] * x[i][j]
        for i in range(riders)
        for j in range(vehicles)
    )

    # Constraint 1: Each rider is assigned to exactly one vehicle
    assignment_constraints = sum(
        Constraint((sum(x[i][j] for j in range(vehicles)) - 1) ** 2, label=f"assign_{i}")
        for i in range(riders)
    )

    # Constraint 2: Each vehicle does not exceed max capacity
    capacity_constraints = sum(
        Constraint((sum(x[i][j] for i in range(riders)) - MAX_CAPACITY) ** 2, label=f"cap_{j}")
        for j in range(vehicles)
    )

    # Constraint 3: Penalize riders waiting beyond max time (soft constraint)
    time_penalty_term = sum(
        Constraint(((time_matrix[i][j] - MAX_WAIT_TIME) ** 2) * x[i][j], label=f"time_{i}_{j}")
        for i in range(riders)
        for j in range(vehicles)
        if time_matrix[i][j] > MAX_WAIT_TIME
    )

    # Compile and convert to QUBO
    model = distance_term + DEFAULT_PENALTY * (assignment_constraints + capacity_constraints + time_penalty_term)
    compiled_model = model.compile()
    qubo, offset = compiled_model.to_qubo()

    return qubo, offset

# ======================
# Entry Point
# ======================
def main():
    parser = argparse.ArgumentParser(description="Generate QUBO model from real or synthetic data.")
    parser.add_argument('--riders', type=int, default=50, help="Number of riders")
    parser.add_argument('--vehicles', type=int, default=10, help="Number of vehicles")
    parser.add_argument('--real-data', action='store_true', help="Use real NYC taxi data")
    parser.add_argument('--output', type=str, default="../Quantum_Ride_Pooling/Data/qubo.json", help="Output file path")
    args = parser.parse_args()

    if args.real_data and not os.path.exists(NYC_DATA_PATH):
        raise FileNotFoundError(f"NYC data not found at {NYC_DATA_PATH}")

    # Build and compile model
    qubo, offset = build_qubo_model(args.riders, args.vehicles, args.real_data)

    # Format QUBO keys for JSON serialization
    formatted_qubo = format_qubo_keys(qubo)

    # Save to JSON
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(formatted_qubo, f, indent=2)

    print(f"✅ QUBO model generated with {len(qubo)} terms")
    print(f"   Riders     : {args.riders}")
    print(f"   Vehicles   : {args.vehicles}")
    print(f"   Real data  : {'Yes' if args.real_data else 'No'}")
    print(f"   Saved to   : {os.path.abspath(args.output)}")
    print(f"   Offset     : {offset}")

if __name__ == "__main__":
    main()
