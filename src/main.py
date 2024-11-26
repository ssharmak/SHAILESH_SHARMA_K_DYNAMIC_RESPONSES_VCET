import time
from src.automation_rules import apply_automation

POLL_INTERVAL = 60  # Poll every 60 seconds

def main():
    while True:
        print("Checking for task updates...")
        try:
            apply_automation()
        except Exception as e:
            print(f"Error during automation: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
