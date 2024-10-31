import argparse
import openrouteservice
import yaml
import time
import backoff

profile = 'driving-car'

@backoff.on_exception(backoff.expo,
                      openrouteservice.exceptions._OverQueryLimit,
                      max_tries=4)
def get_routes(client, coords, profile):
    return client.directions(coordinates=coords, profile=profile)

parser = argparse.ArgumentParser(description='Calculate distances between locations from a YAML file.')
parser.add_argument('-i', '--input_file', help='Input YAML file with locations')
parser.add_argument('-d', '--distances_file', help='Optional YAML file with pre-calculated distances')
parser.add_argument('-o', '--output_file', required=True, help='Output YAML file to store distances and durations')

args = parser.parse_args()

# Read the API key from the api.key file
with open('api.key', 'r') as key_file:
    api_key = key_file.read().strip()

client = openrouteservice.Client(key=api_key)

with open(args.input_file, 'r') as file:
    locations = yaml.safe_load(file)

# Optionally load pre-calculated distances
precalculated_distances = {}
if args.distances_file:
    with open(args.distances_file, 'r') as file:
        precalculated_distances = yaml.safe_load(file)

results = {}

for i, origin in enumerate(locations['locations']):
    results[origin['name']] = {}
    for destination in locations['locations']:
        if origin == destination:
            continue  # Skip calculating distance from a point to itself

        # Check if the distance is already calculated and stored
        if (origin['name'] in precalculated_distances and
                destination['name'] in precalculated_distances[origin['name']]):
            results[origin['name']][destination['name']] = precalculated_distances[origin['name']][destination['name']]
        else:
            try:
                # Request directions and extract distance and duration
                coords = [(origin['coords'][1], origin['coords'][0]), (destination['coords'][1], destination['coords'][0])]
                routes = get_routes(client, coords, profile)
                distance = routes['routes'][0]['summary']['distance']  # Distance in meters
                duration = routes['routes'][0]['summary']['duration']  # Duration in seconds
                results[origin['name']][destination['name']] = {
                    'distance_km': distance / 1000,
                    'duration_min': duration / 60
                }
            except openrouteservice.exceptions.ApiError as error:
                print(f"Error calculating distance between {origin['name']} and {destination['name']}: {error}")
                results[origin['name']][destination['name']] = 'Error'


with open(args.output_file, 'w') as file:
    yaml.dump(results, file, default_flow_style=False)

print(f"Distances and durations have been calculated and saved to {args.output_file}.")
