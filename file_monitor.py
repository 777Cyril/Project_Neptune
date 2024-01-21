import os
import glob
import time
import requests
from airtable import Airtable
from mutagen.mp3 import MP3
from mutagen import MutagenError
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from logger import setup_logger
from config import Config

AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
AIRTABLE_PERSONAL_ACCESS_TOKEN = os.environ.get('AIRTABLE_PERSONAL_ACCESS_TOKEN')
AIRTABLE_BEATS_TABLE_NAME = 'Beats' 

#headers = {
    #'Authorization': f'Bearer {AIRTABLE_PERSONAL_ACCESS_TOKEN}'
#}

#airtable_beats = Airtable(AIRTABLE_BASE_ID, AIRTABLE_BEATS_TABLE_NAME, api_key=None, headers=headers)
#airtable_contacts = Airtable(AIRTABLE_BASE_ID, 'Contacts', api_key=None, headers=headers)
#airtable_email_queue = Airtable(AIRTABLE_BASE_ID, 'EmailQueue', api_key=None, headers=headers)

file_monitor_logger = setup_logger("file_monitor")


#Function definitions
def extract_metadata(file_path):
    audio = MP3(file_path)
    beat_name = os.path.basename(file_path)
    date_created = time.ctime(os.path.getmtime(file_path))
    
    if audio.info.length:
        minutes, seconds = divmod(int(audio.info.length), 60)
        length_formatted = f"{minutes}:{seconds:02d}"
    else:
        length_formatted = "Unknown Length"

    metadata = {
        'Beat Name': beat_name,
        'File Path': file_path,
        'Key': None, # To be implemented later
        'BPM': None, # To be implemented later
        'Length': length_formatted,
        'Genre': None, # users to fill this in later or implement a feature that suggests genres based on other metadata or analysis.
        'Date Created': date_created
    }
    return metadata

def validate_mp3(file_path):
    try:
        audio = MP3(file_path)  # Attempt to load the MP3 file's metadata using mutagen
        return True  # If no exception is raised, the file is likely a valid MP3
    except MutagenError:
        return False  # If an exception is raised, the file is likely invalid or corrupt

#Airtable CRUD Functions
def add_beat_to_airtable(metadata):
    airtable_api_url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BEATS_TABLE_NAME}'
    headers = {
        'Authorization': f'Bearer {AIRTABLE_PERSONAL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Preparing the payload for the POST request
    data = {
        'fields': metadata
    }

    response = requests.post(airtable_api_url, headers=headers, json=data)

    if response.status_code in [200, 201]:  # 201 is the typical success status code for POST
        print("Successfully added beat to Airtable.")
    else:
        print(f"Failed to add beat to Airtable: {response.status_code} {response.text}")

def update_beat_in_airtable(beat_name, updated_metadata):
    headers = {
        'Authorization': f'Bearer {AIRTABLE_PERSONAL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Logic to find the record ID by beat_name
    # ...

    # Airtable API URL for updating a specific record
    #update_url = f'{airtable_api_url}/{record_id}'

    #response = requests.patch(update_url, headers=headers, json={"fields": updated_metadata})
    
    #if response.status_code == 200:
      #  print("Successfully updated beat in Airtable.")
   # else:
       # print(f"Failed to update beat in Airtable: {response.status_code} {response.text}")

def delete_beat_from_airtable(beat_name):
    # Logic to find and delete a record from Airtable
    # Example: You might search for a record with a matching 'Beat Name' and then send a DELETE request
    pass

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
                    # Extract metadata and upload to Airtable
                    metadata = extract_metadata(file_path)
                    add_beat_to_airtable(metadata)
                    file_monitor_logger.info(f"Valid MP3 beat detected: {file_name}, Path: {file_path}")
                else:
                    file_monitor_logger.warning(f"Invalid MP3 file detected: {file_name}, Path: {file_path}")
            else:
                file_monitor_logger.info(f"Non-MP3 file detected: {file_name}, Path: {file_path}")
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.mp3'):
            file_path = event.src_path
            beat_name = os.path.basename(file_path)
            delete_beat_from_airtable(beat_name)
            file_monitor_logger.info(f"File deleted: {os.path.basename(event.src_path)}")

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.mp3'):
            file_path = event.src_path
            beat_name = os.path.basename(file_path)
            updated_metadata = extract_metadata(file_path)
            update_beat_in_airtable(beat_name, updated_metadata)
            file_monitor_logger.info(f"File modified: {os.path.basename(event.src_path)}")

    def on_moved(self, event):
        if not event.is_directory and event.src_path.endswith('.mp3'):
            old_path = event.src_path
            new_path = event.dest_path
            old_beat_name = os.path.basename(old_path)
            new_beat_name = os.path.basename(new_path)

            #if is_within_monitored_folder(new_path):  # You need to implement this check
                #updated_metadata = {'Beat Name': new_beat_name}
                #update_beat_in_airtable(old_beat_name, updated_metadata)
               # file_monitor_logger.info(f"MP3 file renamed within folder: {old_beat_name} to {new_beat_name}")
            #else:
               # delete_beat_from_airtable(old_beat_name)
               # file_monitor_logger.info(f"MP3 file moved out of folder and removed from Airtable: {old_beat_name}")
        
# Function to start the observer
def start_observer():
    path = Config.MONITOR_DIRECTORY # folder to monitor for new beats
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