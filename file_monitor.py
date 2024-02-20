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
from datetime import datetime
from email_service import send_email
from airtable_client import access_token


file_monitor_logger = setup_logger("file_monitor")

def start_observer():
    path = Config.MONITOR_DIRECTORY
    if not path:
        raise ValueError("The MONITOR_DIRECTORY environment variable is not set")
    beat_manager = BeatManager()  # Create an instance of BeatManager
    event_handler = MyHandler(beat_manager)  # Pass BeatManager instance to MyHandler
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Will scan the specified directory, validate the MP3 files, and return a list of the valid ones.
# This list is then used in neptune.py to populate the email queue with tasks.
# Each task will consist of a beat and a contact to whom the email will be sent.
class MyHandler(FileSystemEventHandler):
    def __init__(self, beat_manager):
        self.beat_manager = beat_manager

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if file_path.lower().endswith('.mp3'):
                if self.beat_manager.validate_mp3(file_path):
                    metadata = self.beat_manager.extract_metadata(file_path)
                    if metadata:
                        self.beat_manager.add_beat_to_airtable(metadata)
                        file_monitor_logger.info(f"Valid MP3 beat detected and added to Airtable: {file_path}")
                        self.process_beat_for_all_contacts(file_path, metadata)
                    else:
                        file_monitor_logger.warning(f"Valid MP3 file detected but metadata extraction failed: {file_path}")
                else:
                    file_monitor_logger.warning(f"Invalid MP3 file detected: {file_path}")

    '''def on_deleted(self, event):
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

            if is_within_monitored_folder(new_path):  # You need to implement this check
                #updated_metadata = {'Beat Name': new_beat_name}
                #update_beat_in_airtable(old_beat_name, updated_metadata)
               # file_monitor_logger.info(f"MP3 file renamed within folder: {old_beat_name} to {new_beat_name}")
            else:
               # delete_beat_from_airtable(old_beat_name)
               # file_monitor_logger.info(f"MP3 file moved out of folder and removed from Airtable: {old_beat_name}")'''

class BeatManager:
    def __init__(self):
        self.airtable_beats = Airtable('Beats', access_token)
        self.airtable_contacts = Airtable('Contacts', access_token)
        self.airtable_history_log = Airtable('HistoryLog', access_token)
        self.logger = setup_logger("beat_manager")

    def extract_metadata(self, file_path):
        try:
            audio = MP3(file_path)
            beat_name = os.path.basename(file_path)
            date_created = time.ctime(os.path.getmtime(file_path))
            minutes, seconds = divmod(int(audio.info.length), 60)
            length_formatted = f"{minutes}:{seconds:02d}"

            metadata = {
                'Beat Name': beat_name,
                'File Path': file_path,
                'Key': None, # To be implemented later
                'BPM': None, # To be implemented later
                'Length': length_formatted,
                'Date Created': date_created,
                'Genre': None, # users to fill this in later or implement a feature that suggests genres based on other metadata or analysis.
            }
            return metadata
        except MutagenError as e:
            self.logger.error(f"Error extracting metadata from {file_path}: {e}")
            return None

    def validate_mp3(self, file_path):
        try:
            MP3(file_path)  # Attempt to load the MP3 file's metadata
            return True
        except MutagenError:
            return False

    def add_beat_to_airtable(self, metadata):
        response = self.airtable_beats.create_record(metadata)
        if 'id' in response:
            self.logger.info("Successfully added beat to Airtable.")
        else:
            self.logger.error(f"Failed to add beat to Airtable: {response.get('error', 'Unknown Error')}")

    def scan_and_queue_existing_mp3s(self, directory):
        valid_mp3_files = []
        existing_mp3_files = glob.glob(os.path.join(directory, '*.mp3'))
        sorted_files = sorted(existing_mp3_files, key=os.path.getmtime, reverse=True)

        for file_path in sorted_files:
            if self.validate_mp3(file_path):
                valid_mp3_files.append(file_path)
                metadata = self.extract_metadata(file_path)
                if metadata:
                    self.add_beat_to_airtable(metadata)
                self.logger.info(f"Existing valid MP3 file added to queue: {file_path}")
            else:
                self.logger.warning(f"Existing file failed validation and was not added to queue: {file_path}")
        return valid_mp3_files
    
    def update_email_queue_with_new_beats(self, email_queue, new_beats, contacts):
        for beat_path in new_beats:
            beat_metadata = self.extract_metadata(beat_path)
            if beat_metadata:
                self.add_beat_to_airtable(beat_metadata)
                for contact in contacts:
                    contact_email = contact['fields']['Email']
                    contact_name = contact['fields']['Contact Name']
                    composite_key = self.construct_composite_primary_key(contact_name, contact_email, beat_metadata['Beat Name'])
                    
                    # Check if the beat has already been sent this quarter
                    if not self.check_record_exists_in_history_log(composite_key):
                        # If not, add to email queue
                        email_queue.put({'contact': contact, 'beat': beat_metadata['Beat Name'], 'beat_path': beat_path})
                        
                        # Log the event in 'HistoryLog'
                        self.log_event_in_history_log(composite_key)
    
    def construct_composite_primary_key(self, contact_name, email, beat_name):
        date_sent = datetime.now().strftime('%Y-%m-%d')
        composite_key = f"{contact_name}-{email}-{beat_name}-{date_sent}"
        return composite_key
    
    def check_record_exists(self, composite_key):
    # Replace spaces with '+' and wrap the composite_key in quotes for the formula
        formula = f"{{Composite Key}} = '{composite_key.replace(' ', '+')}'"
        records = self.read_records(filter_formula=formula)
        return len(records.get('records', [])) > 0


    def log_event(self, composite_key):
        data = {"Composite Key": composite_key}
        self.airtable_history_log.create_record(data)

    def process_beat_for_all_contacts(self, beat_path):
        beat_metadata = self.extract_metadata(beat_path)
        if beat_metadata:
            self.add_beat_to_airtable(beat_metadata)
            contacts = self.airtable_contacts.read_records()
            for contact in contacts['records']:
                email = contact['fields']['Email']
                contact_name = contact['fields']['Contact Name']
                composite_key = self.construct_composite_primary_key(contact_name, email, beat_metadata['Beat Name'])
                if not self.airtable_history_log.check_record_exists(composite_key):
                    # Logic to send the email
                    send_email(subject="beats", body_text= "", to_email=email, attachment_file=beat_path)
                    # Log the event in 'HistoryLog'
                    self.airtable_history_log.create_record({"Composite Key": composite_key})



