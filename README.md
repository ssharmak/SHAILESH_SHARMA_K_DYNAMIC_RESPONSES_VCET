# Dynamic Due Date Automation with Asana API

This project automates the due date assignment for tasks in an Asana project based on priority levels. Additionally, it updates the due dates of other tasks in the "In Progress" section when a high-priority task is moved to "In Progress".
also if any task is moved out of in-progress section, the remaining task in the "in-progress" section has its date reduced by 2 days.

## Prerequisites

Before running the script, make sure you have the following:

- Python 3.x installed.
- Access to an Asana account and a valid API token.
- A project in Asana with tasks and custom fields (Priority).

To run the file  use following command: python -m src.main

## Setup Instructions

### 1. Clone the Repository

Clone the repository to your local machine.

```bash
git clone <repository_url>
cd <repository_name>

```

## 2. Run the file

    python -m src.main
