import pulp
import pandas as pd
from config import NUM_LOCATIONS

def initialize_rmp(initial_routes):
    rmp = pulp.LpProblem("Restricted_Master_Problem", pulp.LpMinimize)
    lambda_s = pulp.LpVariable.dicts("Route", initial_routes["Route_ID"], lowBound=0)
    rmp += pulp.lpSum([lambda_s[r] * initial_routes.loc[initial_routes["Route_ID"] == r, "Cost"].values[0] 
                       for r in initial_routes["Route_ID"]])

    for i in range(1, NUM_LOCATIONS + 1):
        rmp += pulp.lpSum([lambda_s[r] * initial_routes.loc[initial_routes["Route_ID"] == r, f"a_{i}"].values[0] 
                           for r in initial_routes["Route_ID"]]) == 1, f"Coverage_Bin_{i}"
    return rmp, lambda_s

def solve_rmp(rmp):
    rmp.solve()
    return {i: rmp.constraints[f"Coverage_Bin_{i}"].pi for i in range(1, NUM_LOCATIONS + 1)}

def add_new_routes_to_rmp(rmp, initial_routes, new_routes):
    for route in new_routes:
        route_id = f"R{len(initial_routes) + 1}"
        col = pulp.LpVariable(route_id, lowBound=0)
        rmp.objective += col * route["cost"]
        for bin in route["route"]:
            rmp.constraints[f"Coverage_Bin_{bin}"] += col
        new_row = {"Route_ID": route_id, "Cost": route["cost"], "Bins_Covered": set(route["route"])}
        new_row.update({f"a_{i}": 1 if i in route["route"] else 0 for i in range(1, NUM_LOCATIONS + 1)})
        initial_routes = pd.concat([initial_routes, pd.DataFrame([new_row])], ignore_index=True)
    return initial_routes