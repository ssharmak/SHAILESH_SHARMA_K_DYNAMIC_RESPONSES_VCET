

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
git clone <repository_url>
cd <repository_name>
