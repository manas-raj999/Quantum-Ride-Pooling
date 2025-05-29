"""
QUBO Solver for Ride-Pooling Optimization using Simulated Annealing (neal)
"""

import json
import time
import argparse
import re
import numpy as np
import dimod
from neal import SimulatedAnnealingSampler

# ======================
# Configuration
# ======================
DEFAULT_NUM_READS = 1000
QUBO_FILE = "../Data/qubo.json"
RESULTS_FILE = "../Data/assignments.json"

# ======================
# QUBO Loader
# ======================
def load_qubo(file_path: str) -> dimod.BinaryQuadraticModel:
    """Load QUBO from JSON file and convert to dimod.BQM"""
    with open(file_path, 'r') as f:
        qubo_dict = json.load(f)
    
    # Convert string keys back to tuples
    qubo = {}
    for key_str, value in qubo_dict.items():
        # The QUBO JSON keys might be string representations of tuples like "(16,3)"
        # but if your keys are like 'x[16][3]', eval won't work properly.
        # So let's handle both cases:
        try:
            # Try to eval key (for keys like "(16, 3)")
            key = eval(key_str)
        except:
            # If fails, fallback to parsing 'x[16][3]' style keys
            pattern = re.compile(r"x\[(\d+)\]\[(\d+)\]")
            m = pattern.match(key_str)
            if m:
                key = (int(m.group(1)), int(m.group(2)))
            else:
                raise ValueError(f"Cannot parse QUBO key: {key_str}")
        qubo[key] = value
    
    # Create BinaryQuadraticModel
    bqm = dimod.BinaryQuadraticModel.from_qubo(qubo)
    return bqm

# ======================
# Solution Processing
# ======================
def interpret_solution(sample: dict, riders: int, vehicles: int) -> dict:
    """Convert binary solution to rider-vehicle assignments"""
    assignments = {j: [] for j in range(vehicles)}
    pattern = re.compile(r"x\[(\d+)\]\[(\d+)\]")  # matches keys like x[16][3]
    
    for key_str, val in sample.items():
        if val == 1:
            m = pattern.match(key_str)
            if m:
                i = int(m.group(1))
                j = int(m.group(2))
                assignments[j].append(i)
            else:
                print(f"Warning: could not parse variable name '{key_str}'")
    return assignments

def validate_solution(assignments: dict, riders: int) -> bool:
    """Check if solution meets all constraints"""
    # Check all riders are assigned exactly once
    assigned_riders = set()
    for vehicle, rider_list in assignments.items():
        assigned_riders.update(rider_list)
    
    return len(assigned_riders) == riders

# ======================
# Helper: Convert numpy types for JSON serialization
# ======================
def convert_types(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {convert_types(k): convert_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_types(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    else:
        return obj

# ======================
# Result Saving
# ======================
def save_results(results: dict, file_path: str):
    """Save results to JSON file"""
    with open(file_path, 'w') as f:
        clean_results = convert_types(results)
        json.dump(clean_results, f, indent=2)

# ======================
# Main Execution
# ======================
def main():
    parser = argparse.ArgumentParser(description="Solve QUBO model using simulated annealing (neal).")
    parser.add_argument('--qubo-file', type=str, default=QUBO_FILE,
                       help="Path to QUBO JSON file")
    parser.add_argument('--riders', type=int, required=True,
                       help="Number of riders (for solution interpretation)")
    parser.add_argument('--vehicles', type=int, required=True,
                       help="Number of vehicles (for solution interpretation)")
    parser.add_argument('--num-reads', type=int, default=DEFAULT_NUM_READS,
                       help="Number of reads for simulated annealing")
    parser.add_argument('--output', type=str, default=RESULTS_FILE,
                       help="Output file path for results")
    args = parser.parse_args()

    # Load QUBO model
    print(f"🔍 Loading QUBO from {args.qubo_file}")
    bqm = load_qubo(args.qubo_file)
    
    # Solve with simulated annealing
    print("⚙️ Solving with simulated annealing (neal)...")
    start_time = time.time()
    
    sampler = SimulatedAnnealingSampler()
    sampleset = sampler.sample(bqm, num_reads=args.num_reads)
    
    solve_time = time.time() - start_time
    
    # Get best solution
    best_sample = sampleset.first.sample
    energy = sampleset.first.energy
    
    # Interpret solution
    assignments = interpret_solution(best_sample, args.riders, args.vehicles)
    is_valid = validate_solution(assignments, args.riders)
    
    # Prepare results
    results = {
        "solver": "simulated_annealing",
        "solve_time_sec": solve_time,
        "energy": energy,
        "is_valid": is_valid,
        "assignments": assignments,
        "num_reads": args.num_reads,
        "sampleset_info": {
            "num_occurrences": sampleset.first.num_occurrences,
            "chain_break_fraction": sampleset.info.get('chain_break_fraction', None)
        }
    }
    
    # Save results
    save_results(results, args.output)
    print(f"✅ Solution saved to {args.output}")
    print(f"   Solve time  : {solve_time:.2f} sec")
    print(f"   Energy      : {energy}")
    print(f"   Valid       : {'Yes' if is_valid else 'No'}")
    print(f"   Assignments : {assignments}")

if __name__ == "__main__":
    main()
