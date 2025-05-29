import pandas as pd
import os

# --- Configurable Paths ---
TRIP_DATA_PATH = "../data/nyc_taxi/yellow_tripdata_2023-01.parquet"
CENTROIDS_PATH = "../data/nyc_taxi/zone_centroids.csv"
OUTPUT_CLEAN_CSV = "../data/nyc_taxi/nyc_taxi_cleaned.csv"
OUTPUT_MAPPED_CSV = "../data/nyc_taxi/nyc_taxi_mapped.csv"

NYC_BBOX = {
    'min_lon': -74.2591,
    'max_lon': -73.7004,
    'min_lat': 40.4774,
    'max_lat': 40.9176
}

GRID_SIZE = 20
SAMPLE_SIZE = 5000

def load_data(trip_path, centroid_path):
    if not os.path.exists(trip_path):
        raise FileNotFoundError(f"Trip data not found at: {trip_path}")
    trips = pd.read_parquet(trip_path)

    if not os.path.exists(centroid_path):
        raise FileNotFoundError(f"Zone centroid file not found at: {centroid_path}")
    centroids = pd.read_csv(centroid_path)
    
    return trips, centroids

def merge_centroids(trips, centroids):
    df = trips.merge(
        centroids, left_on="PULocationID", right_on="LocationID", how="left"
    ).rename(columns={"lon": "pickup_lon", "lat": "pickup_lat"}).drop(columns=["LocationID"])

    df = df.merge(
        centroids, left_on="DOLocationID", right_on="LocationID", how="left"
    ).rename(columns={"lon": "dropoff_lon", "lat": "dropoff_lat"}).drop(columns=["LocationID"])

    return df

def filter_invalid_rows(df):
    df = df[
        df["pickup_lon"].notna() &
        df["pickup_lat"].notna() &
        df["dropoff_lon"].notna() &
        df["dropoff_lat"].notna() &
        df["trip_distance"].gt(0) &
        df["pickup_lon"].between(NYC_BBOX['min_lon'], NYC_BBOX['max_lon']) &
        df["pickup_lat"].between(NYC_BBOX['min_lat'], NYC_BBOX['max_lat']) &
        df["dropoff_lon"].between(NYC_BBOX['min_lon'], NYC_BBOX['max_lon']) &
        df["dropoff_lat"].between(NYC_BBOX['min_lat'], NYC_BBOX['max_lat'])
    ].copy()
    return df

def add_time_features(df):
    df['pickup_sec'] = (
        df['tpep_pickup_datetime'].dt.hour * 3600 +
        df['tpep_pickup_datetime'].dt.minute * 60 +
        df['tpep_pickup_datetime'].dt.second
    )
    df['dropoff_sec'] = (
        df['tpep_dropoff_datetime'].dt.hour * 3600 +
        df['tpep_dropoff_datetime'].dt.minute * 60 +
        df['tpep_dropoff_datetime'].dt.second
    )
    return df

def normalize_coordinates(df):
    df['norm_pickup_lon'] = (df['pickup_lon'] - NYC_BBOX['min_lon']) / (NYC_BBOX['max_lon'] - NYC_BBOX['min_lon'])
    df['norm_pickup_lat'] = (df['pickup_lat'] - NYC_BBOX['min_lat']) / (NYC_BBOX['max_lat'] - NYC_BBOX['min_lat'])
    df['norm_dropoff_lon'] = (df['dropoff_lon'] - NYC_BBOX['min_lon']) / (NYC_BBOX['max_lon'] - NYC_BBOX['min_lon'])
    df['norm_dropoff_lat'] = (df['dropoff_lat'] - NYC_BBOX['min_lat']) / (NYC_BBOX['max_lat'] - NYC_BBOX['min_lat'])
    return df

def map_to_grid(df, grid_size):
    df['pickup_x'] = (df['norm_pickup_lon'] * grid_size).astype(int)
    df['pickup_y'] = (df['norm_pickup_lat'] * grid_size).astype(int)
    df['dropoff_x'] = (df['norm_dropoff_lon'] * grid_size).astype(int)
    df['dropoff_y'] = (df['norm_dropoff_lat'] * grid_size).astype(int)
    
    # Filter trips with grid coordinates out of bounds
    df = df[
        df['pickup_x'].between(0, grid_size - 1) &
        df['pickup_y'].between(0, grid_size - 1) &
        df['dropoff_x'].between(0, grid_size - 1) &
        df['dropoff_y'].between(0, grid_size - 1)
    ]
    return df

def sample_trips(df, sample_size):
    return df.sample(n=sample_size, random_state=42)

def save_outputs(df, clean_path, mapped_path):
    df.to_csv(clean_path, index=False)
    mapped_columns = ['pickup_x', 'pickup_y', 'dropoff_x', 'dropoff_y', 'pickup_sec']
    df[mapped_columns].to_csv(mapped_path, index=False)

def main():
    print("🚕 Loading NYC Taxi data...")
    trips, centroids = load_data(TRIP_DATA_PATH, CENTROIDS_PATH)

    print("📍 Merging with zone centroids...")
    df = merge_centroids(trips, centroids)

    print("🧹 Cleaning and filtering data...")
    df = filter_invalid_rows(df)

    print("⏱️ Adding time and coordinate features...")
    df = add_time_features(df)
    df = normalize_coordinates(df)

    print(f"🗺️ Mapping to {GRID_SIZE}x{GRID_SIZE} grid...")
    df = map_to_grid(df, GRID_SIZE)

    print(f"🎲 Sampling {SAMPLE_SIZE} trips...")
    df = sample_trips(df, SAMPLE_SIZE)

    print("💾 Saving processed data...")
    save_outputs(df, OUTPUT_CLEAN_CSV, OUTPUT_MAPPED_CSV)

    print(f"✅ Cleaned data saved to {OUTPUT_CLEAN_CSV}")
    print(f"✅ Grid-mapped data saved to {OUTPUT_MAPPED_CSV}")

if __name__ == "__main__":
    main()
