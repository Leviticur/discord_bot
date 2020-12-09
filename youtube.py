import os
import urllib.parse as urlparse
from googleapiclient.discovery import build

youtube = build('youtube', 'v3', developerKey=os.environ.get('YOUTUBE_TOKEN')) 

def get_title(url):
    
    url_data = urlparse.urlparse(url)
    query = urlparse.parse_qs(url_data.query)
    video_id = query['v'][0]


    request = youtube.videos().list(part='snippet', id=video_id)
    response = request.execute()
    title = response['items'][0]['snippet']['title']
    return title

def get_playlist_videos(url):
    url_data = urlparse.urlparse(url)
    query = urlparse.parse_qs(url_data.query)
    playlist_id = query['list'][0]
    request = youtube.playlistItems().list(part='contentDetails', maxResults=100, playlistId=playlist_id)
    response = request.execute()
    
    videos = []
    for item in response['items']:
        videos.append(dict(video_id=item['contentDetails']['videoId']))
        print(item['contentDetails']['videoId'])

