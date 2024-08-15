"""
this script is designed to get all the coordinates for the streets and points of interest in whatever place 
you enter, can be a city,state,or county. recomended that to keep it either on the city or county level.
set up to find the centriod of a road but the script can be modified to get indivual addresses.
coordiates that dont have names will not get outputted. the coordinate will always be put inside a road.

"""
import requests
from shapely.geometry import LineString
from shapely.ops import nearest_points

def get_osm_data(area_name, feature):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    area["name"="{area_name}"]->.searchArea;
    (
      way["{feature}"](area.searchArea);
      node["tourism"]["name"](area.searchArea);
      node["natural"]["name"](area.searchArea);
      node["amenity"="fuel"]["name"](area.searchArea);
    );
    out body geom;
    """
    print(f"Sending request to Overpass API for {area_name}...")
    response = requests.get(overpass_url, params={'data': overpass_query})
    print(f"Response status code: {response.status_code}")
    response.raise_for_status()
    data = response.json()
    print(f"Received {len(data.get('elements', []))} elements from API")
    return data

def parse_osm_data(osm_data):
    streets = {}
    pois = []
    natural_features = []
    fuel_stations = []

    for element in osm_data.get('elements', []):
        name = element['tags'].get('name')
        if name and name != 'Unnamed':
            # Add a space at the beginning of the name
            name = " " + name

            if element['type'] == 'way' and 'highway' in element['tags']:
                if name not in streets:
                    geometry = LineString([(point['lon'], point['lat']) for point in element['geometry']])
                    centroid = geometry.centroid
                    
                    # Ensure the centroid is inside the geometry
                    if not geometry.contains(centroid):
                        # Find the nearest point on the geometry to the centroid
                        nearest_point = nearest_points(geometry, centroid)[0]
                        centroid = nearest_point  # Move centroid to the nearest point inside

                    streets[name] = (centroid.x, centroid.y)

            elif element['type'] == 'node':
                item = {
                    'name': name,
                    'lon': element['lon'],
                    'lat': element['lat']
                }

                if 'tourism' in element['tags']:
                    pois.append(item)
                elif 'natural' in element['tags']:
                    natural_features.append(item)
                elif element['tags'].get('amenity') == 'fuel':
                    fuel_stations.append(item)

    unique_streets = [{
        'name': name,
        'lon': lon,
        'lat': lat
    } for name, (lon, lat) in streets.items()]

    print(f"Parsed {len(unique_streets)} unique streets, {len(pois)} POIs, {len(natural_features)} natural features, and {len(fuel_stations)} fuel stations from OSM data")
    return unique_streets, pois, natural_features, fuel_stations

def save_to_txt(streets, pois, natural_features, fuel_stations, filename):
    with open(filename, 'w') as file:
        for street in streets:
            file.write(f'"{street["name"]}",({street["lon"]}, {street["lat"]})\n')
        for poi in pois:
            file.write(f'"{poi["name"]}",({poi["lon"]}, {poi["lat"]})\n')
        for natural_feature in natural_features:
            file.write(f'"{natural_feature["name"]}",({natural_feature["lon"]}, {natural_feature["lat"]})\n')
        for fuel_station in fuel_stations:
            file.write(f'"{fuel_station["name"]}",({fuel_station["lon"]}, {fuel_station["lat"]})\n')

    print(f"TXT file '{filename}' has been created.")

def main():
    area_name = "Okaloosa County"  # Change this to the city, state, or county that you want to fetch data from
    feature = "highway"
    filename = "Street_POI_coordinate_data.txt"
    try:
        print(f"Fetching OSM data for {area_name}...")
        osm_data = get_osm_data(area_name, feature)
        print("Parsing OSM data...")
        streets, pois, natural_features, fuel_stations = parse_osm_data(osm_data)
        print(f"Saving data to {filename}...")
        save_to_txt(streets, pois, natural_features, fuel_stations, filename)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Overpass API: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
