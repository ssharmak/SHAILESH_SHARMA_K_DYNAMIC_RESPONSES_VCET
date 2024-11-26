import requests
import json
import os
from datetime import datetime

# Load settings from settings.json
config_path = os.path.join(os.path.dirname(__file__), "../config/settings.json")
with open(config_path, "r") as f:
    settings = json.load(f)

API_URL = "https://app.asana.com/api/1.0"

def get_headers():
    return {
        "Authorization": f"Bearer {settings['api_token']}",
        "Content-Type": "application/json"
    }

def get_tasks():
    """Fetch tasks from the specified project."""
    url = f"{API_URL}/projects/{settings['project_id']}/tasks?opt_expand=custom_fields,assignee_status,sections"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Error fetching tasks: {response.status_code} - {response.json()}")
        return []

def fetch_task_details(task_id):
    """
    Fetch task details from Asana using the API.
    """
   
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}"
    headers = {
        "Authorization": f"Bearer {settings['api_token']}",
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", {})
    else:
        raise Exception(f"Failed to fetch task details: {response.status_code} - {response.text}")
def update_task_due_date(task_id, due_date):
    """
    Update the due date for a specific task and display the task name.
    """
    url = f"{API_URL}/tasks/{task_id}"
    data = {"data": {"due_on": due_date}}

    # Fetch task details to get the task name
    try:
        response_task = requests.get(url, headers=get_headers())
        response_task.raise_for_status()
        task_name = response_task.json().get("data", {}).get("name", "Unknown Task")
    except Exception as e:
        task_name = "Unknown Task"
        print(f"Error fetching task details for ID {task_id}: {e}")

    # Update the due date
    response = requests.put(url, headers=get_headers(), json=data)
    if response.status_code == 200:
        print(f"Task '{task_name}' (ID: {task_id}) updated with due date {due_date}")
    else:
        print(f"Error updating task '{task_name}' (ID: {task_id}): {response.status_code} - {response.json()}")

def get_section_tasks(section_name):
    """
    Fetch all tasks in a specific section by name.
    """
    # Get all sections in the project
    url = f"{API_URL}/projects/{settings['project_id']}/sections"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()  # Raise error for invalid response
    sections = response.json().get("data", [])

    # Find the section by name
    section = next((sec for sec in sections if sec["name"] == section_name), None)
    if not section:
        raise ValueError(f"Section '{section_name}' not found in the project.")

    # Get tasks in the section (explicitly request due_on field)
    url = f"{API_URL}/sections/{section['gid']}/tasks?opt_fields=name,due_on"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()  # Raise error for invalid response
    return response.json().get("data", [])

def get_task_details(task_id):
    """Fetch details of a specific task."""
    url = f"{API_URL}/tasks/{task_id}?opt_expand=custom_fields,assignee_status,sections"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        return response.json().get("data", {})
    else:
        print(f"Error fetching task details for ID {task_id}: {response.status_code} - {response.json()}")
        return {}

def get_task_section(task_id):
    """
    Get the section name of a specific task.
    """
    task_details = get_task_details(task_id)
    sections = task_details.get("memberships", [])
    if sections:
        # Assuming the task is in one section, return the first one
        return sections[0].get("section", {}).get("name", "Unknown Section")
    return "Unknown Section"
