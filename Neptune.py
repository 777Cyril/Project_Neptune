from app import app
from config import Config
import queue
from file_monitor import scan_and_queue_existing_mp3s, start_observer
from email_service import process_email_queue
from contacts import contacts
import threading
import random


# Initialize the email queue globally
email_queue = queue.Queue()

def update_email_queue(email_queue, new_beats, contacts):
    # Extract existing tasks from the queue
    existing_tasks = list(email_queue.queue)
    existing_beats = [task['beat'] for task in existing_tasks]

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

def scheduled_beat_check(directory, interval, email_queue, contacts):
    new_beats = scan_and_queue_existing_mp3s(directory)
    update_email_queue(email_queue, new_beats, contacts)

    # Schedule the next execution of this function 
    threading.Timer(interval, scheduled_beat_check, [directory, interval, email_queue, contacts]).start()

def populate_email_queue(beats, contacts):
    for beat in beats:
        for contact in contacts:
            email_task = {'contact': contact, 'beat': beat}
            email_queue.put(email_task)

if __name__ == '__main__':
    valid_beats = scan_and_queue_existing_mp3s("/Users/lifecrzy/Desktop/777")
    populate_email_queue(valid_beats, contacts)

    email_thread = threading.Thread(target=process_email_queue, args=(email_queue,))
    email_thread.start()

    observer_thread = threading.Thread(target=start_observer) # Start the observer in a new thread
    observer_thread.start()

    scheduled_beat_check("/Users/lifecrzy/Desktop/777", 25200, email_queue, contacts)  # 25200 seconds = 7 hours

    app.run(debug=True, use_reloader=False)
