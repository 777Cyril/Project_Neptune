from flask import Flask, jsonify
from config import Config

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