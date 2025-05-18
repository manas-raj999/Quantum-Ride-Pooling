from pyqubo import Binary, Array, Constraint
import numpy as np
import json

# Step 1: Define Variables
# -------------------------
# 50 riders, 10 vehicles
riders = 50
vehicles = 10

# Binary variables: x[i][j] = 1 if rider i is assigned to vehicle j
x = Array.create('x', shape=(riders, vehicles), vartype='BINARY')

# Step 2: Define Distance Cost
# ----------------------------
np.random.seed(42)  # For reproducibility
distance_matrix = np.random.randint(1, 10, size=(riders, vehicles))  # Random distances (1-10 km)

distance_cost = sum(
    distance_matrix[i][j] * x[i][j]
    for i in range(riders)
    for j in range(vehicles)
)

# Step 3: Add Constraints
# ------------------------
# Constraint 1: Vehicle capacity (max 4 riders)
capacity_penalty = 1000 * sum(
    Constraint((sum(x[i][j] for i in range(riders)) - 4)**2, f'cap_{j}')
    for j in range(vehicles)
)

# Constraint 2: Time windows (max 5-minute wait)
time_matrix = np.random.randint(0, 10, size=(riders, vehicles))  # Random wait times (0-10 mins)
time_penalty = 1000 * sum(
    Constraint((time_matrix[i][j] - 5)**2 * x[i][j], f'time_{i}_{j}')
    for i in range(riders)
    for j in range(vehicles)
)

# Step 4: Compile the QUBO
# -------------------------
model = distance_cost + capacity_penalty + time_penalty
qubo, offset = model.compile().to_qubo()

# Step 5: Save or Print the QUBO
# ------------------------------
serializable_qubo = {str(k): v for k, v in qubo.items()}

with open('qubo.json', 'w') as f:
    json.dump(serializable_qubo, f)

print("QUBO saved to qubo.json!")
