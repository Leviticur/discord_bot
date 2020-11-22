import os
import asyncio
import datetime

import discord
from discord.ext import commands
from youtube_search import YoutubeSearch
import youtube_dl

import youtube
import messages


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
client = commands.Bot(command_prefix=['!', ';'], intents=intents)

guilds = dict()


async def initialize_guild(guild_id):
    """Initializes default value for guild in guilds"""
    global guilds

    guilds[guild_id] = dict()
    guilds[guild_id]['member'] = None
    guilds[guild_id]['voice'] = None
    guilds[guild_id]['queue'] = list()
    guilds[guild_id]['lastaction'] = None


async def get_voice(ctx):
    """Will return existing guild voice or create and return one if one is not found"""
    if not guilds[ctx.guild.id]['voice']:
        channel = ctx.author.voice.channel
        voice = await channel.connect()
        guilds[ctx.guild.id]['voice'] = voice
    return guilds[ctx.guild.id]['voice']


async def get_url(results):
    return f"https://www.youtube.com{results.videos[0]['url_suffix']}"


async def remove_mp3(guild_id):
    for file in os.listdir('./'):
        if file == f"{guild_id}.mp3":
            os.remove(file)


async def download_song(url, guild_id):
    ydl_opt['outtmpl'] = f"{guild_id}.mp3"
    with youtube_dl.YoutubeDL(ydl_opt) as ydl:
        ydl.download([url])


async def play_song(ctx, voice):
    voice.play(discord.FFmpegPCMAudio(f"{ctx.guild.id}.mp3"), after=lambda e: asyncio.run_coroutine_threadsafe(next_song(ctx), client.loop))
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = .20


@client.command(aliases=['p'])
async def play(ctx, *args):
    global guilds

    seperator = ' '
    arg = seperator.join(args)

    if not ctx.guild.id in guilds:
        await initialize_guild(ctx.guild.id)

    voice = await get_voice(ctx)

    if guilds[ctx.guild.id]['member']:
        await stop_playwith(voice, ctx.guild.id)

    if arg.startswith(('https://www.youtube.com')):
        url = arg
        video_title = youtube.get_title(url)
    else:
        results = YoutubeSearch(arg, max_results=1)
        if results.videos:
            url = await get_url(results)
            video_title = results.videos[0]['title']
        else:
            return

    if voice.is_playing():
        guilds[ctx.guild.id]['queue'].append(url)
        await messages.send_queue_message(ctx, video_title, url)
    else:
        guilds[ctx.guild.id]['lastaction'] = datetime.datetime.utcnow()
        await messages.send_now_playing_message(ctx, video_title, url)
        await remove_mp3(ctx.guild.id)  
        await download_song(url, ctx.guild.id)
        await play_song(ctx, voice)


async def next_song(ctx):
    global guilds

    if not guilds[ctx.guild.id]['queue']:
        print("No songs in queue awaiting next play command")
        await timeout(ctx.guild.id)
    else:
        voice = await get_voice(ctx)
        await remove_mp3(ctx.guild.id)  
        await download_song(guilds[ctx.guild.id]['queue'][0], ctx.guild.id)

        voice.play(discord.FFmpegPCMAudio(f"{ctx.guild.id}.mp3"), after=lambda e: asyncio.run_coroutine_threadsafe(next_song(ctx), client.loop))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = .30

        guilds[ctx.guild.id]['lastaction'] = datetime.datetime.utcnow()

        guilds[ctx.guild.id]['queue'].pop(0)


async def get_member(name, ctx):
    members = list()
    for member in ctx.guild.members:
        if ((f"{member.name.lower()}#{member.discriminator}" == name) or (member.nick and f"{member.nick.lower()}#{member.discriminator}" == name)):
            print("Name/Discriminator Found")
            return member
        elif member.name.lower() == name:
            members.append(member)
        elif member.nick and member.nick.lower() == name:  
            members.append(member)
                
    if members and len(members) > 1:
        await messages.send_multiple_members_message(ctx, members[0])

    return members[0]


async def get_spotify_song(activities):
    for activity in activities:
        if activity.name == 'Spotify':
            name = f"{activity.artist} {activity.title} Audio"
            start = activity.start
            return {'name': name, 'start': start}


async def play_spotify_song(voice, guild_id, timestamp=0):
    voice.play(discord.FFmpegPCMAudio(f"{guild_id}.mp3", before_options=f"-ss {timestamp}"), after=lambda e: asyncio.run_coroutine_threadsafe(timeout(guild_id), client.loop))
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = .30


@client.command(aliases=['sw', 'pw'])
async def playwith(ctx, *args):
    global guilds

    seperator = ' '
    arg = seperator.join(args).lower()  

    if not ctx.guild.id in guilds:  
        await initialize_guild(ctx.guild.id)

    member = await get_member(arg, ctx)
    
    if not member:
        print("Could not find member")
        return

    voice = await get_voice(ctx)


    if guilds[ctx.guild.id]['member']:
        if guilds[ctx.guild.id]['member'] == member:
            return
        else:
            guilds[ctx.guild.id]['member'] = None
            guilds[ctx.guild.id]['queue'] = list()

    if voice.is_playing():  
        voice.stop()

    guilds[ctx.guild.id]['member'] = member
    guilds[ctx.guild.id]['lastaction'] = datetime.datetime.utcnow()

    song = await get_spotify_song(member.activities)

    if song:
        song_name = song['name']
        song_start = song['start']
        results = YoutubeSearch(song_name, max_results=1)
        if results.videos:
            url = await get_url(results)
            video_title = results.videos[0]['title']

            await messages.send_playwith_message(ctx, member, video_title, url)

            await remove_mp3(ctx.guild.id)  
            await download_song(url, ctx.guild.id)

            if voice.is_playing():
                voice.stop()

            timestamp = (datetime.datetime.utcnow() - song_start).total_seconds()
            await play_spotify_song(voice, ctx.guild.id, timestamp)
    else:  
        print("User is not playing Spotify")
        await messages.send_not_playing_song_message(ctx, member)
        await timeout(ctx.guild.id)


@client.event
async def on_member_update(before, after):
    if before.guild.id in guilds and 'member' in guilds[before.guild.id] and guilds[before.guild.id]['member'] and guilds[before.guild.id]['member'].id == before.id:
        before_song = await get_spotify_song(before.activities)
        after_song = await get_spotify_song(after.activities)

        
        if before_song and not after_song:  
            voice = guilds[before.guild.id]['voice']
            if voice.is_playing():
                voice.stop()
        
        elif after_song:  
            after_song_name = after_song['name']
            after_song_start = after_song['start']

            results = YoutubeSearch(after_song_name, max_results=1)
            if results.videos:
                guilds[before.guild.id]['lastaction'] = datetime.datetime.utcnow()

                url = await get_url(results)
                await remove_mp3(before.guild.id)  
                await download_song(url, before.guild.id)

                voice = guilds[before.guild.id]['voice']
                if voice.is_playing():
                    voice.stop()

                timestamp = (datetime.datetime.utcnow() - after_song_start).total_seconds()  # Will produce correct timestamp after pauses, not sure why
                
                await play_spotify_song(voice, before.guild.id, timestamp)



@client.event
async def on_voice_state_update(member, before, after):
    global guilds

    if member == client.user:
        if before.channel and not after.channel:
            await initialize_guild(member.guild.id)
            await remove_mp3(member.guild.id)


async def timeout(guild_id):
    voice = guilds[guild_id]['voice']
    await asyncio.sleep(10)
    if voice.is_playing():
        return
    else:
        await asyncio.sleep(50)        
        if (datetime.datetime.utcnow() - guilds[guild_id]['lastaction']).total_seconds() > 60:
            await voice.disconnect()


async def stop_playwith(voice, guild_id):
    guilds[guild_id]['member'] = None
    if voice.is_playing():
        voice.stop()
    

@client.command(aliases=['s', 'stop'])
async def skip(ctx):
    if ctx.guild.id not in guilds:  
        return

    emoji = '\U0001f595'
    await ctx.message.add_reaction(emoji)

    voice = guilds[ctx.guild.id]['voice']

    if guilds[ctx.guild.id]['member']:
        await stop_playwith(voice, ctx.guild.id)
        await timeout(ctx.guild.id)
    elif voice and voice.is_playing():
        voice.stop()
    elif guilds[ctx.guild.id]['queue']:
       guilds[ctx.guild.id]['queue'].pop(0)
        

@client.command(aliases=['u'])
async def undo(ctx):
    if guilds[ctx.guild.id]['queue']:
        guilds[ctx.guild.id]['queue'].pop()
        await messages.send_undo_message(ctx)

    
@client.command(aliases=['c'])
async def clear(ctx):
    if guilds[ctx.guild.id]['queue']:
        guilds[ctx.guild.id]['queue'] = list()
        await messages.send_clear_message(ctx)


@client.command(aliases=['l'])
async def leave(ctx):
    voice = guilds[ctx.guild.id]['voice']
    if voice:
        if voice.is_playing():
            voice.stop()
        await voice.disconnect()


client.run(os.environ.get('DISCORD_TOKEN'))
