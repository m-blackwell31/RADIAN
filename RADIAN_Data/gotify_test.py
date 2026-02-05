import requests

GOTIFY_URL = "http://10.249.52.19:3000"  # verify port
APP_TOKEN = "AJTcm8GhyGQKvos"

def notify(title, message, priority=5):
    try:
        response = requests.post(
            f"{GOTIFY_URL}/message",
            params={"token": APP_TOKEN},
            json={
                "title": title,
                "message": message,
                "priority": priority
            },
            timeout=5
        )
        response.raise_for_status()
        print("Notification sent!")
    except Exception as e:
        print(f"Notification failed: {e}")

# Test
notify(
    "Pi Notification",
    "Test message from Raspberry Pi to Gotify server."
)
