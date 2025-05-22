import neal  
import json  
import numpy as np  

# Load QUBO  
with open('qubo.json', 'r') as f:  
    qubo_strkeys = json.load(f)  
    qubo = {eval(k): v for k, v in qubo_strkeys.items()}  

# Solve with simulated annealing  
sampler = neal.SimulatedAnnealingSampler()  
response = sampler.sample_qubo(qubo, num_reads=100)  
solution = response.first.sample  

# Convert numpy.int8 to Python int for JSON compatibility  
solution_converted = {k: int(v) for k, v in solution.items()}  # Fix here

# Save solution  
with open('quantum_assignments.json', 'w') as f:  
    json.dump(solution_converted, f)  # Use converted solution
print("Assignments saved successfully!")
