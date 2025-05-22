import random
import csv

rides = []
for i in range(50):
    pickup = (random.randint(0, 3), random.randint(0, 3))   # ← fixed
    dropoff = (random.randint(0, 3), random.randint(0, 3))  # ← fixed
    depart = random.randint(0, 300)  # 0-5 minutes
    rides.append({
        'id': i,
        'pickup': f"{pickup[0]},{pickup[1]}",
        'dropoff': f"{dropoff[0]},{dropoff[1]}",
        'depart': depart
    })

with open('../simulations/sumo/ride_requests.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'pickup', 'dropoff', 'depart'])
    writer.writeheader()
    writer.writerows(rides)
