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

def process_transcription_csv(input_file, flagged_file, annotated_file, clarifications, keyword_categories, street_data):
    with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
         open(flagged_file, 'w', newline='', encoding='utf-8') as flagged_outfile, \
         open(annotated_file, 'w', newline='', encoding='utf-8') as annotated_outfile:
        reader = csv.reader(infile)
        flagged_writer = csv.writer(flagged_outfile)
        annotated_writer = csv.writer(annotated_outfile)

        matched_streets = set()  # Keep track of matched streets

        # Skip the header row
        header = next(reader)

        # Read all rows into memory
        all_rows = list(reader)

        for index, row in enumerate(all_rows):
            if len(row) != 4:
                continue

            timestamp, file_name, transcription, model = row
            flagged_categories = set()
            flagged_keywords = set()
            matched_coordinates = []

            # Check for street names in transcription
            for street_name, coordinates in street_data.items():
                if street_name.lower() in transcription.lower():
                    matched_coordinates.append((street_name, coordinates))

            # Check for keywords in each category
            for category, keywords in keyword_categories.items():
                for keyword in keywords:
                    if keyword.lower() in transcription.lower():
                        flagged_categories.add(category)
                        flagged_keywords.add(keyword)

            # Prepare data for flagged_data.csv
            coordinates_str = ';'.join([f"{street}: {lon},{lat}" for street, (lon, lat) in matched_coordinates])
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
                # Remove .wav extension from the timestamp
                file_timestamp = '_'.join(file_name.split('_')[1:3]).replace('.wav', '')
                category = ", ".join([cat for cat in flagged_categories if cat.lower() != "locations"]) or "NULL"
                
                # If category is NULL, search nearby transcriptions
                if category == "NULL":
                    current_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    nearby_category = search_nearby_transcriptions(all_rows, index, current_time, keyword_categories)
                    if nearby_category:
                        category = nearby_category

                annotated_row = [
                    ';'.join([f"{lon},{lat}" for _, (lon, lat) in matched_coordinates]),
                    file_timestamp,
                    category
                ]
                annotated_writer.writerow(annotated_row)

def search_nearby_transcriptions(all_rows, current_index, current_time, keyword_categories):
    for i in range(max(0, current_index - 20), min(len(all_rows), current_index + 20)):
        if i == current_index:
            continue
        row = all_rows[i]
        if len(row) != 4:
            continue
        timestamp, _, transcription, _ = row
        row_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        if abs((row_time - current_time).total_seconds()) <= 180:  # Within 3 minutes
            flagged_categories = set()
            for category, keywords in keyword_categories.items():
                for keyword in keywords:
                    if keyword.lower() in transcription.lower():
                        flagged_categories.add(category)
            if flagged_categories and "locations" not in flagged_categories:
                return ", ".join(flagged_categories)
    return None

def countdown_timer(seconds, interval):
    for remaining in range(seconds, 0, -interval):
        print(f"\rNext check in {remaining} seconds...", end="")
        time.sleep(interval)
    print("\rChecking now...                ", end="\r")

def main():
    input_directory = r"D:\Police_audio_recordings"  # Change this to your input directory
    input_file = os.path.join(input_directory, "transcriptions.csv")
    flagged_file = os.path.join(input_directory, "flagged_data.csv")
    annotated_file = os.path.join(input_directory, "annotated.csv")

    while True:
        # Load keywords at the beginning of each loop
        clarifications, keyword_categories, street_data = load_keywords()
        if clarifications is None or keyword_categories is None or street_data is None:
            print("Failed to load keyword data. Exiting.")
            break

        if os.path.exists(input_file):
            print(f"Processing transcription file: {input_file}")
            process_transcription_csv(input_file, flagged_file, annotated_file, clarifications, keyword_categories, street_data)
            print(f"Finished processing {input_file}")
        else:
            print(f"Transcription file not found: {input_file}")
        
        countdown_timer(30, 5)  # 30-second countdown timer with 5-second intervals
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen after countdown

if __name__ == "__main__":
    main()
