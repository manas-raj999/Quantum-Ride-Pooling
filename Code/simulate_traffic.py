"""
SUMO Traffic Simulation with Quantum Optimization Integration
Handles both synthetic and NYC taxi datasets
"""

import os
import time
import argparse
import traci
import pandas as pd
import json

# ======================
# Configuration
# ======================
SIMULATION_STEP = 1.0  # Seconds per simulation step
VEHICLE_CAPACITY = 4   # Max passengers per vehicle
NUM_VEHICLES = 10     # Total vehicles in simulation

# ======================
# Command-line Arguments
# ======================
parser = argparse.ArgumentParser(description='Run SUMO traffic simulation')
parser.add_argument('--grid', type=str, default='synthetic', 
                   choices=['synthetic', 'nyc'], 
                   help='Grid type: synthetic (4x4) or nyc (20x20)')
parser.add_argument('--algorithm', type=str, default='greedy',
                   choices=['greedy', 'quantum'],
                   help='Routing algorithm to use')
parser.add_argument('--output', type=str, default='results',
                   help='Output folder name for results')
args = parser.parse_args()

# ======================
# File Paths
# ======================
if args.grid == 'nyc':
    GRID_SIZE = 20
    sumo_config = "../simulations/SUMO/nyc/nyc_grid.sumocfg"
    trip_data_path = "../data/nyc_taxi/nyc_taxi_mapped.csv"
    quantum_assignments_path = "../QUBO/quantum_assignments.json"
else:
    GRID_SIZE = 4
    sumo_config = "../simulations/SUMO/grid.sumocfg"
    trip_data_path = "../simulations/SUMO/ride_requests.csv"
    quantum_assignments_path = "../QUBO/synthetic_assignments.json"

# ======================
# Load Trip Data
# ======================
try:
    df = pd.read_csv(trip_data_path)
    sample_size = min(len(df), 5000)  # Avoid ValueError
    trips = df.sample(sample_size, replace=False)
    print(f"✅ Loaded {len(trips)} trips from {trip_data_path}")
except FileNotFoundError:
    print(f"❌ Error: Trip data not found at {trip_data_path}")
    exit(1)


# ======================
# SUMO Initialization
# ======================
def initialize_sumo():
    """Start SUMO connection with proper configuration"""
    sumo_cmd = [
        "sumo-gui" if os.name == 'nt' else "sumo",
        "-c", sumo_config,
        "--emission-output", f"../simulations/results/emissions.xml",
        "--tripinfo-output", f"../simulations/results/tripinfo.xml",
        "--waiting-time-memory", "10000"  # Track waiting times over 10k steps
    ]
    
    traci.start(sumo_cmd)
    print(f"🚦 SUMO initialized with {args.grid} grid")

# ======================
# Vehicle Management
# ======================
def add_vehicles():
    """Initialize vehicles at central depot"""
    depot_node = "node100" if args.grid == 'nyc' else "node0"
    
    for veh_id in range(NUM_VEHICLES):
        traci.route.add(f"route_{veh_id}", [depot_node])
        traci.vehicle.add(f"veh_{veh_id}", f"route_{veh_id}")
        traci.vehicle.setPersonCapacity(f"veh_{veh_id}", VEHICLE_CAPACITY)
        traci.vehicle.setColor(f"veh_{veh_id}", (0, 255, 0, 255))  # Green

# ======================
# Routing Algorithms
# ======================
def greedy_assignment():
    """Classical greedy algorithm for baseline comparison"""
    for trip in trips.itertuples():
        best_veh = None
        min_dist = float('inf')
        
        for veh_id in traci.vehicle.getIDList():
            if traci.vehicle.getPersonCapacity(veh_id) > 0:
                veh_pos = traci.vehicle.getPosition(veh_id)
                dx = abs(veh_pos[0] - trip.pickup_x)
                dy = abs(veh_pos[1] - trip.pickup_y)
                dist = dx + dy  # Manhattan distance
                
                if dist < min_dist:
                    min_dist = dist
                    best_veh = veh_id
        
        if best_veh:
            assign_ride(best_veh, trip)

def quantum_assignment():
    """Load quantum-optimized vehicle assignments"""
    try:
        with open(quantum_assignments_path, 'r') as f:
            assignments = json.load(f)
            print(f"✅ Loaded quantum assignments for {len(assignments)} vehicles")
    except FileNotFoundError:
        print(f"❌ Error: Quantum assignments not found at {quantum_assignments_path}")
        exit(1)

    for veh_id, rider_ids in assignments.items():
        for rider_id in rider_ids:
            trip = trips.iloc[rider_id]
            assign_ride(veh_id, trip)

def assign_ride(veh_id, trip):
    """Update vehicle route for a single ride"""
    pickup_node = f"node{trip.pickup_x}{trip.pickup_y}"
    dropoff_node = f"node{trip.dropoff_x}{trip.dropoff_y}"
    
    try:
        traci.vehicle.changeTarget(veh_id, pickup_node)
        traci.vehicle.changeTarget(veh_id, dropoff_node)
        traci.vehicle.setPersonCapacity(veh_id, 
            traci.vehicle.getPersonCapacity(veh_id) - 1)
    except traci.TraCIException:
        print(f"⚠️ Failed to assign ride to vehicle {veh_id}")

# ======================
# Main Simulation Loop
# ======================
def run_simulation():
    """Execute the traffic simulation"""
    start_time = time.time()
    step = 0
    
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        # Assign rides at first step for quantum, dynamically for greedy
        if step == 0 and args.algorithm == 'quantum':
            quantum_assignment()
        elif args.algorithm == 'greedy':
            greedy_assignment()
        
        step += 1
        if step % 100 == 0:
            print(f"⏱ Simulation step {step} | Running vehicles: {len(traci.vehicle.getIDList())}")

    print(f"⏱ Simulation completed in {time.time()-start_time:.2f} seconds")

# ======================
# Execution
# ======================
if __name__ == "__main__":
    initialize_sumo()
    add_vehicles()
    run_simulation()
    traci.close()
