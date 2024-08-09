import whisper
import os
import csv
import time
import wave
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from queue import Queue
from keywords import clarifications

class NewFileHandler(FileSystemEventHandler):
    """Handles new .wav files created in the watched directory."""

    def __init__(self, medium_model, directory_to_watch):
        """Initializes the file handler with the Whisper model and the directory to watch."""
        self.medium_model = medium_model
        self.directory_to_watch = directory_to_watch
        self.csv_file = os.path.join(directory_to_watch, "transcriptions.csv")
        self.file_queue = Queue()
        self.processed_files = self.load_processed_files()

    def load_processed_files(self):
        """Loads the set of already processed files from the CSV file."""
        processed_files = set()
        if os.path.exists(self.csv_file):
            with open(self.csv_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) >= 2:
                        processed_files.add(row[1])  # Assuming the second column is the file name
        return processed_files

    def create_csv_file(self):
        """Creates the CSV file if it does not exist and writes the header."""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "File", "Transcription", "Model", "Last End Time", "File Length"])

    def on_created(self, event):
        """Handles the event when a new file is created in the directory."""
        if event.is_directory:
            return
        if event.src_path.endswith('.wav'):
            time.sleep(0.3)  # Wait to ensure the file is fully written
            self.file_queue.put(event.src_path)
            self.process_files()

    def process_files(self):
        """Processes all files in the queue."""
        while not self.file_queue.empty():
            file_path = self.file_queue.get()
            self.process_new_file(file_path)

    def process_new_file(self, file_path):
        """Processes a new .wav file: transcribes it, and writes the result to the CSV."""
        file_name = os.path.basename(file_path)
        if file_name not in self.processed_files:
            print(f"Processing new file: {file_path}")
            try:
                # Transcribe with timestamps
                result = self.medium_model.transcribe(file_path, without_timestamps=False, fp16=False)
                segments = [segment['text'] for segment in result['segments']]
                concatenated_text = ' / '.join(segments)
                text_with_clarifications = self.add_clarifications(concatenated_text)

                # Get the last end time
                last_end_time = result['segments'][-1]['end'] if result['segments'] else 0

                # Get the length of the .wav file
                wav_length = self.get_wav_length(file_path)

                # Write to CSV
                self.write_to_csv(file_path, text_with_clarifications, "medium.en", last_end_time, wav_length)
                self.processed_files.add(file_name)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    def get_wav_length(self, file_path):
        """Calculates the length of the .wav file in seconds."""
        with wave.open(file_path, 'r') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            duration = frames / float(rate)
        return duration

    def add_clarifications(self, text):
        """Adds clarifications to the transcribed text based on predefined keywords."""
        for keyword, clarification in clarifications.items():
            text = text.replace(keyword, clarification)
        return text

    def write_to_csv(self, file_path, text, model_name, last_end_time, wav_length):
        """Writes the transcription data to the CSV file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([timestamp, os.path.basename(file_path), text, model_name, last_end_time, wav_length])
        os.system('cls')
        print(f"Transcription written to CSV for file: {file_path}")

    def process_existing_files(self):
        """Processes existing .wav files in the directory that haven't been processed yet."""
        for filename in os.listdir(self.directory_to_watch):
            if filename.endswith('.wav') and filename not in self.processed_files:
                file_path = os.path.join(self.directory_to_watch, filename)
                self.process_new_file(file_path)

def main(directory_to_watch):
    """Main function that sets up the file watcher and processes files."""
    medium_model = whisper.load_model("medium.en")
    event_handler = NewFileHandler(medium_model, directory_to_watch)
    event_handler.create_csv_file()
    # Process existing .wav files that are not in the CSV
    event_handler.process_existing_files()
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=False)
    print(f"Watching directory: {directory_to_watch}")
    print(f"CSV file: {event_handler.csv_file}")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    directory_to_watch = r"D:\Police_audio_recordings"  # Change this to your directory
    main(directory_to_watch)
