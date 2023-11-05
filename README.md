# TSP Solver Earth based on Open Route Service API

This repository is dedicated to solving TSP problem for driving car. It utilizes the OpenRouteService API to solve the Traveling Salesman Problem (TSP) with actual road distances. It includes a Python script for fetching distances, a Python and C++ implementation for the TSP algorithm, and a Python script to visualize the route on a map.

## Project Structure

The project is organized into several directories:

- `cpp`: Contains the C++ source code and the compiled module for the TSP algorithm.
- `dictionary_from_open_route_service_api`: Contains the script to fetch distances and durations between locations using the OpenRouteService API.
- `draw_map`: Includes the script to visualize the calculated TSP route on an interactive map.

`YAML` files include example configurations, distances, and outputs for demonstration purposes.

## Setup and Usage

Before using the scripts, ensure you have an API key from OpenRouteService saved in the `api.key` file. Use `-h` param with python files to get help.

It is not necessary to compile C++ module, although it is recommended to make execution of `find_route.py` faster.

In order to compile C++ module, you can use `g++`:

```bash
g++ -O3 -Wall -shared -std=c++2a -fPIC $(python3 -m pybind11 --includes) tps_solver.cpp -o tps_solver$(python3-config --extension-suffix)
```

## Dependencies

- Python 3.x
- Folium (for map visualization)
- OpenRouteService Python client
- NetworkX (for graph operations in Python)
- pybind11 (for binding C++ and Python)
- A C++ compiler (with C++17 support)
- Backoff (for retrying API calls)
- Time, sys, argparse, yaml (Python standard libraries)
