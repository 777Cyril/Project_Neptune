import base64
import os.path
import os
import requests
import queue
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from logger import setup_logger
from config import Config
from config import SCOPES
from dotenv import load_dotenv
from airtable import Airtable
from datetime import datetime

load_dotenv()

class Airtable:
    def __init__(self, table_name):
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.access_token = os.getenv('AIRTABLE_PERSONAL_ACCESS_TOKEN')
        self.table_name = table_name
        self.endpoint = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def create_record(self, data):
        response = requests.post(self.endpoint, json={"fields": data}, headers=self.headers)
        return response.json()

    def read_records(self, filter_formula=None):
        params = {}
        if filter_formula:
            params['filterByFormula'] = filter_formula
            
        response = requests.get(self.endpoint, headers=self.headers, params=params)
        return response.json()

    def update_record(self, record_id, data):
        record_endpoint = f"{self.endpoint}/{record_id}"
        response = requests.patch(record_endpoint, json={"fields": data}, headers=self.headers)
        return response.json()

    def delete_record(self, record_id):
        record_endpoint = f"{self.endpoint}/{record_id}"
        response = requests.delete(record_endpoint, headers=self.headers)
        return response.json()

'''users_airtable_client = Airtable('Users')
beats_airtable_client = Airtable('Beats')   
contacts_airtable_client = Airtable('Contacts')
historylog_airtable_client = Airtable('HistoryLog')'''

# Setup logger for this service
email_logger = setup_logger("email_service")

def process_email_queue(email_queue):
    while True:
        try:
            task = email_queue.get(block=True)
            subject = "beats"  # Example subject
            body_text = "777"  # Example body text
            to_email = task['contact']['email']  # Extracting email from the task
            attachment_file = task['beat']
            send_email(subject, body_text, to_email, attachment_file)
            email_queue.task_done()
        except queue.Empty:
            break  # Exit if the queue is empty

def get_gmail_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def send_email(subject, body_text, to_email, attachment_file):
    service = get_gmail_service()
    message = MIMEMultipart()
    message['to'] = to_email
    message['subject'] = subject

    # Add the plain text to the email
    message.attach(MIMEText(body_text))

    # Attach the MP3 file
    if attachment_file:
        part = MIMEBase('application', 'octet-stream')
        with open(attachment_file, 'rb') as file:
            part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            f'attachment; filename={os.path.basename(attachment_file)}')
            message.attach(part)

    # Encode the entire message to send via the Gmail API
    raw_message_no_attachment = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message_no_attachment}).execute()
        print(f'Message Id: {send_message["id"]}')
        return send_message
    except Exception as e:
        print(f'An error occurred: {e}')
        return None
