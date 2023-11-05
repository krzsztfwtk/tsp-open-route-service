import time
import platform
import argparse
import yaml
import networkx as nx
import sys
from itertools import permutations

try:
    from cpp import tsp_solver
    cpp_module_available = True
except ImportError as e:
    print("Could not import the C++ module. Error:", e)
    cpp_module_available = False

# cpp_module_available = False

def read_distances(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data['distances']

def read_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return (config['start_location'], config['end_location'], 
            config['required_stops'], config['weights'])

def verify_stops_in_distances(distances, stops):
    for stop in stops:
        if stop not in distances:
            raise ValueError(f"Stop '{stop}' is not present in the distances dictionary.")

def calculate_cost(distance, duration, weights):
    return weights['distance_km'] * distance + weights['duration_min'] * duration

def solve_tsp(distances, start_location, end_location, required_stops, weights):
    verify_stops_in_distances(distances, required_stops + [start_location, end_location])
    
    G = nx.Graph()
    for location, edges in distances.items():
        for destination, metrics in edges.items():
            G.add_edge(location, destination, 
                       weight=calculate_cost(metrics['distance_km'], metrics['duration_min'], weights),
                       distance_km=metrics['distance_km'],
                       duration_min=metrics['duration_min'])

    all_possible_paths = permutations(required_stops)

    full_paths = [(start_location,) + path + (end_location,) for path in all_possible_paths]

    shortest_path = None
    min_cost = float('inf')
    total_distance = 0
    total_duration = 0
    for path in full_paths:
        cost = 0
        distance = 0
        duration = 0
        for i in range(len(path) - 1):
            edge = G.edges[path[i], path[i+1]]
            cost += edge['weight']
            distance += edge['distance_km']
            duration += edge['duration_min']
        if cost < min_cost:
            min_cost = cost
            shortest_path = path
            total_distance = distance
            total_duration = duration

    return shortest_path, min_cost, total_distance, total_duration


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Solve the TSP including required stops and weighted cost function.')
    parser.add_argument('-d', '--distances_file', required=True, help='YAML file with distances between locations')
    parser.add_argument('-c', '--config_file', required=True, help='YAML config file with start and end locations and weights')
    parser.add_argument('-o', '--output_file', required=True, help='YAML file to output the shortest TSP route')

    args = parser.parse_args()

    distances = read_distances(args.distances_file)
    start_location, end_location, required_stops, weights = read_config(args.config_file)

    start_time = time.time()

    # Solve the TSP using the C++ module if available, otherwise use the Python function
    if cpp_module_available:
        # Convert the Python dictionary to the C++ Graph structure
        cpp_distances = {
            start: {
                end: tsp_solver.Edge(metrics['distance_km'], metrics['duration_min'])
                for end, metrics in destinations.items()
            }
            for start, destinations in distances.items()
        }


        shortest_path, min_cost, total_distance, total_duration = tsp_solver.solve_tsp(
            cpp_distances, 
            start_location, 
            end_location, 
            required_stops, 
            weights['distance_km'], 
            weights['duration_min']
        )
    else:
        shortest_path, min_cost, total_distance, total_duration = solve_tsp(
            distances, start_location, end_location, required_stops, weights
        )

    end_time = time.time()

    elapsed_time = end_time - start_time

    output_data = {
        'shortest_path': shortest_path,
        'total_cost': min_cost,
        'total_distance_km': total_distance,
        'total_duration_min': total_duration,
        'solving_time_seconds': elapsed_time
    }
    with open(args.output_file, 'w') as file:
        yaml.dump(output_data, file, default_flow_style=False)

    print(f"Shortest path: {shortest_path}")
    print(f"Total cost: {min_cost}")
    print(f"Total distance: {total_distance} km")
    print(f"Total duration: {total_duration} min")
    print(f"Solving time: {elapsed_time} seconds")
