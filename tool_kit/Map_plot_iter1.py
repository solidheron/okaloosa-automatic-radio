"""
    This is a script that takes any coordinates found in flagged_date and plots them onto a 
    map. mostly there for interesting viusal
"""
import csv
import folium

def read_coordinates_from_csv(csv_filename):
    coordinates = []
    with open(csv_filename, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header row if there is one
        for row in reader:
            if len(row) >= 7:
                coord_str = row[6]
                if coord_str != "NULL":
                    coord_pairs = coord_str.split(';')
                    for pair in coord_pairs:
                        street, coord = pair.split(': ')
                        lon, lat = map(float, coord.split(','))
                        coordinates.append((lat, lon, street))
    return coordinates

def plot_coordinates_on_map(coordinates, output_html):
    # Create a map centered around the first coordinate
    if coordinates:
        first_coord = coordinates[0]
        m = folium.Map(location=[first_coord[0], first_coord[1]], zoom_start=12)

        # Add markers for each coordinate
        for lat, lon, street in coordinates:
            folium.Marker(
                location=[lat, lon],
                popup=f"{street}: ({lat}, {lon})",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

        # Save the map to an HTML file
        m.save(output_html)
        print(f"Map has been saved to {output_html}")
    else:
        print("No coordinates to plot.")

if __name__ == "__main__":
    csv_filename = r'D:\Police_audio_recordings\flagged_data.csv'
    output_html = r'D:\Police_audio_recordings\map.html'

    coordinates = read_coordinates_from_csv(csv_filename)
    plot_coordinates_on_map(coordinates, output_html)
