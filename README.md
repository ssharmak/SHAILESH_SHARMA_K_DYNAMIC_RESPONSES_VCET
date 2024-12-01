

---

# Asana Task Management Automation

This project implements a webhook-based solution to dynamically manage task deadlines in Asana. It features priority-based due date updates and real-time synchronization with task changes using Flask, SQLite, and Render.

## Features
1. **Dynamic Due Date Management**: Updates due dates based on task priority.
2. **Real-Time Updates**: Listens for Asana webhook events to adjust deadlines.
3. **Task State Restoration**: Restores original deadlines when tasks move out of the "In Progress" section.
4. **Database Integration**: Tracks and manages task extensions.

---

## Prerequisites

1. Python 3.8+
2. Flask
3. SQLite
4. [Ngrok](https://ngrok.com/) for local webhook testing
5. Render for hosting the application
6. Asana API Access Token

---

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-repo.git
    cd your-repo
    ```

2. Install required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Configure Asana API:
   - Create a `config.py` file and define:
     ```python
     ASANA_API_URL = "https://app.asana.com/api/1.0"
     HEADERS = {
         "Authorization": "Bearer YOUR_ACCESS_TOKEN",
         "Content-Type": "application/json"
     }
     ```

4. Initialize the SQLite database:
    ```bash
    python -c "from asana import init_db; init_db()"
    ```

---

## Usage

### 1. Start the Flask App
Run the app locally for development:
```bash
python app.py
```
The default port is `5000`.

### 2. Expose the App
Use Ngrok to expose your localhost:
```bash
ngrok http 5000
```
Update the `target` URL in `create_webhook.py` with the Ngrok forwarding URL.

### 3. Create the Webhook
Execute the script to register the webhook with Asana:
```bash
python create_webhook.py
```

---

## Code Overview

### Flask Server (`app.py`)
- **Health Check Endpoint**: `GET /` confirms the service is running.
- **Webhook Endpoint**: `POST /webhook` processes Asana events:
  - Handles priority-based due date updates.
  - Adjusts deadlines for tasks in the "In Progress" section.

### Asana Utilities (`asana.py`)
- Manages Asana task interactions.
- Provides helper functions:
  - `update_due_date()`: Sets due dates based on priority.
  - `extend_due_dates_in_progress()`: Adjusts deadlines for tasks.
  - `restore_original_due_dates()`: Reverts extended deadlines.

### Webhook Registration (`create_webhook.py`)
- Registers the webhook with Asana for a specific project.

---

## Deployment

1. Deploy the app to Render:
   - Use `render.yaml` for configuration.
   - Point the webhook `target` to the Render-hosted URL.
   
2. Verify the deployment:
   - Check the webhook status in Asana.
   - Monitor logs for successful event processing.

---

## Example Workflow

1. **New Task Created**:
   - Sets a due date based on priority.
   
2. **Task Moved to 'In Progress'**:
   - Extends deadlines of other tasks by 2 days.

3. **Task Removed from 'In Progress'**:
   - Restores original deadlines.

4. **Priority Changes**:
   - Updates due date dynamically.

---

## Troubleshooting

1. **Webhook Verification Error**:
   - Ensure the Flask app returns the `X-Hook-Secret` header.

2. **Database Errors**:
   - Confirm `task_extensions.db` exists in the `/opt/render/project/.data/` directory.

3. **API Rate Limits**:
   - Monitor Asana API usage and consider implementing rate-limiting.

---

## References

- [Asana API Documentation](https://developers.asana.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Ngrok Documentation](https://ngrok.com/docs)

---

