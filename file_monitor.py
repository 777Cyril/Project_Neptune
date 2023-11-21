import os
import glob
from mutagen.mp3 import MP3
from mutagen import MutagenError
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from logger import setup_logger


file_monitor_logger = setup_logger("file_monitor")

# Function definitions for validate_mp3, scan_and_queue_existing_mp3s, and MyHandler class...
def validate_mp3(file_path):
    try:
        audio = MP3(file_path)  # Attempt to load the MP3 file's metadata using mutagen
        return True  # If no exception is raised, the file is likely a valid MP3
    except MutagenError:
        return False  # If an exception is raised, the file is likely invalid or corrupt


# Will scan the specified directory, validate the MP3 files, and return a list of the valid ones.
# This list is then used in neptune.py to populate the email queue with tasks.
# Each task will consist of a beat and a contact to whom the email will be sent.
def scan_and_queue_existing_mp3s(directory):
    valid_mp3_files = []  # List to store valid MP3 file paths
    existing_mp3_files = glob.glob(os.path.join(directory, '*.mp3')) # Get a list of all MP3 files in the directory
    
    sorted_files = sorted(existing_mp3_files, key=os.path.getmtime, reverse=True)

    for file_path in sorted_files:
        if validate_mp3(file_path):
            valid_mp3_files.append(file_path)
            print(f"Existing valid MP3 file added to queue: {file_path}")
        else:
            print(f"Existing file failed validation and was not added to queue: {file_path}")
    return valid_mp3_files

# Define event handler class
class MyHandler(FileSystemEventHandler): 
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_name, file_extension = os.path.splitext(file_path)
            if file_extension.lower() == '.mp3':
                if validate_mp3(file_path):
                    file_monitor_logger.info(f"Valid MP3 beat detected: {file_name}, Path: {file_path}")
                else:
                    file_monitor_logger.warning(f"Invalid MP3 file detected: {file_name}, Path: {file_path}")
            else:
                file_monitor_logger.info(f"Non-MP3 file detected: {file_name}, Path: {file_path}")

    def on_deleted(self, event):
        file_monitor_logger.info(f"File deleted: {os.path.basename(event.src_path)}")

    def on_modified(self, event):
        file_monitor_logger.info(f"File modified: {os.path.basename(event.src_path)}")

    def on_moved(self, event):
        file_monitor_logger.info(f"File moved from {os.path.basename(event.src_path)} to {os.path.basename(event.dest_path)}")
        
# Function to start the observer
def start_observer():
    path = os.getenv('MONITOR_DIRECTORY') # folder to monitor for new beats
    if not path:
        raise ValueError("The MONITOR_DIRECTORY environment variable is not set")
    event_handler = MyHandler()
    observer = Observer() # Set up the observer
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
     while True: #keep the observer running
        time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()