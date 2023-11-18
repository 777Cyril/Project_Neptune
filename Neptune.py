from app import app
import time
import threading
from config import Config
from file_monitor import scan_and_queue_existing_mp3s, start_observer
from email_service import send_email
import queue
from contacts import contacts


# Initialize the email queue globally
email_queue = queue.Queue()


if __name__ == '__main__':
    scan_and_queue_existing_mp3s("/Users/lifecrzy/Desktop/777")
    observer_thread = threading.Thread(target=start_observer) # Start the observer in a new thread
    observer_thread.start()
    app.run(debug=True, use_reloader=False)
