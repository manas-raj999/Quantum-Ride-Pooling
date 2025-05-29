import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def validate_grid_values(df, grid_cols, grid_size=20):
    print("🧪 Validating grid coordinate ranges...")
    for col in grid_cols:
        min_val = df[col].min()
        max_val = df[col].max()
        print(f"{col}: min={min_val}, max={max_val}")
        if min_val < 0 or max_val >= grid_size:
            print(f"⚠️ Warning: {col} values out of bounds!")
    print()

def plot_scatter(df):
    plt.figure(figsize=(10, 6))
    plt.scatter(df['pickup_x'], df['pickup_y'], alpha=0.5, label='Pickup', s=10)
    plt.scatter(df['dropoff_x'], df['dropoff_y'], alpha=0.5, label='Dropoff', s=10)
    plt.xlabel('Grid X (0-19)')
    plt.ylabel('Grid Y (0-19)')
    plt.title('NYC Taxi Trips Mapped to 20x20 Grid')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_heatmap(df, col_x, col_y, title):
    grid_size = 20
    heatmap, xedges, yedges = np.histogram2d(df[col_x], df[col_y], bins=grid_size, range=[[0, grid_size], [0, grid_size]])
    heatmap = heatmap.T  # transpose to align axes

    plt.figure(figsize=(8, 6))
    plt.imshow(heatmap, origin='lower', cmap='hot', interpolation='nearest')
    plt.colorbar(label='Number of Trips')
    plt.title(title)
    plt.xlabel('Grid X')
    plt.ylabel('Grid Y')
    plt.show()

def plot_pickup_time_histogram(df):
    plt.figure(figsize=(10, 4))
    plt.hist(df['pickup_sec'], bins=24*4, color='blue', alpha=0.7)  # 15-min bins for 24 hrs
    plt.xlabel('Pickup Time (seconds since midnight)')
    plt.ylabel('Number of Trips')
    plt.title('Distribution of Pickup Times')
    plt.grid(True)
    plt.show()

def main():
    filepath = "../data/nyc_taxi/nyc_taxi_mapped.csv"
    print(f"📥 Loading mapped data from {filepath}")
    df = pd.read_csv(filepath)

    # Validate grid values
    grid_columns = ['pickup_x', 'pickup_y', 'dropoff_x', 'dropoff_y']
    validate_grid_values(df, grid_columns, grid_size=20)

    # Scatter plot pickups and dropoffs
    plot_scatter(df)

    # Heatmaps for pickups and dropoffs
    plot_heatmap(df, 'pickup_x', 'pickup_y', 'Heatmap of Pickup Locations on 20x20 Grid')
    plot_heatmap(df, 'dropoff_x', 'dropoff_y', 'Heatmap of Dropoff Locations on 20x20 Grid')

    # Histogram of pickup times
    plot_pickup_time_histogram(df)

if __name__ == "__main__":
    main()
