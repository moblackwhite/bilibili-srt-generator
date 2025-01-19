from datetime import datetime
from selenium import webdriver
import re
from database_manager import VideoDatabase
import requests


def extract_video_title(html_source):
    # Pattern to match the video title - looking for data-title attribute
    pattern = r'data-title="([^"]+)"'

    # Find the match
    match = re.search(pattern, html_source)

    return match.group(1)

def extract_video_duration(html_source):
    # Pattern to match the video duration - looking for data-duration attribute
    pattern = r'"timelength":(\d+)'

    # Find the match
    match = re.search(pattern, html_source)

    duration_ms = int(match.group(1))

    return duration_ms // 1000

vd = VideoDatabase()

records = vd.get_all_no_audio_videos()


driver = webdriver.Chrome()
try:
    for record in records:
        BV = record.BV
        audio_save_path = f'data/audio/{BV}.m4s'

        video_url = f'https://www.bilibili.com/video/{BV}'
        driver.get(video_url)
        html_source = driver.page_source

        matches = re.findall(r'https:[^\s"]+\-1\-30280\.m4s\?[^\s"]+', html_source)

        audio_download_url = matches[0]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Referer': video_url
        }

        # Download the audio file with headers
        response = requests.get(audio_download_url, headers=headers)
        
        # Save the audio file
        with open(audio_save_path, 'wb') as file:
            file.write(response.content)
        
        # UPDATE THE RECORD
        record.title = extract_video_title(html_source)
        record.download_date = datetime.now()
        record.duration = extract_video_duration(html_source)
        record.audio_path = audio_save_path
        record.status = 1

        vd.update_video(record)
finally:
    driver.quit()