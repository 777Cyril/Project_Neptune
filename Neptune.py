from app import app
from config import Config
from dotenv import load_dotenv
import os
import queue
from file_monitor import start_observer
from email_service import process_email_queue
import threading
import random
from file_monitor import BeatManager
from airtable_client import Airtable

load_dotenv()  # This loads the .env file at the root of the project

print(os.getenv('FLASK_RUN_PORT'))

# Initialize the email queue globally
email_queue = queue.Queue()

def update_email_queue(email_queue, new_beats, contacts):
    # Extract existing tasks from the queue
    existing_tasks = list(email_queue.queue)
    existing_beats = [task['beat'] for task in existing_tasks]
    # Update Email Queue Logic to add a check against the history log to ensure compliance with the once-a-quarter rule.

    # Combine new and existing beats
    all_beats = list(set(existing_beats + new_beats))
    random.shuffle(all_beats)  # Shuffle to mix new and old beats

    # Clear the existing queue
    while not email_queue.empty():
        email_queue.get_nowait()

    # Repopulate the queue with shuffled beats
    for beat in all_beats:
        for contact in contacts:
            email_queue.put({'contact': contact, 'beat': beat})

def scheduled_beat_check(directory, interval):
    beat_manager = BeatManager()
    new_beats = beat_manager.scan_and_queue_existing_mp3s(directory)
    populate_email_queue(new_beats)
    # Reschedule the beat check
    threading.Timer(interval, scheduled_beat_check, args=(directory, interval)).start()

def fetch_contacts():
    # Fetch contact information dynamically from Airtable
    contacts_client = Airtable('Contacts')
    records = contacts_client.read_records()
    contacts = [{'email': record['fields'].get('Email'), 'name': record['fields'].get('Name')} for record in records if 'Email' in record['fields']]
    return contacts

def populate_email_queue(beats):
    contacts = fetch_contacts()  # Fetch contacts dynamically
    for beat in beats:
        for contact in contacts:
            email_task = {'contact': contact, 'beat': beat}
            email_queue.put(email_task)

def ensure_log_directory_exists():
    if not os.path.exists(Config.LOG_DIR):
        os.makedirs(Config.LOG_DIR)

if __name__ == '__main__':
    # Initial setup: Ensure log directory exists and populate the email queue
    ensure_log_directory_exists()

    beat_manager = BeatManager()

    valid_beats = beat_manager.scan_and_queue_existing_mp3s(Config.MONITOR_DIRECTORY)
    
    populate_email_queue(valid_beats)
    
    # Start the email processing thread
    email_thread = threading.Thread(target=process_email_queue, args=(email_queue,))
    email_thread.start()

    # Start the filesystem observer thread
    observer_thread = threading.Thread(target=start_observer) # Start the observer in a new thread
    observer_thread.start()

    # Start the scheduled beat check
    scheduled_beat_check(Config.MONITOR_DIRECTORY, 25200)  # 25200 seconds = 7 hours

    # Start the Flask application
    app.run(debug=True, port=Config.FLASK_RUN_PORT, use_reloader=False)
