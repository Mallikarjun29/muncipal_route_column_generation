# Municipal Route Column Generation

This project implements a column generation approach to solve the municipal routes problem using the Clarke-Wright Savings Heuristic with dual-value weighting.

## Requirements

- Python 3.8 or higher

## Dependencies

The following Python packages are required to run the code:

- numpy==2.2.4
- pandas==2.2.3
- scipy==1.15.2
- PuLP==3.0.2
- networkx==3.4.2

You can install these dependencies using `pip`:

```sh
pip install numpy==2.2.4 pandas==2.2.3 scipy==1.15.2 PuLP==3.0.2 networkx==3.4.2
```

## Running the Code

1. Clone the repository:

```sh
git clone https://github.com/yourusername/muncipal_route_column_generation.git
cd muncipal_route_column_generation
```



2. After installing required dependencies generate the instances:

```sh
python generate_instances.py
```

3. Run the main script to solve the municipal routes problem:

```sh
python main.py
```

## Project Structure

- `config.py`: Configuration file containing parameters for the project.
- `generate_instances.py`: Script to generate locations, compute distance matrix, and generate bin attributes.
- `pricing_problem.py`: Script containing functions to build and solve the pricing problem using the Clarke-Wright Savings Heuristic.
- `rmp_solver.py`: Script containing functions to initialize and solve the restricted master problem (RMP) and add new routes.
- `main.py`: Main script to run the entire process, including generating instances, solving the pricing problem, and solving the RMP.

## Example Output

After running the `main.py` script, you will see the status, total cost, and details of the optimal routes selected. The output will include the bins covered, cost, waste load, and other relevant information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.