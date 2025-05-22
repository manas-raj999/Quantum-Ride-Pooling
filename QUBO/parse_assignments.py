import json  

# Load assignments  
with open('quantum_assignments.json', 'r') as f:  
    assignments = json.load(f)  

# Example: { "x[0][0]": 1, "x[0][1]": 0, ... }  
vehicle_to_riders = {j: [] for j in range(10)}  # 10 vehicles  

for var, val in assignments.items():  
    if val == 1:  
        i = int(var.split('[')[1].split(']')[0])  # Extract rider index  
        j = int(var.split('[')[2].split(']')[0])  # Extract vehicle index  
        vehicle_to_riders[j].append(i)  

# Save as {vehicle_0: [rider_3, rider_5], ...}  
with open('vehicle_routes.json', 'w') as f:  
    json.dump(vehicle_to_riders, f)  
