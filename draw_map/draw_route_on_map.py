import argparse
import folium
import openrouteservice
import yaml
import backoff

@backoff.on_exception(backoff.expo,
                      openrouteservice.exceptions.ApiError,
                      giveup=lambda e: e.status_code != 429,
                      max_tries=8)
def get_route(client, coords):
    return client.directions(coordinates=coords, profile='driving-car', format='geojson')

parser = argparse.ArgumentParser(description='Draw a route on the map with highlighted locations.')
parser.add_argument('-l', '--locations_file', required=True, help='YAML file with locations data')
parser.add_argument('-r', '--route_file', required=True, help='YAML file with route data')
parser.add_argument('-o', '--output_file', default='map.html', help='Output HTML file for the map')

args = parser.parse_args()

with open('api.key', 'r') as key_file:
    api_key = key_file.read().strip()

client = openrouteservice.Client(key=api_key)

with open(args.locations_file, 'r') as file:
    locations_data = yaml.safe_load(file)

with open(args.route_file, 'r') as file:
    route_data = yaml.safe_load(file)

first_location_coords = locations_data['locations'][0]['coords']
m = folium.Map(location=first_location_coords[::-1], zoom_start=12)

for location in locations_data['locations']:
    folium.Marker(
        location['coords'],
        popup=location['name'],
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

# Draw the route on the map
for i in range(len(route_data['shortest_path']) - 1):
    start_location = route_data['shortest_path'][i]
    end_location = route_data['shortest_path'][i + 1]
    start_coords = next(item for item in locations_data['locations'] if item['name'] == start_location)['coords']
    end_coords = next(item for item in locations_data['locations'] if item['name'] == end_location)['coords']

    # Get route from OpenRouteService
    route = get_route(client, (start_coords[::-1], end_coords[::-1]))  # reverse coords for API (lon, lat)

    # Add the route to the map
    folium.features.GeoJson(route, name='Route').add_to(m)

# Save the map to an HTML file
m.save(args.output_file)

print(f"Map with the route has been saved to {args.output_file}")


#python draw_route_on_map.py -l ../dictionary_from_open_route_service_api/example_locations.yaml -r ../example_output.yaml -o example_map.html