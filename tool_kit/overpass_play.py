"""
this script is designed to get all the coordinates for the streets and points of interest in whatever place 
you enter, can be a city,state,or county. recomended that to keep it either on the city or county level.
set up to find the centriod of a road but the script can be modified to get indivual addresses.
coordiates that dont have names will not get outputted.

"""
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
from collections import defaultdict

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
            if element['type'] == 'way' and 'highway' in element['tags']:
                if name not in streets:
                    geometry = LineString([(point['lon'], point['lat']) for point in element['geometry']])
                    centroid = geometry.centroid
                    streets[name] = (centroid.x, centroid.y)
            elif element['type'] == 'node':
                item = {
                    'name': name,
                    'type': 'Unknown',
                    'lon': element['lon'],
                    'lat': element['lat']
                }
                if 'tourism' in element['tags']:
                    item['type'] = 'POI'
                    pois.append(item)
                elif 'natural' in element['tags']:
                    item['type'] = 'Natural Feature'
                    natural_features.append(item)
                elif element['tags'].get('amenity') == 'fuel':
                    item['type'] = 'Fuel Station'
                    fuel_stations.append(item)

    unique_streets = [
        {
            'name': name,
            'lon': lon,
            'lat': lat
        }
        for name, (lon, lat) in streets.items()
    ]

    print(f"Parsed {len(unique_streets)} unique streets, {len(pois)} POIs, {len(natural_features)} natural features, and {len(fuel_stations)} fuel stations from OSM data")
    return unique_streets, pois, natural_features, fuel_stations

def save_to_csv(streets, pois, natural_features, fuel_stations, filename):
    data = []

    for street in streets:
        data.append({
            'name': street['name'],
            'type': 'Street',
            'lon': street['lon'],
            'lat': street['lat'],
            'area': 'Destin'
        })

    for poi in pois:
        data.append({
            'name': poi['name'],
            'type': poi['type'],
            'lon': poi['lon'],
            'lat': poi['lat'],
            'area': 'Destin'
        })

    for natural_feature in natural_features:
        data.append({
            'name': natural_feature['name'],
            'type': natural_feature['type'],
            'lon': natural_feature['lon'],
            'lat': natural_feature['lat'],
            'area': 'Destin'
        })

    for fuel_station in fuel_stations:
        data.append({
            'name': fuel_station['name'],
            'type': fuel_station['type'],
            'lon': fuel_station['lon'],
            'lat': fuel_station['lat'],
            'area': 'Destin'
        })

    if not data:
        print(f"No data to save. CSV file '{filename}' will be empty.")
        return

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"CSV file '{filename}' has been created with {len(data)} entries.")

def main():
    area_name = "Okaloosa County" #change this to the city,state, or county that you want to fetch data from 
    feature = "highway"
    filename = "Street_POI_coordinate_data.csv"
    try:
        print(f"Fetching OSM data for {area_name}...")
        osm_data = get_osm_data(area_name, feature)
        print("Parsing OSM data...")
        streets, pois, natural_features, fuel_stations = parse_osm_data(osm_data)
        print(f"Saving data to {filename}...")
        save_to_csv(streets, pois, natural_features, fuel_stations, filename)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Overpass API: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
