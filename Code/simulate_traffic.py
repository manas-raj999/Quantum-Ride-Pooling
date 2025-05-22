import traci
import time
import csv
import os
import json

# Load data
with open('../simulations/sumo/ride_requests.csv', 'r') as f:
    rides = list(csv.DictReader(f))
    
with open('../QUBO/vehicle_routes.json', 'r') as f:
    quantum_assignments = json.load(f)

# SUMO configuration
sumo_cmd = [
    "sumo-gui" if os.name == 'nt' else "sumo",
    "-c", "../simulations/sumo/grid.sumocfg",
    "--emission-output", "../simulations/results/emissions_quantum.xml",
    "--tripinfo-output", "../simulations/results/tripinfo_quantum.xml"
]

def create_route(vehicle_id, nodes):
    """Create valid SUMO routes from node sequence"""
    edges = []
    for i in range(len(nodes)-1):
        from_node = nodes[i].replace("_", ",")
        to_node = nodes[i+1].replace("_", ",")
        edge_id = f"edge_{from_node}_to_{to_node}"
        
        # Verify edge exists
        if edge_id not in traci.edge.getIDList():
            print(f"Warning: Edge {edge_id} does not exist! Using shortest path.")
            edges.extend(traci.simulation.findRoute(from_node, to_node).edges)
        else:
            edges.append(edge_id)
            
    traci.route.add(f"route_{vehicle_id}", edges)
    return edges

def assign_quantum_routes():
    """Assign quantum-optimized routes"""
    all_nodes = traci.edge.getIDList()  # Get valid edges
    
    for veh_id, rider_ids in quantum_assignments.items():
        veh_id = f"veh_{veh_id}"
        
        # 1. Build node sequence: depot -> pickups -> dropoffs
        nodes = ["0,0"]  # Start from depot
        
        # Add pickup nodes
        for rider_id in rider_ids:
            pickup = rides[int(rider_id)]['pickup']
            if pickup not in nodes:
                nodes.append(pickup)
                
        # Add dropoff nodes
        for rider_id in rider_ids:
            dropoff = rides[int(rider_id)]['dropoff']
            nodes.append(dropoff)
            
        # 2. Create valid route
        try:
            route_edges = create_route(veh_id, nodes)
            traci.vehicle.add(veh_id, f"route_{veh_id}", typeID="taxi", depart=0)
            traci.vehicle.setPersonCapacity(veh_id, 4)
        except traci.exceptions.TraCIException as e:
            print(f"Failed to create route for {veh_id}: {str(e)}")

# Main simulation
traci.start(sumo_cmd)
print("Valid edges:", traci.edge.getIDList())  # Debugging
assign_quantum_routes()

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    print(f"Time: {traci.simulation.getTime():.1f}s", end="\r")

traci.close()
print("\nSimulation complete!")
