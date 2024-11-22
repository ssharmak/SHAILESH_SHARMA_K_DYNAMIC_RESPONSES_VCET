from datetime import datetime, timedelta
import requests
from flask import Flask, jsonify, render_template, request
import json

app = Flask(__name__)

# Load settings
with open("settings.json") as f:
    settings = json.load(f)

ASANA_API_KEY = settings["asana_api_key"]

# Asana API Base URL
ASANA_BASE_URL = "https://app.asana.com/api/1.0"

# Headers for API authentication
headers = {
    "Authorization": f"Bearer {ASANA_API_KEY}",
    "Content-Type": "application/json"
}

# Route to fetch all projects and their tasks
@app.route("/projects_with_tasks", methods=["GET"])
def get_projects_with_tasks():
    url = f"{ASANA_BASE_URL}/projects"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({"error": "Unable to fetch projects", "details": response.json()}), 400

    projects = response.json()["data"]
    projects_with_tasks = []

    for project in projects:
        project_id = project["gid"]
        project_name = project["name"]

        # Fetch tasks for the current project
        tasks_url = f"{ASANA_BASE_URL}/projects/{project_id}/tasks"
        tasks_response = requests.get(tasks_url, headers=headers)

        if tasks_response.status_code == 200:
            tasks = tasks_response.json()["data"]

            # Fetch task details including due dates and priorities
            detailed_tasks = []
            for task in tasks:
                task_details_url = f"{ASANA_BASE_URL}/tasks/{task['gid']}"
                task_details_response = requests.get(task_details_url, headers=headers)

                if task_details_response.status_code == 200:
                    task_details = task_details_response.json()["data"]
                    detailed_tasks.append({
                        "id": task_details["gid"],
                        "name": task_details["name"],
                        "due_date": task_details.get("due_on", "No Due Date"),
                        "priority": task_details.get("priority", "low")
                    })

            projects_with_tasks.append({
                "id": project_id,
                "name": project_name,
                "tasks": detailed_tasks
            })

    return jsonify(projects_with_tasks)

# Route to update due date and dependent tasks
@app.route("/update_due_date/<task_id>", methods=["POST"])
def update_due_date_with_priority(task_id):
    # Get the priority from the request data (we don't need the due date)
    data = request.json
    priority = data.get("priority")  # Priority should be passed

    if not priority:
        return jsonify({"error": "Priority not provided"}), 400

    # Get today's date and calculate the new due date
    today = datetime.today()

    if priority == "high":
        new_due_date = add_days(today, 2)  # High priority: 2 days
    elif priority == "medium":
        new_due_date = add_days(today, 7)  # Medium priority: 7 days
    elif priority == "low":
        new_due_date = add_days(today, 14)  # Low priority: 14 days
    else:
        return jsonify({"error": "Invalid priority provided"}), 400

    # Update the task's due date
    task_url = f"{ASANA_BASE_URL}/tasks/{task_id}"
    payload = {"data": {"due_on": new_due_date, "priority": priority}}
    response = requests.put(task_url, headers=headers, json=payload)

    if response.status_code != 200:
        return jsonify({"error": "Unable to update due date", "details": response.json()}), 400

    # Fetch the project and other tasks in the project
    task_details_url = f"{ASANA_BASE_URL}/tasks/{task_id}"
    task_details_response = requests.get(task_details_url, headers=headers)

    if task_details_response.status_code == 200:
        task_details = task_details_response.json()["data"]
        project_id = task_details["projects"][0]["gid"]

        tasks_url = f"{ASANA_BASE_URL}/projects/{project_id}/tasks"
        tasks_response = requests.get(tasks_url, headers=headers)

        if tasks_response.status_code != 200:
            return jsonify({"error": "Unable to fetch tasks in project"}), 400

        tasks = tasks_response.json()["data"]

        # Update medium and low-priority tasks based on high-priority task's new due date
        for task in tasks:
            task_details_url = f"{ASANA_BASE_URL}/tasks/{task['gid']}"
            task_details_response = requests.get(task_details_url, headers=headers)

            if task_details_response.status_code == 200:
                task_details = task_details_response.json()["data"]
                task_priority = task_details.get("priority", "low")  # Default to low if no priority set

                if priority == "high" and task_priority == "medium":
                    new_due_date = add_days(new_due_date, 7)
                    update_task_due_date(task_details_url, new_due_date)
                elif priority in ["high", "medium"] and task_priority == "low":
                    new_due_date = add_days(new_due_date, 14)
                    update_task_due_date(task_details_url, new_due_date)

    return jsonify({"message": "Due date updated successfully"})

# Function to update task due date
def update_task_due_date(task_url, new_due_date):
    payload = {"data": {"due_on": new_due_date}}
    requests.put(task_url, headers=headers, json=payload)

# Function to add days to a given due date and skip Sundays
def add_days(start_date, days_to_add):
    new_due_date = start_date + timedelta(days=days_to_add)
    return skip_sundays(new_due_date).strftime("%Y-%m-%d")

# Function to skip Sundays
def skip_sundays(due_date):
    while due_date.weekday() == 6:  # 6 is Sunday
        due_date += timedelta(days=1)
    return due_date

# Route to render projects and tasks on the web interface
@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
