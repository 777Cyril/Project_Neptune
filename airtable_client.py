from airtable import Airtable
import requests
import os.path
import os

access_token = os.getenv('AIRTABLE_PERSONAL_ACCESS_TOKEN')

class Airtable:
    def __init__(self, table_name, access_token):
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.access_token = access_token
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
    
    def get_record_by_id(self, record_id):
        """Fetch a single record by its ID."""
        record_endpoint = f"{self.endpoint}/{record_id}"
        response = requests.get(record_endpoint, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching record by ID: {response.status_code}")
            return None