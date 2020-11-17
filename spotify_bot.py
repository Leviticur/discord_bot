import os
import datetime
import pytz

import discord
from discord.ext import commands
from youtube_search import YoutubeSearch
import youtube_dl

ydl_opt = {
        'format': 'bestaudio/best',
        'outtmpl': '',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
            }],
        }

intents = discord.Intents().all()
client = commands.Bot(command_prefix='!', intents=intents)

members = dict()
guilds = dict()


def remove_mp3(guild_id):
    for file in os.listdir('./'):
        if file == f"{guild_id}.mp3":
            os.remove(file)

def download_song(url, guild_id):
    ydl_opt['outtmpl'] = f"{guild_id}.mp3"
    with youtube_dl.YoutubeDL(ydl_opt) as ydl:
        ydl.download([url])



@client.command()
async def listenwith(ctx, *args):
    global listeneds
    global guilds_listened

    seperator = ' '
    member_name = seperator.join(args).lower()  

    if not ctx.guild.id in guilds:
        guilds[ctx.guild.id] = {'member': None, 'voice': None}

    if not guilds[ctx.guild.id]['member']:

        member = None
        for memb in ctx.guild.members:
            if memb.name and  memb.name.lower() == member_name:
                member = memb
            elif memb.nick and memb.nick.lower() == member_name:  
                member = memb
        
        if not member:  # Could not find member
            return

        channel = ctx.author.voice.channel
        voice = await channel.connect()

        if member.id not in members.keys():
            members[member.id] = [ctx.guild.id]
        else:
            members[member.id].append(ctx.guild.id)

        guilds[ctx.guild.id] = {'member': member.id, 'voice': voice}

        song_name = None
        for activity in member.activities:
            if activity.name == 'Spotify':
                song_name = f"{activity.artist} {activity.title} Audio"
                song_start = activity.start

        if song_name:
            results = YoutubeSearch(song_name, max_results=1)
            if results.videos:
                url = f"https://www.youtube.com{results.videos[0]['url_suffix']}"

                remove_mp3(ctx.guild.id)  # I think order was different before but this makes more sense
                download_song(url, ctx.guild.id)

                timestamp = (datetime.datetime.utcnow() - song_start).total_seconds()

                voice.play(discord.FFmpegPCMAudio(f"{ctx.guild.id}.mp3", before_options=f"-ss {timestamp}"))
                voice.source = discord.PCMVolumeTransformer(voice.source)
                voice.source.volume = .20
    else:
        print("You are already listening to someone")


@client.command()
async def stop(ctx):
    if ctx.guild.id not in guilds.keys():  # Guild has never issued a play command
        return

    elif not guilds[ctx.guild.id]['member']:  # Guild not listening to anyone
        return
    else:
        voice = guilds[ctx.guild.id]['voice']
        if voice.is_playing():
            voice.stop()
        await voice.disconnect()


@client.event
async def on_member_update(before, after):
    if before.id in members.keys():  # a guild is listening with member
        before_song_name = None
        for activity in before.activities:
            if activity.name == 'Spotify':
                before_song_name = f"{activity.artist} {activity.title} Audio"

        after_song_name = None
        for activity in after.activities:
            if activity.name == 'Spotify':
                after_song_name = f"{activity.artist} {activity.title} Audio"

        if not after_song_name:  # not playing music
            return
        elif before_song_name and before_song_name == after_song_name:  # they are playing the same song
            return
        
        else:  # Situtations where music should be played
            results = YoutubeSearch(after_song_name, max_results=1)
            if results.videos:
                url = f"https://www.youtube.com{results.videos[0]['url_suffix']}"
                for guild_id in members[before.id]:
                    remove_mp3(guild_id)  # I think order was different before but this makes more sense
                    download_song(url, guild_id)

                    voice = guilds[guild_id]['voice']
                    if voice.is_playing():
                        voice.stop()

                    voice.play(discord.FFmpegPCMAudio(f"{guild_id}.mp3"))
                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    voice.source.volume = .20




@client.event
async def on_voice_state_update(member, before, after):
    if member == client.user:
        if before.channel and not after.channel:
            members[guilds[member.guild.id]['member']].remove(member.guild.id)
            guilds[member.guild.id] = {'member': None, 'voice': None}


client.run("Nzc3NjMyOTYwNTU0NzI5NTYy.X7GRIQ.l7lXs6iHbFmNnK_-Idy50aLcI-o")

