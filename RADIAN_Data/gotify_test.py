import requests

## Configuring these
GOTIFY_URL = "http://10.249.52.19"
APP_TOKEN = "AJTcm8GhyGQKvos"

## Message Details
title = "Pi Notification"
message = "This is a test of Gotify server. Going from the Raspbery Pi to a computer connected to the server. This test occured on Tuesday, October 21st at 9:57am"
priority = 5

## Send to Gotify (Use this to test) --------------

payload = {
	"title": "Test Notification",
	"message": message,
	"priority": 5
}

response = requests.post(
	f"{GOTIFY_URL}/message?token={APP_TOKEN}",
	json = payload,
	headers = {"Content-Type" : "application/json"}\
)

print(response.status_code, response.text)


# --------------------------------------------------


#def notify(title, message, priority = 5):
#	try:
#		response = requests.post(
#			f"{GOTIFY_URL}/message?token={APP_TOKEN}",
#			json = {"title": title, "message": message, "priority": priority},
#			timeout = 5
#		)
#		response.raise_for_status()
#		print("Notification sent!")
#	except Exception as e:
#		print("Notification failed: {e}")

# How it is used:

#from gotify_notify import notify
#notify("Radar Test Complete", "All scanes finished successfully.")


