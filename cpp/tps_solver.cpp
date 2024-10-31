#include <vector>
#include <string>
#include <unordered_map>
#include <limits>
#include <algorithm>
#include <cmath>
#include <iostream>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

namespace py = pybind11;

struct Edge {
    double distance_km;
    double duration_min;

    Edge(double dist_km, double dur_min) : distance_km(dist_km), duration_min(dur_min) {}
};


using Graph = std::unordered_map<std::string, std::unordered_map<std::string, Edge>>;

double calculate_cost(double distance_km, double duration_min, double weight_distance, double weight_duration) {
    return weight_distance * distance_km + weight_duration * duration_min;
}

std::tuple<std::vector<std::string>, double, double, double> solve_tsp(
    const Graph& graph,
    const std::string& start_location,
    const std::string& end_location,
    const std::vector<std::string>& required_stops,
    double weight_distance,
    double weight_duration) {
    
    std::vector<std::string> shortest_path;
    double min_cost = std::numeric_limits<double>::infinity();
    double total_distance = 0;
    double total_duration = 0;

    std::vector<std::string> locations = required_stops;
    locations.insert(locations.begin(), start_location);
    locations.push_back(end_location);

    std::sort(locations.begin() + 1, locations.end() - 1);  // Sort the required stops

    do {
        double cost = 0;
        double distance = 0;
        double duration = 0;
        for (size_t i = 0; i < locations.size() - 1; ++i) {
            try {
                const Edge& edge = graph.at(locations[i]).at(locations[i+1]);
                cost += calculate_cost(edge.distance_km, edge.duration_min, weight_distance, weight_duration);
                distance += edge.distance_km;
                duration += edge.duration_min;
            } catch (const std::out_of_range& e) {
                std::cerr << "Edge not found between " << locations[i] << " and " << locations[i+1] << std::endl;
                throw;
            }
        }
        if (cost < min_cost) {
            min_cost = cost;
            shortest_path = locations;
            total_distance = distance;
            total_duration = duration;
        }
    } while (std::next_permutation(locations.begin() + 1, locations.end() - 1));  // Next permutation of required stops

    return std::make_tuple(shortest_path, min_cost, total_distance, total_duration);
}



PYBIND11_MODULE(tsp_solver, m) {
    py::class_<Edge>(m, "Edge")
        .def(py::init<double, double>())
        .def_readwrite("distance_km", &Edge::distance_km)
        .def_readwrite("duration_min", &Edge::duration_min);

    m.def("solve_tsp", &solve_tsp,
          py::arg("distances"), py::arg("start_location"), py::arg("end_location"),
          py::arg("required_stops"), py::arg("weight_distance"), py::arg("weight_duration"),
          "Solves the Traveling Salesman Problem");
}


//g++ -O3 -Wall -shared -std=c++2a -fPIC $(python3 -m pybind11 --includes) tps_solver.cpp -o tps_solver$(python3-config --extension-suffix)
