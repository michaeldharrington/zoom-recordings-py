import jwt
import requests
import os
import json
from datetime import datetime, timedelta
from time import time
from urllib.parse import urlencode
from secrets import API_KEY, API_SECRET
DATE_FORMAT = "%Y-%m-%d"
BASE_URL = "https://api.zoom.us/v2/accounts/me/recordings"
today = datetime.now()


def generateToken():
    return jwt.encode(
        {"iss": API_KEY, "exp": time() + 5000}, API_SECRET, algorithm="HS256"
    ).decode("utf-8")


def getHeaders():
    headers = {
        "authorization": "Bearer %s" % generateToken(),
        "content-type": "application/json",
    }
    return headers


def save_meetings(start, end):
    params = {
        "from": start,
        "to": end,
        "page_size": 300,
    }
    encoded_params = urlencode(params)
    url = f"{BASE_URL}?{encoded_params}"
    response = requests.get(url, headers=getHeaders())
    meetings = json.loads(response.text)["meetings"]
    print(" ")
    print(f"Received meetings from {start} to {end}")
    for meeting in meetings:
        dirname = "_".join(
            [meeting["topic"].replace(
                " ", ""), meeting["start_time"], meeting["host_email"]]
        )
        filepath = os.path.abspath(
            ''.join(ch for ch in dirname if ch.isalnum()))
        recordings = meeting["recording_files"]
        print(f"Downloading: {dirname}")
        for recording in recordings:
            if recording["file_type"] != "MP4":
                continue
            save_recording(recording, filepath)


def save_recording(recording, filepath):
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    download_url = recording["download_url"]
    response = requests.get(download_url)
    recording_filename = os.path.join(filepath, "recording.mp4")
    with open(recording_filename, "wb+") as f:
        f.write(response.content)
    json_filename = os.path.join(filepath, "description.json")
    with open(json_filename, "w+") as f:
        f.write(json.dumps(recording))
    print("Downloaded")
    return download_url


total_days_to_go_back = today - timedelta(100)
current_start = today - timedelta(29)
current_end = today
while current_start > total_days_to_go_back:
    save_meetings(current_start, current_end)
    current_start -= timedelta(30)
    current_end -= timedelta(30)
