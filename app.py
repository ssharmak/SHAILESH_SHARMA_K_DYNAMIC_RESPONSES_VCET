from datetime import datetime, timedelta
import requests
from flask import Flask, jsonify, render_template, request
import json
import threading
import time

app = Flask(__name__)

# Load settings
with open("settings.json") as f:
    settings = json.load(f)

ASANA_API_KEY = settings["asana_api_key"]
ASANA_BASE_URL = "https://app.asana.com/api/1.0"

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

        # Fetch tasks with custom fields
        tasks_url = f"{ASANA_BASE_URL}/projects/{project_id}/tasks?opt_fields=name,due_on,custom_fields"
        tasks_response = requests.get(tasks_url, headers=headers)

        if tasks_response.status_code == 200:
            tasks = tasks_response.json()["data"]

            detailed_tasks = []
            for task in tasks:
                priority = "low"  # Default to low priority
                for field in task.get("custom_fields", []):
                    if field["name"].lower() == "priority":  # Match the priority custom field
                        priority = field.get("display_value", "low").lower()

                detailed_tasks.append({
                    "id": task["gid"],
                    "name": task["name"],
                    "due_date": task.get("due_on", "No Due Date"),
                    "priority": priority
                })

            projects_with_tasks.append({
                "id": project_id,
                "name": project_name,
                "tasks": detailed_tasks
            })

    return jsonify(projects_with_tasks)


# Route to update due date dynamically based on priority
@app.route("/update_due_date/<task_id>", methods=["POST"])
def update_due_date(task_id):
    data = request.json
    priority = data.get("priority", "low").lower()  # Default to low if no priority provided

    today = datetime.today()
    if priority == "high":
        new_due_date = add_days(today, 2)
    elif priority == "medium":
        new_due_date = add_days(today, 7)
    else:
        new_due_date = add_days(today, 14)

    task_url = f"{ASANA_BASE_URL}/tasks/{task_id}"
    payload = {"data": {"due_on": new_due_date}}
    response = requests.put(task_url, headers=headers, json=payload)

    if response.status_code != 200:
        return jsonify({"error": "Unable to update due date", "details": response.json()}), 400

    return jsonify({"message": "Due date updated successfully"})


# Background task to update all tasks' due dates periodically
def update_task_due_dates():
    while True:
        print("Running periodic task update...")
        projects_response = requests.get(f"{ASANA_BASE_URL}/projects", headers=headers)

        if projects_response.status_code == 200:
            projects = projects_response.json()["data"]
            for project in projects:
                project_id = project["gid"]
                tasks_url = f"{ASANA_BASE_URL}/projects/{project_id}/tasks?opt_fields=name,custom_fields"
                tasks_response = requests.get(tasks_url, headers=headers)

                if tasks_response.status_code == 200:
                    tasks = tasks_response.json()["data"]
                    for task in tasks:
                        task_id = task["gid"]
                        priority = "low"  # Default to low
                        for field in task.get("custom_fields", []):
                            if field["name"].lower() == "priority":
                                priority = field.get("display_value", "low").lower()

                        # Assign due dates dynamically based on priority
                        today = datetime.today()
                        if priority == "high":
                            new_due_date = add_days(today, 2)
                        elif priority == "medium":
                            new_due_date = add_days(today, 7)
                        else:
                            new_due_date = add_days(today, 14)

                        task_url = f"{ASANA_BASE_URL}/tasks/{task_id}"
                        payload = {"data": {"due_on": new_due_date}}
                        requests.put(task_url, headers=headers, json=payload)

        time.sleep(60)


# Function to add days and skip Sundays
def add_days(start_date, days_to_add):
    new_due_date = start_date + timedelta(days=days_to_add)
    return skip_sundays(new_due_date).strftime("%Y-%m-%d")


def skip_sundays(due_date):
    while due_date.weekday() == 6:  # Sunday
        due_date += timedelta(days=1)
    return due_date


# Start background task
def start_background_task():
    thread = threading.Thread(target=update_task_due_dates)
    thread.daemon = True
    thread.start()


@app.route("/")
def index():
    return render_template("index.html")


start_background_task()

if __name__ == "__main__":
    app.run(debug=True)
