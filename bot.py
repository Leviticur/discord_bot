import os
import datetime
import asyncio

import discord
from discord.ext import commands
from youtube_search import YoutubeSearch
import youtube_dl

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


@client.command(aliases=['p'])
async def play(ctx, *args):
    global servers

    arg = ' '.join(args)


    if ctx.guild.id in servers:
        server = servers[ctx.guild.id]
    else:
        server = Server()
        servers[ctx.guild.id] = server

    if server.following:
        server.following = None
        if server.voice.is_playing():
            server.voice.stop()


    if ctx.author.voice and not server.voice or (server.voice and not server.voice.is_connected()):  
        server.voice = await ctx.author.voice.channel.connect()


    if arg.startswith('https://'):  
        url = arg
        title = youtube.get_title(url)
    else:
        results = YoutubeSearch(arg, max_results=1)
        if results:
            url = "https://youtube.com" + results.videos[0]['url_suffix']
            title = results.videos[0]['title']
        else:
            print("Search terms yielded no results")


    if (ctx.author.voice and server.voice and server.voice.is_connected()
        and len(ctx.author.voice.channel.members) == 1):  

        await server.voice.disconnect()  
        server.voice = await ctx.author.voice.channel.connect()

        if server.queue:
            await next_song(ctx, server)


    if server.voice and server.voice.is_playing():  
        server.queue.append(url)
        await messages.queued(ctx, title, url)
        print(server.queue)


    elif ctx.author.voice:  


        if ctx.author.voice.channel == server.voice.channel:
            server.lastaction = datetime.datetime.utcnow() 
            await messages.now_playing(ctx, title, url)
            await remove_mp3(ctx.guild.id)
            await download_song(url, ctx.guild.id)
            await play_song(ctx, server)


async def next_song(ctx, server):
    if not server.queue:
        print("No songs in queue")
        await timeout(server)

    elif server.voice.is_connected():  
        print("Next song called")
        await remove_mp3(ctx.guild.id)
        await download_song(server.queue[0], ctx.guild.id)
        await play_song(ctx, server)
        server.queue.pop(0)

    else:
        print("Not connected to voice")
        

async def play_song(ctx, server):
    server.voice.play(discord.FFmpegPCMAudio(str(ctx.guild.id) + ".mp3"), after=lambda e: asyncio.run_coroutine_threadsafe(next_song(ctx, server), client.loop))
    server.voice.source = discord.PCMVolumeTransformer(server.voice.source)
    server.voice.source.volume = .3
    

async def timeout(server):
    await asyncio.sleep(60)
    if (datetime.datetime.utcnow() - server.lastaction).total_seconds() > 60:
        await server.voice.disconnect()


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
        

client.load_extension('bot_commands')
client.load_extension('spotify')
client.run(os.environ.get('DISCORD_TOKEN'))
