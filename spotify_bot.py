import os
import asyncio
import datetime

import discord
from discord.ext import commands
from youtube_search import YoutubeSearch
import youtube_dl

from styling import style


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


async def get_member(member_name, ctx):
    members = list()
    for member in ctx.guild.members:
        if ((f"{member.name.lower()}#{member.discriminator}" == member_name) or 
            (member.nick and f"{member.nick.lower()}#{member.discriminator}" == member_name)):

            print("Name/Discriminator Found")
            return member
        elif member.name.lower() == member_name:
            members.append(member)
        elif member.nick and member.nick.lower() == member_name:  
            members.append(member)
    if members:
        if len(members) > 1:
            embed = discord.Embed(
                description = f"**{style('Found multiple users, may need to include a discriminator for a more precise result Name#0000')}**"
            )
            await ctx.send(embed=embed)

        return members[0]


async def get_url(results):
    return f"https://www.youtube.com{results.videos[0]['url_suffix']}"


async def create_voice(ctx):
    """Will return existing guild voice or create and return one if one is not found"""
    if not guilds[ctx.guild.id]['voice']:
        channel = ctx.author.voice.channel
        voice = await channel.connect()
        guilds[ctx.guild.id]['voice'] = voice
    return guilds[ctx.guild.id]['voice']


async def remove_mp3(guild_id):
    for file in os.listdir('./'):
        if file == f"{guild_id}.mp3":
            os.remove(file)


async def download_song(url, guild_id):
    ydl_opt['outtmpl'] = f"{guild_id}.mp3"
    with youtube_dl.YoutubeDL(ydl_opt) as ydl:
        ydl.download([url])


async def play_song(voice, guild_id, timestamp=0):
    voice.play(discord.FFmpegPCMAudio(f"{guild_id}.mp3", before_options=f"-ss {timestamp}"), after=lambda e: asyncio.run_coroutine_threadsafe(timeout(guild_id), client.loop))
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = .30


async def next_song(ctx):
    global guilds

    if not guilds[ctx.guild.id]['queue']:
        print("No songs in queue awaiting next play command")
        await timeout(ctx.guild.id)
    else:
        voice = await create_voice(ctx)
        results = YoutubeSearch(guilds[ctx.guild.id]['queue'][0], max_results=1)
        if results.videos:
            url = await get_url(results)
            await remove_mp3(ctx.guild.id)  
            await download_song(url, ctx.guild.id)

            voice.play(discord.FFmpegPCMAudio(f"{ctx.guild.id}.mp3"), after=lambda e: asyncio.run_coroutine_threadsafe(next_song(ctx), client.loop))
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = .30

            guilds[ctx.guild.id]['lastaction'] = datetime.datetime.utcnow()

            guilds[ctx.guild.id]['queue'].pop(0)


async def timeout(guild_id):
    voice = guilds[guild_id]['voice']
    await asyncio.sleep(10)
    if voice.is_playing():
        return
    else:
        await asyncio.sleep(10)        
        if (datetime.datetime.utcnow() - guilds[guild_id]['lastaction']).total_seconds() > 20:
            await voice.disconnect()


@client.command(aliases=['p'])
async def play(ctx, *args):
    global guilds

    seperator = ' '
    song_name = seperator.join(args)

    if not ctx.guild.id in guilds:
        guilds[ctx.guild.id] = {'member': None, 'voice': None, 'queue': list(), 'lastaction': None}
    
    voice = await create_voice(ctx)

    if guilds[ctx.guild.id]['member']:
        guilds[ctx.guild.id]['member'] = None

        if voice.is_playing():
            voice.stop()

    results = YoutubeSearch(song_name, max_results=1)
    if results.videos:
        url = await get_url(results)
    else:
        print("Could not find song")
        return

    if voice.is_playing():
        guilds[ctx.guild.id]['queue'].append(song_name)
        print(guilds[ctx.guild.id]['queue'])


        embed = discord.Embed(
            description = f"**{style('Queued')} [{results.videos[0]['title']}]({url}) [{ctx.author.mention}]**"
        )
        await ctx.send(embed=embed)

    else:
        guilds[ctx.guild.id]['lastaction'] = datetime.datetime.utcnow()

        embed = discord.Embed(
            title = f"{style('Now Playing')}",
            description = f"**[{style(results.videos[0]['title'])}]({url}) [{ctx.author.mention}]**"
        )
        await ctx.send(embed=embed)

        await remove_mp3(ctx.guild.id)  
        await download_song(url, ctx.guild.id)

        voice.play(discord.FFmpegPCMAudio(f"{ctx.guild.id}.mp3"), after=lambda e: asyncio.run_coroutine_threadsafe(next_song(ctx), client.loop))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = .20



@client.command(aliases=['sw', 'pw'])
async def spotifywith(ctx, *args):
    global guilds

    seperator = ' '
    member_name = seperator.join(args).lower()  

    if not ctx.guild.id in guilds:  
        guilds[ctx.guild.id] = {'member': None, 'voice': None, 'queue': list()}

    member = await get_member(member_name, ctx)
    
    if not member:
        print("Could not find member")
        return

    voice = await create_voice(ctx)

    if voice.is_playing():  # This is optional, I've included so that if someone is playing a song, but member is not  the song stops playing
        voice.stop()

    if guilds[ctx.guild.id]['member']:
        if guilds[ctx.guild.id]['member'] == member:
            print("Already listening to this user")
            return
        else:
            if voice.is_playing():
                print("Stopping song")
                voice.stop()

            guilds[ctx.guild.id]['member'] = None
            guilds[ctx.guild.id]['queue'] = list()


    guilds[ctx.guild.id]['member'] = member
    guilds[ctx.guild.id]['lastaction'] = datetime.datetime.utcnow()

    song_name = None
    for activity in member.activities:
        if activity.name == 'Spotify':
            song_name = f"{activity.artist} {activity.title} Audio"
            song_start = activity.start

    if song_name:
        results = YoutubeSearch(song_name, max_results=1)
        if results.videos:
            url = await get_url(results)

            embed = discord.Embed(
                title = f"**{style(f'Spotify with {member.name}')}**",
                description = f"**{style('Now Playing')} [{style(results.videos[0]['title'])}]({url}) [{ctx.author.mention}]**"
            )
            await ctx.send(embed=embed)

            await remove_mp3(ctx.guild.id)  
            await download_song(url, ctx.guild.id)

            if voice.is_playing():
                voice.stop()

            timestamp = (datetime.datetime.utcnow() - song_start).total_seconds()
            await play_song(voice, ctx.guild.id, timestamp)
        else:  # If member is not playing a song
            await timeout(ctx.guild.id)




@client.command(aliases=['s', 'stop'])
async def skip(ctx):
    if ctx.guild.id not in guilds:  
        return

    emoji = '\U0001f595'
    await ctx.message.add_reaction(emoji)

    if not guilds[ctx.guild.id]['member']:  
        voice = guilds[ctx.guild.id]['voice']
        if voice and voice.is_playing():
            voice.stop()
    elif guilds[ctx.guild.id]['queue']:
       guilds[ctx.guild.id]['queue'].pop(0)
       print("No song currently playing, removing next song from queue")
        
    else:  # If listening with member
        guilds[ctx.guild.id]['member'] = None

        voice = guilds[ctx.guild.id]['voice']
        if voice.is_playing():
            voice.stop()
        await timeout(ctx.guild.id)

@client.command(aliases=['u'])
async def undo(ctx):
    if guilds[ctx.guild.id]['queue']:
        results = YoutubeSearch(guilds[ctx.guild.id]['queue'][-1], max_results=1)
        if results:
            url = await get_url(results)

            embed = discord.Embed(
                description = f"**{style('Removed')} [{style(results.videos[0]['title'])}]({url}) {style('from Queue')} [{ctx.author.mention}]**"
            )
            await ctx.send(embed=embed)

        guilds[ctx.guild.id]['queue'].pop()


@client.command(aliases=['c'])
async def clear(ctx):
    if guilds[ctx.guild.id]['queue']:
        guilds[ctx.guild.id]['queue'] = list()

        embed = discord.Embed(
            description = f"**{style('Cleared Queue')}[{ctx.author.mention}]**"
        )
        await ctx.send(embed=embed)


@client.command(aliases=['l'])
async def leave(ctx):
    voice = guilds[ctx.guild.id]['voice']
    if voice:
        if voice.is_playing():
            voice.stop()
        await voice.disconnect()


@client.event
async def on_member_update(before, after):
    if before.guild.id in guilds and 'member' in guilds[before.guild.id] and guilds[before.guild.id]['member'] and guilds[before.guild.id]['member'].id == before.id:
        before_song_name = None
        for activity in before.activities:
            if activity.name == 'Spotify':
                before_song_name = f"{activity.artist} {activity.title} Audio"

        after_song_name = None
        for activity in after.activities:
            if activity.name == 'Spotify':
                after_song_name = f"{activity.artist} {activity.title} Audio"
                after_song_start = activity.start
        
        if before_song_name and not after_song_name:  
            voice = guilds[before.guild.id]['voice']
            if voice.is_playing():
                voice.stop()
        
        elif after_song_name:  

            results = YoutubeSearch(after_song_name, max_results=1)
            if results.videos:
                guilds[before.guild.id]['lastaction'] = datetime.datetime.utcnow()

                url = await get_url(results)
                await remove_mp3(before.guild.id)  
                await download_song(url, before.guild.id)

                voice = guilds[before.guild.id]['voice']
                if voice.is_playing():
                    voice.stop()

                timestamp = (datetime.datetime.utcnow() - after_song_start).total_seconds()
                
                await play_song(voice, before.guild.id, timestamp)


@client.event
async def on_voice_state_update(member, before, after):
    global guilds

    if member == client.user:
        if before.channel and not after.channel:
            guilds[member.guild.id] = {'member': None, 'voice': None, 'queue': list(), 'lastaction': None}


client.run(os.environ.get('DISCORD_TOKEN'))
