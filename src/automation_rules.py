from datetime import datetime, timedelta
from src.asana_api import get_tasks, update_task_due_date, get_section_tasks

# Priority to days mapping
PRIORITY_DAYS = {
    "Low": 14,
    "Medium": 7,
    "High": 2
}
# Cache to track the tasks previously in "In Progress" and adjusted tasks
in_progress_cache = set()
adjusted_due_dates = {}  # Cache for adjusted due dates to prevent reverting


def calc_due_date(priority):
    """Calculate default due date based on the priority."""
    return (datetime.now() + timedelta(days=PRIORITY_DAYS[priority])).strftime("%Y-%m-%d")

def hand_task_mvmt_in_progress(moved_task_id):
    """
    Handle tasks when a task is moved to 'In Progress'.
    If the moved task is high-priority, extend the due dates of other tasks in 'In Progress' by 2 days.
    """
    try:
        # Fetch details of the task moved in
        moved_task = get_task_details(moved_task_id)
        if not moved_task:
            raise Exception(f"Unable to fetch task details for task ID {moved_task_id}.")

        # Check if the task is high priority
        priority = None
        if moved_task.get("custom_fields"):
            priority_field = next((field for field in moved_task["custom_fields"] if field.get("name") == "Priority"), None)
            if priority_field:
                priority = priority_field.get("enum_value", {}).get("name")

        # Get all tasks in "In Progress"
        in_progress_tasks = get_section_tasks("In Progress")
        if priority == "High":
            print(f"Task '{moved_task['name']}' (ID: {moved_task_id}) is high priority. Extending due dates of other tasks.")
            for task in in_progress_tasks:
                # Skip the task that was just moved
                if task["gid"] == moved_task_id:
                    continue

                task_id = task["gid"]
                task_name = task["name"]
                current_due_date = task.get("due_on")

                if current_due_date:
                    # Extend the due date by 2 days
                    new_due_date = (datetime.strptime(current_due_date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")

                    # Ensure the new due date is not in the past
                    if datetime.strptime(new_due_date, "%Y-%m-%d") >= datetime.now():
                        update_task_due_date(task_id, new_due_date)
                        adjusted_due_dates[task_id] = new_due_date
                        print(f"Extended due date for task '{task_name}' (ID: {task_id}) to {new_due_date}")
                    else:
                        print(f"Skipped updating task '{task_name}' (ID: {task_id}) as the new due date is in the past.")
                else:
                    print(f"Task '{task_name}' (ID: {task_id}) has no due date to extend.")
        else:
            print(f"Task '{moved_task['name']}' (ID: {moved_task_id}) is not high priority. No action required for other tasks.")

    except Exception as e:
        print(f"Error in handling task movement to 'In Progress': {e}")
def handle_tsk_mvmnt_out_in_progress(moved_task_id):
    """
    Handle tasks when a task is moved out of 'In Progress'.
    Reduce due dates of remaining tasks in 'In Progress' by 2 days, including tasks where the new due date is in the past.
    """
    try:
        # Fetch all tasks in "In Progress"
        in_progress_tasks = get_section_tasks("In Progress")

        # Iterate through all tasks in "In Progress"
        for task in in_progress_tasks:
            # Skip the task that was just moved out
            if task["gid"] == moved_task_id:
                continue

            task_id = task["gid"]
            task_name = task["name"]
            current_due_date = task.get("due_on")

            if current_due_date:
                # Reduce the due date by 2 days
                new_due_date = (datetime.strptime(current_due_date, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d")

                # Update the due date even if it is in the past
                update_task_due_date(task_id, new_due_date)
                adjusted_due_dates[task_id] = new_due_date
                print(f"Reduced due date for task '{task_name}' (ID: {task_id}) to {new_due_date}")
            else:
                print(f"Task '{task_name}' (ID: {task_id}) has no due date to reduce.")

    except Exception as e:
        print(f"Error in handling task movement out of 'In Progress': {e}")

def get_task_details(task_id):
    """
    Fetch details of a specific task using its ID.
    """
    try:
        # Assuming there's a method in `src.asana_api` to fetch task details
        from src.asana_api import fetch_task_details  # Replace with actual API call if necessary
        return fetch_task_details(task_id)
    except Exception as e:
        print(f"Error fetching details for task ID {task_id}: {e}")
        return None

def apply_automation():
    """
    Apply due date automation based on priority and handle 'In Progress' rules.
    """
    global in_progress_cache

    # Fetch current tasks in "In Progress"
    current_in_progress_tasks = {task["gid"] for task in get_section_tasks("In Progress")}

    # Detect tasks moved out of "In Progress"
    moved_out_tasks = in_progress_cache - current_in_progress_tasks
    for moved_task_id in moved_out_tasks:
        print(f"Task moved out of 'In Progress': {moved_task_id}")
        handle_tsk_mvmnt_out_in_progress(moved_task_id)

    # Detect tasks moved into "In Progress"
    moved_in_tasks = current_in_progress_tasks - in_progress_cache
    for moved_task_id in moved_in_tasks:
        print(f"Task moved into 'In Progress': {moved_task_id}")
        hand_task_mvmt_in_progress(moved_task_id)

    # Update the cache with the current tasks in "In Progress"
    in_progress_cache = current_in_progress_tasks

    # Fetch all tasks in the project and apply priority-based due dates
    tasks = get_tasks()
    for task in tasks:
        task_id = task["gid"]
        if task_id in adjusted_due_dates:  # Skip tasks with adjusted due dates
            continue

        priority = None
        if task.get("custom_fields"):
            priority_field = next((field for field in task["custom_fields"] if field.get("name") == "Priority"), None)
            if priority_field:
                priority = priority_field.get("enum_value", {}).get("name")

        # Apply priority-based due dates for tasks not in "In Progress"
        if priority in PRIORITY_DAYS:
            due_date = calc_due_date(priority)
            try:
                update_task_due_date(task_id, due_date)
                
            except Exception as e:
                print(f"Error updating task '{task['name']}' (ID: {task_id}): {e}")

    print("Automation rules applied successfully!")


if __name__ == "__main__":
    apply_automation()