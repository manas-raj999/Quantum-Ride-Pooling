import traci
import time
import csv
import os
import json

def coord_to_node(coord):
    x, y = map(int, coord.split(','))
    return chr(ord('A') + x) + str(y)

def get_outgoing_edges(node, edge_list):
    # SUMO edge IDs are like A0A1, A1A2, etc. (not internal edges starting with ":")
    return [e for e in edge_list if e.startswith(node) and not e.startswith(":")]

def create_route(vehicle_id, node_list, edge_list):
    """Create a valid SUMO route from a sequence of node IDs using shortest paths."""
    edges = []
    for i in range(len(node_list) - 1):
        from_node = node_list[i]
        to_node = node_list[i + 1]
        from_edges = get_outgoing_edges(from_node, edge_list)
        to_edges = get_outgoing_edges(to_node, edge_list)
        if not from_edges or not to_edges:
            raise Exception(f"No outgoing edges from {from_node} or {to_node}")
        # Use first outgoing edge as start, first outgoing as end
        from_edge = from_edges[0]
        to_edge = to_edges[0]
        route = traci.simulation.findRoute(from_edge, to_edge)
        if not route.edges:
            raise Exception(f"No route from {from_edge} to {to_edge}")
        # Avoid duplicate edges when concatenating
        if edges and route.edges[0] == edges[-1]:
            edges.extend(route.edges[1:])
        else:
            edges.extend(route.edges)
    traci.route.add(f"route_{vehicle_id}", edges)
    return edges

# Load data
with open('../simulations/sumo/ride_requests.csv', 'r') as f:
    rides = list(csv.DictReader(f))

with open('../QUBO/vehicle_routes.json', 'r') as f:
    quantum_assignments = json.load(f)

sumo_cmd = [
    "sumo-gui" if os.name == 'nt' else "sumo",
    "-c", "../simulations/sumo/grid.sumocfg",
    "--emission-output", "../simulations/results/emissions_quantum.xml",
    "--tripinfo-output", "../simulations/results/tripinfo_quantum.xml"
]

def assign_quantum_routes():
    edge_list = traci.edge.getIDList()
    for veh_id, rider_ids in quantum_assignments.items():
        veh_id_str = f"veh_{veh_id}"
        # Build node sequence: depot -> pickups -> dropoffs
        nodes = [coord_to_node("0,0")]  # Start from depot at A0
        for rider_id in rider_ids:
            pickup = rides[int(rider_id)]['pickup']
            pickup_node = coord_to_node(pickup)
            if pickup_node not in nodes:
                nodes.append(pickup_node)
        for rider_id in rider_ids:
            dropoff = rides[int(rider_id)]['dropoff']
            dropoff_node = coord_to_node(dropoff)
            nodes.append(dropoff_node)
        try:
            route_edges = create_route(veh_id_str, nodes, edge_list)
            traci.vehicle.add(veh_id_str, f"route_{veh_id_str}", typeID="taxi", depart=0)
            # traci.vehicle.setPersonCapacity(veh_id_str, 4)
        except Exception as e:
            print(f"Failed to create route for {veh_id_str}: {str(e)}")

# Main simulation
traci.start(sumo_cmd)
assign_quantum_routes()

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    print(f"Time: {traci.simulation.getTime():.1f}s", end="\r")

traci.close()
print("\nSimulation complete!")
