import os
import youtube_dl


ydl_opt = {
    'format': 'bestaudio/best',
    'outtmpl': '',
    'cookies': 'youtube.com_cookies.txt',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
        }],
    }


async def remove_mp3(guild_id):
    for file in os.listdir('./'):
        if file == str(guild_id) + ".mp3":
            os.remove(file)
            
            
            
async def download_song(url, guild_id):
   ydl_opt['outtmpl']  = str(guild_id) + ".mp3"
   with youtube_dl.YoutubeDL(ydl_opt) as ydl:
    ydl.download([url])
