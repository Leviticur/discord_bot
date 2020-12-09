# If going to add functionality move play, play_song, next_song, timeout into file play.py
# Keep client, Server, servers, on_voice_state_update
import os
import datetime
import asyncio

import discord
from discord.ext import commands
from youtube_search import YoutubeSearch

from downloads import remove_mp3, download_song
import youtube
import messages


intents = discord.Intents().all()
client = commands.Bot(command_prefix=['!', ';;', ';'], intents=intents)

servers = dict()


class Server:

    def __init__(self):

        self.voice = None
        self.queue = []
        self.following = None
        self.lastaction = None
        self.lastjoin = None
        self.pw_message = None


@client.event
async def on_voice_state_update(member, before, after):
    if member.guild.id in servers:
        server = servers[member.guild.id]

        if member == client.user:
            if not before.channel and after.channel:
                server.lastjoin = datetime.datetime.utcnow()  # Update isolation timeout when bot joins new voice channel
            elif before.channel and not after.channel:
                print("Bot disconnected")

                await asyncio.sleep(2)
                if not server.voice.is_connected():
                    print("Bot did not reconnect within 2 second clearing queue")
                    server.queue = []
                    server.following = None
                    server.pw_message = None
                    print(server.queue)
        else:
            if server.voice and server.voice.channel:
                print("")
                if not before.channel and after.channel and after.channel == server.voice.channel:
                    server.lastjoin = datetime.datetime.utcnow()  # Update isolation timeout when someone joins bot's voice channel
                elif (before.channel and before.channel == server.voice.channel
                      and len(server.voice.channel.members) == 1):
                  
                    await asyncio.sleep(60)
                    if not server.lastjoin or (datetime.datetime.utcnow() - server.lastjoin).total_seconds() > 60:
                        print("Bot alone, disconnecting")
                        await server.voice.disconnect()
                        await remove_mp3(member.guild.id)
        

client.load_extension('play')
client.load_extension('spotify')
client.load_extension('bot_commands')
client.run(os.environ.get('DISCORD_TOKEN'))
