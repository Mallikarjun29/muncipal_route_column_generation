import pulp
from config import TRUCK_CAPACITY
from concurrent.futures import ThreadPoolExecutor

def build_pricing_problem(n_bins, distance_matrix, dual_values, waste_loads):
    model = pulp.LpProblem("Pricing_Problem", pulp.LpMinimize)
    nodes = range(n_bins + 1)
    x = pulp.LpVariable.dicts("x", [(i, j) for i in nodes for j in nodes if i != j], cat='Binary')
    y = pulp.LpVariable.dicts("y", [i for i in nodes[1:]], cat='Binary')

    model += (
        pulp.lpSum(distance_matrix[i][j] * x[i, j] for i in nodes for j in nodes if i != j) -
        pulp.lpSum(dual_values[i] * y[i] for i in nodes[1:])
    )

    model += pulp.lpSum(x[0, j] for j in nodes[1:]) == 1
    model += pulp.lpSum(x[i, 0] for i in nodes[1:]) == 1

    for k in nodes[1:]:
        model += (
            pulp.lpSum(x[i, k] for i in nodes if i != k) == 
            pulp.lpSum(x[k, j] for j in nodes if j != k)
        )

    for i in nodes[1:]:
        model += y[i] == pulp.lpSum(x[i, j] for j in nodes if j != i)

    model += (
        pulp.lpSum(waste_loads[i] * y[i] for i in nodes[1:]) <= TRUCK_CAPACITY
    )

    u = pulp.LpVariable.dicts("u", nodes[1:], lowBound=1, upBound=n_bins, cat='Integer')
    for i in nodes[1:]:
        for j in nodes[1:]:
            if i != j:
                model += u[i] - u[j] + n_bins * x[i, j] <= n_bins - 1

    return model, x, y

def solve_pricing(model):
    model.solve(pulp.PULP_CBC_CMD(msg=0))
    if model.status == pulp.LpStatusOptimal:
        return pulp.value(model.objective)
    else:
        return None

def extract_new_route(x_vars, n_bins):
    route = []
    current = 0
    while True:
        next_node = None
        for j in range(n_bins + 1):
            if j == current:
                continue
            if x_vars[current, j].value() > 0.5:
                next_node = j
                break
        if next_node is None or next_node == 0:
            break
        route.append(next_node)
        current = next_node
    return route

def calculate_savings(i, j, distance_matrix, dual_values):
    return (i, j), distance_matrix[0][i] + distance_matrix[0][j] - distance_matrix[i][j] - (dual_values[i] + dual_values[j])

def clarke_wright_savings_heuristic(n_bins, distance_matrix, dual_values, waste_loads):
    savings = {}
    with ThreadPoolExecutor(max_workers= 8) as executor:
        futures = [executor.submit(calculate_savings, i, j, distance_matrix, dual_values) for i in range(1, n_bins + 1) for j in range(i + 1, n_bins + 1)]
        for future in futures:
            (i, j), saving = future.result()
            savings[(i, j)] = saving

    sorted_savings = sorted(savings.items(), key=lambda item: item[1], reverse=True)
    
    routes = {i: [0, i, 0] for i in range(1, n_bins + 1)}
    route_loads = {i: waste_loads[i] for i in range(1, n_bins + 1)}

    for (i, j), saving in sorted_savings:
        if i in routes and j in routes and routes[i][-2] == i and routes[j][1] == j:
            if route_loads[i] + route_loads[j] <= TRUCK_CAPACITY:
                routes[i] = routes[i][:-1] + routes[j][1:]
                route_loads[i] += route_loads[j]
                del routes[j]

    new_routes = []
    for route in routes.values():
        if len(route) > 3:
            new_routes.append(route[1:-1])

    return new_routes

def pricing_problem(n_bins, distance_matrix, dual_values, waste_loads):
    new_routes = clarke_wright_savings_heuristic(n_bins, distance_matrix, dual_values, waste_loads)
    if not new_routes:
        return None

    routes_info = []
    for route in new_routes:
        route_cost = sum(distance_matrix[route[i]][route[i + 1]] for i in range(len(route) - 1))
        reduced_cost = route_cost - sum(dual_values[i] for i in route)
        routes_info.append({
            "route": route,
            "cost": route_cost,
            "reduced_cost": reduced_cost
        })

    return routes_info