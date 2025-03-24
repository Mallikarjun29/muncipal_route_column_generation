import pulp
from config import TRUCK_CAPACITY

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

def pricing_problem(n_bins, distance_matrix, dual_values, waste_loads):
    model, x, y = build_pricing_problem(n_bins, distance_matrix, dual_values, waste_loads)
    reduced_cost = solve_pricing(model)
    if reduced_cost is None or reduced_cost >= -1e-5:
        return None
    new_route = extract_new_route(x, n_bins)
    route_cost = sum(distance_matrix[i][j] * x[i, j].value() for i in range(n_bins + 1) for j in range(n_bins + 1) if i != j)
    reduced_cost = route_cost - sum(dual_values[i] for i in new_route)
    return [{
        "route": new_route,
        "cost": route_cost,
        "reduced_cost": reduced_cost
    }]