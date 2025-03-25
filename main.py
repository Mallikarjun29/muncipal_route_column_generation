import pandas as pd
from generate_instances import generate_locations, compute_distance_matrix, generate_bins, merge_data
from rmp_solver import initialize_rmp, solve_rmp, add_new_routes_to_rmp
from config import TRUCK_CAPACITY
from scipy.spatial.distance import cdist
from pricing_problem import pricing_problem
import pulp
from config import *
import time

if __name__ == "__main__":
    locations = generate_locations()
    distance_matrix = compute_distance_matrix(locations)
    bins = generate_bins(locations)
    dataset = merge_data(locations, bins)
    
    depot_row = pd.DataFrame({"Location_ID": [0], "X_Coordinate": [0], "Y_Coordinate": [0]})
    locations_with_depot = pd.concat([depot_row, locations], ignore_index=True)
    coordinates_with_depot = locations_with_depot[["X_Coordinate", "Y_Coordinate"]].values
    distance_matrix_with_depot = cdist(coordinates_with_depot, coordinates_with_depot, metric="euclidean")
    
    waste_loads = {row["Location_ID"]: row["Bin_Capacity"] * (row["Current_Fill_Level"] / 100) for _, row in dataset.iterrows()}
    n_bins = len(waste_loads)

    initial_routes = pd.DataFrame({
        "Route_ID": [f"R{i}" for i in range(1, NUM_LOCATIONS + 1)],
        "Bins_Covered": [{i} for i in range(1, NUM_LOCATIONS + 1)],
        "Cost": dataset["Route_Cost"].values
    })

    # Create a DataFrame for the a_i columns
    a_columns = pd.DataFrame({
        f"a_{i}": initial_routes["Bins_Covered"].apply(lambda x: 1 if i in x else 0) for i in range(1, NUM_LOCATIONS + 1)
    })

    # Concatenate the a_columns DataFrame to the initial_routes DataFrame
    initial_routes = pd.concat([initial_routes, a_columns], axis=1)
    
    start_time = time.time()
    rmp, lambda_s = initialize_rmp(initial_routes)
    max_iter = 1000
    optimality_gap = 1.0
    best_lower_bound = float('inf')
    i = 0

    while i < max_iter:
        duals = solve_rmp(rmp)
        new_routes = pricing_problem(n_bins, distance_matrix_with_depot, duals, waste_loads)
        if not new_routes:
            break
        initial_routes = add_new_routes_to_rmp(rmp, initial_routes, new_routes)
        rmp.solve()
        current_obj_value = pulp.value(rmp.objective)
        best_lower_bound = min(best_lower_bound, current_obj_value)
        optimality_gap = (current_obj_value - best_lower_bound) / current_obj_value
        i += 1
    
    rmp.solve()
    print("Status:", pulp.LpStatus[rmp.status])
    print("Total Cost:", pulp.value(rmp.objective))
    
    print("\n=== Optimal Routes ===")
    total_cost = 0
    selected_count = 0
    for var in rmp.variables():
        if var.varValue > 1e-5:
            route_id = var.name.replace("Route_", "")
            route_data = initial_routes[initial_routes["Route_ID"] == route_id].iloc[0]
            bins_covered = [i for i in range(1, NUM_LOCATIONS+1) if route_data[f"a_{i}"] == 1]
            cost = route_data["Cost"]
            print(f"Route {route_id}:")
            print(f"  Bins: {sorted(bins_covered)}")
            print(f"  Cost: {cost:.2f} km")
            print(f"  Waste Load: {sum(waste_loads[i] for i in bins_covered):.1f} kg")
            print("-" * 30)
            total_cost += cost * var.varValue
            selected_count += 1
    print(f"\nTotal Routes Selected: {selected_count}")
    print(f"Total Distance: {total_cost:.2f} km")
    print(f"Truck Capacity Used: {TRUCK_CAPACITY} kg")
    print(f"Total Waste Load: {sum(waste_loads.values()):.1f} kg")
    print(f"Execution Time: {time.time() - start_time:.2f} seconds")
    print(f"Total routes discovered: {len(initial_routes)}")
    print(f"Optimality Gap: {optimality_gap}")