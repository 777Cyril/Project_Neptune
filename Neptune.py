import time
from mutagen.mp3 import MP3
from mutagen import MutagenError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Flask, jsonify
import threading
import os
from dotenv import load_dotenv
import queue
import glob
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Load environment variables from a .env file
load_dotenv()

config = {
    'email_host': os.getenv('EMAIL_HOST'),
    'email_port': int(os.getenv('EMAIL_PORT', 587)),
    'email_host_user': os.getenv('EMAIL_HOST_USER'),
    'email_host_password': os.getenv('EMAIL_HOST_PASSWORD'),
    'email_use_tls': os.getenv('EMAIL_USE_TLS', 'False') == 'True'
}

# Initialize the file queue
file_queue = queue.Queue()

# Define utility functions
def validate_mp3(file_path):
    try:
        audio = MP3(file_path)  # Attempt to load the MP3 file's metadata using mutagen
        return True  # If no exception is raised, the file is likely a valid MP3
    except MutagenError:
        return False  # If an exception is raised, the file is likely invalid or corrupt
    
def scan_and_queue_existing_mp3s(directory):
    # Get a list of all MP3 files in the directory
    existing_mp3_files = glob.glob(os.path.join(directory, '*.mp3'))
    for file_path in existing_mp3_files:
        if validate_mp3(file_path):
            file_queue.put(file_path)
            print(f"Existing valid MP3 file added to queue: {file_path}")
        else:
            print(f"Existing file failed validation and was not added to queue: {file_path}")

def send_email(subject, body, to_addr, config, attachment_path=None, content_type='plain'):
    msg = MIMEMultipart()   
    msg['From'] = config['email_host_user']
    msg['To'] = to_addr
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, content_type))

    # Attach an MP3 file if the path is provided
    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"')
            msg.attach(part)

    try:
        server = smtplib.SMTP(config['email_host'], config['email_port'])
        if config['email_use_tls']:
            server.starttls()
        server.login(config['email_host_user'], config['email_host_password'])
        server.sendmail(config['email_host_user'], to_addr, msg.as_string())
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        server.quit()

# Define event handler class
class MyHandler(FileSystemEventHandler): #Overriding base class event handler with my own custom handler
    def on_created(self, event):
            # This function is called when a file is created
        if not event.is_directory:  # make sure it's not a directory
            file_path = event.src_path  # get the full path of the created file
            file_name, file_extension = os.path.splitext(file_path)  # split the path to get the name and extension
            if file_extension.lower() == '.mp3':  # check if the file is an MP3
                if validate_mp3(file_path):
                    file_queue.put(file_path)  # Add the file path to the queue if valid
                    print(f"Valid MP3 beat detected and added to queue: {file_path}")
                    # Proceed with additional processing...
                else:
                    print(f"Invalid MP3 file detected: {file_path}")
                    # Handle the invalid file case... 
            else:
                print(f"Not an MP3: {file_path}")
                # Handle non-MP3 files if necessary...
    def on_deleted(self, event):
        print(f"What the fudge! Someone deleted {event.src_path}!")

    def on_modified(self, event):
        print(f"Hey buddy, {event.src_path} has been modified")

    def on_moved(self, event):
        print(f"Ok ok ok, someone moved {event.src_path} to {event.dest_path}")

# Define the Flask application
app = Flask(__name__)
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise ValueError("No SECRET_KEY set for Flask application")

app.secret_key = secret_key

# Define your Flask route
@app.route('/')
def index():
    return jsonify(status="Monitoring")

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

if __name__ == '__main__':
# Pre-scan the directory for existing MP3 files
    scan_and_queue_existing_mp3s("/Users/lifecrzy/Desktop/777")
# Start the observer in a new thread
    observer_thread = threading.Thread(target=start_observer)
    observer_thread.start()
    
    app.run(debug=True, use_reloader=False)
