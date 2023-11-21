import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from logger import setup_logger
import os
import queue
from config import Config

# Setup logger for this service
email_logger = setup_logger("email_service")

def process_email_queue(email_queue):
    while True:
        try:
            task = email_queue.get(block=True)
            send_email("beat", "777", task['contact']['email'], Config, task['beat'])
            email_queue.task_done()
        except queue.Empty:
            break  # Exit if the queue is empty

def send_email(subject, body, to_addr, config, attachment_path, content_type='plain'):
    msg = MIMEMultipart()   
    msg['From'] = config['email_host_user']
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, content_type))

    # Attach an MP3 file
    with open(attachment_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"')
        msg.attach(part)

    try:
        server = smtplib.SMTP(config['email_host'], config['email_port'])
        email_logger.info(f"Connecting to email server for sending to {to_addr}")
        if config['email_use_tls']:
            server.starttls()
        server.login(config['email_host_user'], config['email_host_password'])
        server.sendmail(config['email_host_user'], to_addr, msg.as_string())
        email_logger.info(f"Email sent successfully to {to_addr}")
    except Exception as e:
        email_logger.error(f"Failed to send email to {to_addr}: {e}")
    finally:
        server.quit()
        email_logger.info("Email server connection closed")
