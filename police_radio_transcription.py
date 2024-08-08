import whisper
import os
import csv
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from queue import Queue
from keywords import clarifications

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, medium_model, directory_to_watch):
        self.medium_model = medium_model
        self.directory_to_watch = directory_to_watch
        self.csv_file = os.path.join(directory_to_watch, "transcriptions.csv")
        self.file_queue = Queue()
        self.processed_files = self.load_processed_files()

    def load_processed_files(self):
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
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "File", "Transcription", "Model"])

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.wav'):
            time.sleep(0.1)
            self.file_queue.put(event.src_path)
            self.process_files()

    def process_files(self):
        while not self.file_queue.empty():
            file_path = self.file_queue.get()
            self.process_new_file(file_path)

    def process_new_file(self, file_path):
        file_name = os.path.basename(file_path)
        if file_name not in self.processed_files:
            print(f"Processing new file: {file_path}")
            try:
                result = self.medium_model.transcribe(file_path, without_timestamps=True, fp16=False)
                text = result["text"]

                text_with_clarifications = self.add_clarifications(text)
                self.write_to_csv(file_path, text_with_clarifications, "medium.en")
                self.processed_files.add(file_name)

            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    def add_clarifications(self, text):
        for keyword, clarification in clarifications.items():
            text = text.replace(keyword, clarification)
        return text

    def write_to_csv(self, file_path, text, model_name):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([timestamp, os.path.basename(file_path), text, model_name])
        os.system('cls')
        print(f"Transcription written to CSV for file: {file_path}")

    def process_existing_files(self):
        for filename in os.listdir(self.directory_to_watch):
            if filename.endswith('.wav') and filename not in self.processed_files:
                file_path = os.path.join(self.directory_to_watch, filename)
                self.process_new_file(file_path)

def main(directory_to_watch):
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
