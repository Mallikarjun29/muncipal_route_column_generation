import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from config import NUM_LOCATIONS, CITY_GRID_SIZE

def generate_locations():
    locations = pd.DataFrame({
        "Location_ID": range(1, NUM_LOCATIONS + 1),
        "X_Coordinate": np.random.uniform(0, CITY_GRID_SIZE, NUM_LOCATIONS),
        "Y_Coordinate": np.random.uniform(0, CITY_GRID_SIZE, NUM_LOCATIONS)
    })
    return locations

def compute_distance_matrix(locations):
    coordinates = locations[["X_Coordinate", "Y_Coordinate"]].values
    distance_matrix = cdist(coordinates, coordinates, metric="euclidean")
    return pd.DataFrame(distance_matrix, columns=locations["Location_ID"], index=locations["Location_ID"])

def generate_bins(locations):
    bins = pd.DataFrame({
        "Location_ID": range(1, NUM_LOCATIONS + 1),
        "Waste_Generation_Rate": np.random.uniform(5, 20, size=NUM_LOCATIONS),  # kg/day
        "Bin_Capacity": np.random.uniform(50, 100, size=NUM_LOCATIONS),         # kg
        "Current_Fill_Level": np.random.uniform(30, 90, size=NUM_LOCATIONS)     # %
    })
    bins["Waste_loads"] = bins["Bin_Capacity"] * bins["Current_Fill_Level"] / 100
    return bins

def merge_data(locations, bins):
    dataset = pd.merge(locations, bins, on="Location_ID")
    dataset["Route_Cost"] = dataset.apply(
        lambda row: calculate_route_cost(row["X_Coordinate"], row["Y_Coordinate"]), axis=1
    )
    return dataset


def calculate_route_cost(bin_x, bin_y):
    depot = {"X_Coordinate": 0, "Y_Coordinate": 0}
    distance_to_depot = np.sqrt((bin_x - depot["X_Coordinate"])**2 + (bin_y - depot["Y_Coordinate"])**2)
    return 2 * distance_to_depot  # Round trip

if __name__ == "__main__":
    locations = generate_locations()
    distance_matrix = compute_distance_matrix(locations)
    bins = generate_bins(locations)
    dataset = merge_data(locations, bins)
    
    print(dataset)
    print(distance_matrix)