import os
import urllib.parse as urlparse
from googleapiclient.discovery import build

youtube = build('youtube', 'v3', developerKey=os.environ.get('YOUTUBE_TOKEN')) 

def get_title(url):
    
    url_data = urlparse.urlparse(url)
    query = urlparse.parse_qs(url_data.query)
    video_id = query["v"][0]


    request = youtube.videos().list(part='snippet', id=video_id)
    response = request.execute()
    title = response['items'][0]['snippet']['title']
    return title

