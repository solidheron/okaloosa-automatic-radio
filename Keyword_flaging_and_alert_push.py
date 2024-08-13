import csv
import os
import time
import importlib
from datetime import datetime, timedelta

def load_keywords():
    try:
        keywords = importlib.import_module('keywords')
        importlib.reload(keywords)
        print("Successfully imported clarifications, keyword categories, and street data from keywords.py")
        return keywords.clarifications, keywords.keyword_categories, keywords.street_data
    except ImportError:
        print("Error: keywords.py not found or not accessible. Please ensure it's in the same directory as this script.")
        return None, None, None

def extract_timestamp_from_filename(filename):
    """Extracts and formats the timestamp from the filename."""
    try:
        parts = filename.split('_')
        date_str = parts[1]
        time_str = parts[2][:6]  # Only take the first 6 characters for HHMMSS
        timestamp_str = f"{date_str}_{time_str}"
        return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    except (IndexError, ValueError):
        return None

def process_transcription_csv(input_file, flagged_file, annotated_file, clarifications, keyword_categories, street_data):
    with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
         open(flagged_file, 'w', newline='', encoding='utf-8') as flagged_outfile, \
         open(annotated_file, 'w', newline='', encoding='utf-8') as annotated_outfile:
        
        reader = csv.reader(infile)
        flagged_writer = csv.writer(flagged_outfile)
        annotated_writer = csv.writer(annotated_outfile)
        
        # Skip the header row
        header = next(reader)
        
        # Read all rows into memory
        all_rows = list(reader)
        
        for index, row in enumerate(all_rows):
            if len(row) < 4:
                continue
            timestamp, file_name, transcription, model = row[:4]
            
            flagged_categories = set()
            flagged_keywords = set()
            matched_coordinates = []
            
            # Check for street names in transcription
            for street_name, coordinates in street_data.items():
                if street_name.lower() in transcription.lower():
                    matched_coordinates.append((street_name, coordinates))
            
            # Check for keywords in each category
            for category, keywords in keyword_categories.items():
                if category.lower() == "locations":
                    continue  # Skip the "locations" category
                for keyword in keywords:
                    if keyword.lower() in transcription.lower():
                        flagged_categories.add(category)
                        flagged_keywords.add(keyword)
            
            # Prepare data for flagged_data.csv
            coordinates_str = ';'.join([f"{street}: ({lon}, {lat})" for street, (lon, lat) in matched_coordinates])
            flagged_row = [
                timestamp,
                file_name,
                ", ".join(flagged_categories) if flagged_categories else "NULL",
                ", ".join(flagged_keywords) if flagged_keywords else "NULL",
                transcription,
                model,
                coordinates_str if coordinates_str else "NULL"
            ]
            
            # Write to flagged_data.csv if columns 3, 4, and 7 are not all "NULL"
            if not (flagged_row[2] == "NULL" and flagged_row[3] == "NULL" and flagged_row[6] == "NULL"):
                flagged_writer.writerow(flagged_row)
            
            # Write to annotated.csv if coordinates are found
            if matched_coordinates:
                # Extract the timestamp from the file name
                file_timestamp = extract_timestamp_from_filename(file_name)
                category = ", ".join([cat for cat in flagged_categories if cat.lower() != "locations"]) or "NULL"
                
                # If category is NULL, search nearby transcriptions
                if category == "NULL":
                    current_time = extract_timestamp_from_filename(file_name)
                    nearby_category = search_nearby_transcriptions(all_rows, index, current_time, keyword_categories)
                    if nearby_category:
                        category = nearby_category
                
                annotated_row = [
                    ';'.join([f"{lon}, {lat}" for _, (lon, lat) in matched_coordinates]),
                    file_timestamp.strftime("%Y%m%d_%H%M%S") if file_timestamp else "NULL",
                    category
                ]
                
                annotated_writer.writerow(annotated_row)

def search_nearby_transcriptions(all_rows, current_index, current_time, keyword_categories):
    """Searches nearby transcriptions for categories within a 3-minute window."""
    all_nearby_categories = set()
    
    for i in range(max(0, current_index - 20), min(len(all_rows), current_index + 20)):
        if i == current_index:
            continue
        row = all_rows[i]
        if len(row) < 4:
            continue
        _, file_name, transcription, _ = row[:4]
        row_time = extract_timestamp_from_filename(file_name)
        
        if row_time and abs((row_time - current_time).total_seconds()) <= 180:  # Within 3 minutes
            # Add all categories except "locations"
            for category, keywords in keyword_categories.items():
                if category.lower() == "locations":
                    continue  # Skip the "locations" category
                for keyword in keywords:
                    if keyword.lower() in transcription.lower():
                        all_nearby_categories.add(category)
    
    return ", ".join(all_nearby_categories) if all_nearby_categories else "NULL"

def process_annotated2_data(flagged_file, annotated_file, annotated2_file, street_data):
    """Processes flagged_data.csv to create annotated2.csv for entries with categories but no coordinates."""
    with open(flagged_file, 'r', newline='', encoding='utf-8') as infile, \
         open(annotated_file, 'r', newline='', encoding='utf-8') as annotated_infile, \
         open(annotated2_file, 'w', newline='', encoding='utf-8') as annotated2_outfile:
        
        reader = csv.reader(infile)
        annotated_reader = csv.reader(annotated_infile)
        annotated2_writer = csv.writer(annotated2_outfile)
        
        # Read all annotated rows to track used categories
        annotated_rows = list(annotated_reader)
        used_categories = set(row[2] for row in annotated_rows if len(row) > 2 and row[2] != "NULL")
        
        # Read all flagged rows
        all_rows = list(reader)
        
        for index, row in enumerate(all_rows):
            if len(row) < 7:
                continue
            timestamp, file_name, categories, _, transcription, _, coordinates = row[:7]
            
            # Check if the row has categories but no coordinates
            if categories != "NULL" and coordinates == "NULL":
                category_list = categories.split(", ")
                # Exclude rows where "locations" is the only category
                if "locations" in category_list and len(category_list) == 1:
                    continue
                
                # Check if these categories have already been used
                if not any(cat in used_categories for cat in category_list):
                    # Search for nearby coordinates
                    current_time = extract_timestamp_from_filename(file_name)
                    nearby_coordinates = search_nearby_coordinates(all_rows, index, current_time, street_data)
                    
                    if nearby_coordinates:
                        # Extract the timestamp from the file name
                        file_timestamp = extract_timestamp_from_filename(file_name)
                        formatted_timestamp = file_timestamp.strftime("%Y%m%d_%H%M%S") if file_timestamp else "NULL"
                        
                        # Prepare the row for annotated2.csv
                        annotated2_row = [
                            formatted_timestamp,
                            ", ".join(category_list),
                            ", ".join(nearby_coordinates.keys()),
                            "; ".join([f"{lon}, {lat}" for lon, lat in nearby_coordinates.values()])
                        ]
                        
                        annotated2_writer.writerow(annotated2_row)



def search_nearby_coordinates(all_rows, current_index, current_time, street_data):
    """Searches nearby transcriptions for coordinates within a 3-minute window."""
    nearby_coordinates = {}
    
    for i in range(max(0, current_index - 20), min(len(all_rows), current_index + 20)):
        if i == current_index:
            continue
        row = all_rows[i]
        if len(row) < 7:
            continue
        _, file_name, _, _, transcription, _, _ = row[:7]
        row_time = extract_timestamp_from_filename(file_name)
        
        if row_time and abs((row_time - current_time).total_seconds()) <= 180:  # Within 3 minutes
            # Check for street names in transcription
            for street_name, coordinates in street_data.items():
                if street_name.lower() in transcription.lower():
                    nearby_coordinates[street_name] = coordinates
    
    return nearby_coordinates

def countdown_timer(seconds, interval):
    for remaining in range(seconds, 0, -interval):
        print(f"\rNext check in {remaining} seconds...", end="")
        time.sleep(interval)
    print("\rChecking now... ", end="\r")

def main():
    input_directory = r"D:\Police_audio_recordings"  # Change this to your input directory
    input_file = os.path.join(input_directory, "transcriptions.csv")
    flagged_file = os.path.join(input_directory, "flagged_data.csv")
    annotated_file = os.path.join(input_directory, "annotated.csv")
    annotated2_file = os.path.join(input_directory, "annotated2.csv")
    
    while True:
        clarifications, keyword_categories, street_data = load_keywords()
        if clarifications is None or keyword_categories is None or street_data is None:
            print("Failed to load keyword data. Exiting.")
            break
        
        if os.path.exists(input_file):
            print(f"Processing transcription file: {input_file}")
            process_transcription_csv(input_file, flagged_file, annotated_file, clarifications, keyword_categories, street_data)
            process_annotated2_data(flagged_file, annotated_file, annotated2_file, street_data)
            print(f"Finished processing {input_file}")
        else:
            print(f"Transcription file not found: {input_file}")
        
        countdown_timer(1200, 5)
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    main()
