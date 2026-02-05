import requests

GOTIFY_URL = "http://172.20.10.13"  # Using Mitch's hotspot, this is the URL to use
APP_TOKEN = "AJTcm8GhyGQKvos" #Stays the same, have Mitch use the CLIENT token

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
    "This is a current test of the communication bewtween the Gotify server and flutter RADIAN app. This test occured at 9:45am on Thursday Feb. 5, 2026."
)
