import requests
import sys
import os
import sqlite3
from datetime import datetime, timedelta
from config import ASANA_API_URL, HEADERS


def init_db():
    """Initialize SQLite database to track task extensions"""
    # Use Render's persistent storage path
    db_path = os.path.join('/opt/render/project/.data', 'task_extensions.db')
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_extensions (
            high_priority_task_id TEXT,
            extended_task_id TEXT,
            original_due_date TEXT,
            UNIQUE(high_priority_task_id, extended_task_id)
        )
    ''')
    conn.commit()
    conn.close()

def update_due_date(task_id, priority):
    """Set initial due date based on priority"""
    due_date = calculate_due_date(priority)
    url = f"{ASANA_API_URL}/tasks/{task_id}"
    payload = {"data": {"due_on": due_date}}
   
    response = requests.put(url, json=payload, headers=HEADERS)
    if response.status_code == 200:
        print(f"Task {task_id} due date set to {due_date} based on {priority} priority")
    else:
        raise Exception(f"Failed to update due date: {response.status_code}")

def calculate_due_date(priority):
    """Calculate due date based on priority"""
    today = datetime.today()
    if priority == "Low":
        due_date = today + timedelta(days=14)
    elif priority == "Mid" or priority == "Medium":
        due_date = today + timedelta(days=7)
    elif priority == "High":
        due_date = today + timedelta(days=2)
    else:
        due_date = today + timedelta(days=7)  # Default case
   
    return due_date.strftime("%Y-%m-%d")

def record_task_extension(high_priority_task_id, extended_task_id, original_due_date):
    """Record the extension of a task due to a high-priority task"""
    db_path = os.path.join('/opt/render/project/.data', 'task_extensions.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO task_extensions 
            (high_priority_task_id, extended_task_id, original_due_date) 
            VALUES (?, ?, ?)
        ''', (high_priority_task_id, extended_task_id, original_due_date))
        conn.commit()
    except Exception as e:
        print(f"Error recording task extension: {e}")
    finally:
        conn.close()

def get_extended_tasks(high_priority_task_id):
    """Retrieve tasks extended by a specific high-priority task"""
    db_path = os.path.join('/opt/render/project/.data', 'task_extensions.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT extended_task_id, original_due_date 
        FROM task_extensions 
        WHERE high_priority_task_id = ?
    ''', (high_priority_task_id,))
    extended_tasks = cursor.fetchall()
    conn.close()
    return extended_tasks

def clear_task_extensions(high_priority_task_id):
    """Clear extensions for a specific high-priority task"""
    db_path = os.path.join('/opt/render/project/.data', 'task_extensions.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM task_extensions 
        WHERE high_priority_task_id = ?
    ''', (high_priority_task_id,))
    conn.commit()
    conn.close()

def extend_due_dates_in_progress(section_id, high_priority_task_id):
    """Extend due dates of tasks in progress, excluding the high-priority task"""
    url = f"{ASANA_API_URL}/sections/{section_id}/tasks"
    response = requests.get(url, headers=HEADERS)
   
    if response.status_code == 200:
        tasks = response.json()['data']
       
        for task in tasks:
            task_id = task['gid']
            if task_id == high_priority_task_id:
                continue
            
            # Get current task details
            task_url = f"{ASANA_API_URL}/tasks/{task_id}"
            task_response = requests.get(task_url, headers=HEADERS)
            
            if task_response.status_code == 200:
                task_details = task_response.json()['data']
                current_due_date = task_details.get('due_on')
                
                if current_due_date:
                    # Extend due date
                    due_date = datetime.strptime(current_due_date, "%Y-%m-%d") + timedelta(days=2)
                    
                    # Prepare payload
                    payload = {"data": {"due_on": due_date.strftime("%Y-%m-%d")}}
                    
                    # Update task due date
                    update_response = requests.put(task_url, json=payload, headers=HEADERS)
                    
                    if update_response.status_code == 200:
                        # Record the extension
                        record_task_extension(high_priority_task_id, task_id, current_due_date)
                        print(f"Extended due date for task {task_id} by 2 days to {due_date.strftime('%Y-%m-%d')}")
    else:
        raise Exception(f"Failed to fetch tasks: {response.status_code}")

def restore_original_due_dates(high_priority_task_id):
    """Restore original due dates for tasks extended by a high-priority task"""
    extended_tasks = get_extended_tasks(high_priority_task_id)
    
    for task_id, original_due_date in extended_tasks:
        url = f"{ASANA_API_URL}/tasks/{task_id}"
        
        # Prepare payload with original due date
        payload = {"data": {"due_on": original_due_date}}
        
        # Update task due date
        response = requests.put(url, json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            print(f"Restored original due date for task {task_id} to {original_due_date}")
    
    # Clear the extensions for this high-priority task
    clear_task_extensions(high_priority_task_id)

def get_task_details(task_id):
    """Fetch details of a specific task"""
    url = f"{ASANA_API_URL}/tasks/{task_id}"
    response = requests.get(url, headers=HEADERS)
   
    if response.status_code == 200:
        return response.json()['data']
    return {}

def get_tasks_in_section(section_id):
    """Fetch tasks in a specific section"""
    url = f"{ASANA_API_URL}/sections/{section_id}/tasks"
    response = requests.get(url, headers=HEADERS)
   
    if response.status_code == 200:
        return response.json()['data']
    return []

# Initialize the database when the module is imported
init_db()