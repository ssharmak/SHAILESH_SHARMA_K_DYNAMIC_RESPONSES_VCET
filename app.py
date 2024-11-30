from flask import Flask, request, jsonify, make_response
from asana import (
    update_due_date, 
    extend_due_dates_in_progress, 
    restore_original_due_dates, 
    get_task_details
)
import os

app = Flask(__name__)

PRIORITY_MAPPING = {
    "1208841020836314": "Low",    
    "1208841020836313": "Medium",
    "1208841020836312": "High"    
}

IN_PROGRESS_SECTION_ID = "1208840851929450"

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Asana Webhook Listener is running"}), 200

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # [Rest of your existing webhook handler code remains the same]
    if 'X-Hook-Secret' in request.headers:
        handshake_secret = request.headers['X-Hook-Secret']
        response = make_response("", 200)
        response.headers["X-Hook-Secret"] = handshake_secret
        response.headers["Content-Type"] = "text/plain"
        return response

    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": "Failed to decode JSON object"}), 400

    if data is None:
        return jsonify({"error": "Invalid JSON"}), 400

    if 'events' in data:
        for event in data['events']:
            action = event.get('action')
            task = event.get('resource', {})
            task_id = task.get('gid')
            parent = event.get('parent') or {}
            section_id = parent.get('gid')

            # Handle task added to In Progress section
            if action == 'added' and task.get('resource_type') == 'task' and parent.get('resource_type') == 'section':
                if section_id == IN_PROGRESS_SECTION_ID:
                    task_details = get_task_details(task_id)
                   
                    if 'custom_fields' in task_details:
                        for field in task_details['custom_fields']:
                            if field.get('enum_value') and field['enum_value'].get('gid') in PRIORITY_MAPPING:
                                priority_name = PRIORITY_MAPPING[field['enum_value']['gid']]
                                if priority_name == "High":
                                    try:
                                        extend_due_dates_in_progress(IN_PROGRESS_SECTION_ID, task_id)
                                    except Exception as e:
                                        print(f"Error extending due dates: {str(e)}")

            # Handle task moved out of In Progress section
            if action == 'removed' and task.get('resource_type') == 'task' and section_id == IN_PROGRESS_SECTION_ID:
                task_details = get_task_details(task_id)
                
                if 'custom_fields' in task_details:
                    for field in task_details['custom_fields']:
                        if field.get('enum_value') and field['enum_value'].get('gid') in PRIORITY_MAPPING:
                            priority_name = PRIORITY_MAPPING[field['enum_value']['gid']]
                            if priority_name == "High":
                                try:
                                    restore_original_due_dates(task_id)
                                except Exception as e:
                                    print(f"Error restoring due dates: {str(e)}")

            # Handle initial due date setting for new tasks
            if action == 'added' and task.get('resource_type') == 'task':
                task_details = get_task_details(task_id)
                initial_due_date = task_details.get('due_on')
               
                if task_details.get('name') and not initial_due_date:
                    if 'custom_fields' in task_details:
                        for field in task_details['custom_fields']:
                            if field.get('enum_value') and field['enum_value'].get('gid') in PRIORITY_MAPPING:
                                priority = PRIORITY_MAPPING[field['enum_value']['gid']]
                                update_due_date(task_id, priority)
                                break

            # Handle priority changes
            elif action == 'changed' and task.get('resource_type') == 'task':
                change_field = event.get('change', {}).get('field')
                if change_field == 'custom_fields':
                    new_value = event.get('change', {}).get('new_value', {})
                    if new_value.get('resource_type') == 'custom_field' and new_value.get('enum_value'):
                        enum_value_id = new_value['enum_value']['gid']
                        if enum_value_id in PRIORITY_MAPPING:
                            priority = PRIORITY_MAPPING[enum_value_id]
                            task_details = get_task_details(task_id)
                            initial_due_date = task_details.get('due_on')
                            if not initial_due_date:
                                update_due_date(task_id, priority)

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)