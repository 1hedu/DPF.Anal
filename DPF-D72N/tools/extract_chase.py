import requests
import os
import re

# List of YouTube video URLs
videos = [
    {"title": "S1:E01 - The Hardware", "url": "https://www.youtube.com/watch?v=_2p4xACqiHY"},
    {"title": "S1:E02 - Finding UART on a Photo Frame", "url": "https://www.youtube.com/watch?v=Fu9wnq9UL9E"},
    {"title": "S1:E03 - Sony Left The Memory UNENCRYPTED!", "url": "https://www.youtube.com/watch?v=7nKXnkTp0Ys"},
    {"title": "S1:E04 - Sony Left COMPLETELY Exposed", "url": "https://www.youtube.com/watch?v=eiqYSMQWPVw"},
    {"title": "Series Introduction / Short: Hacking a Photo Frame", "url": "https://www.youtube.com/watch?v=7yAIFJXKTxM"},
]

OUTPUT_DIR = "thumbnails"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_video_id(url):
    return url.split("v=")[1]

def sanitize_filename(name):
    # Replace illegal filename characters
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    return name.strip()

def download_thumbnail(video_id, title):
    safe_title = sanitize_filename(title)

    # Try highest quality first, then fall back
    thumbnail_urls = [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
    ]

    for url in thumbnail_urls:
        response = requests.get(url)
        if response.status_code == 200 and len(response.content) > 1000:
            path = os.path.join(OUTPUT_DIR, f"{safe_title}.jpg")
            with open(path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded thumbnail for: {title}")
            return

    print(f"Failed to download thumbnail for: {title}")

for video in videos:
    video_id = extract_video_id(video["url"])
    download_thumbnail(video_id, video["title"])

print("All thumbnails processed.")
