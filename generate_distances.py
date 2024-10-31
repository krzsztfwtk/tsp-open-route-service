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

with open('api.key', 'r') as key_file:
    api_key = key_file.read().strip()

client = openrouteservice.Client(key=api_key)

with open(args.input_file, 'r') as file:
    locations = yaml.safe_load(file)

precalculated_distances = {}
if args.distances_file:
    with open(args.distances_file, 'r') as file:
        precalculated_distances = yaml.safe_load(file)

results = {}
request_count = 0  # Counter for the number of requests
rate_limit_sleep = 1.2  # Delay between requests in seconds to avoid rate limit

for i, origin in enumerate(locations['locations']):
    results[origin['name']] = {}
    for destination in locations['locations']:
        if origin == destination:
            continue

        if (origin['name'] in precalculated_distances and
                destination['name'] in precalculated_distances[origin['name']]):
            results[origin['name']][destination['name']] = precalculated_distances[origin['name']][destination['name']]
            print(f"Using precalculated distance between {origin['name']} and {destination['name']}")
        else:
            try:
                coords = [(origin['coords'][1], origin['coords'][0]), (destination['coords'][1], destination['coords'][0])]
                routes = get_routes(client, coords, profile)
                distance = routes['routes'][0]['summary']['distance']  # Distance in meters
                duration = routes['routes'][0]['summary']['duration']  # Duration in seconds
                results[origin['name']][destination['name']] = {
                    'distance_km': distance / 1000,
                    'duration_min': duration / 60
                }
                print(f"Successfully retrieved distance between {origin['name']} and {destination['name']}: "
                      f"{distance / 1000} km, {duration / 60} min")
                
                # Increment request count and sleep to respect rate limits
                request_count += 1
                time.sleep(rate_limit_sleep)
                
            except openrouteservice.exceptions.ApiError as error:
                print(f"Error calculating distance between {origin['name']} and {destination['name']}: {error}")
                results[origin['name']][destination['name']] = 'Error'
            except openrouteservice.exceptions._OverQueryLimit:
                print(f"Rate limit exceeded. Retrying with backoff for {origin['name']} to {destination['name']}.")

with open(args.output_file, 'w') as file:
    yaml.dump(results, file, default_flow_style=False)

print(f"Distances and durations have been calculated and saved to {args.output_file}.")
