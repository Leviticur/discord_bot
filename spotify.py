import datetime
import asyncio

import discord
from discord.ext import commands

from bot import Server, servers
from downloads import remove_mp3, download_song
from youtube_search import YoutubeSearch

import messages


async def get_song(activities):
    for activity in activities:
        if activity.name == "Spotify":
            name = "%s %s Audio" % (activity.artist, activity.title)
            start = activity.start
            return (name, start)


async def timeout(server):
    await asyncio.sleep(10)
    if server.voice.is_playing():
        return
    else:
        await asyncio.sleep(110)

        if (datetime.datetime.utcnow() - server.lastaction).total_seconds() > 120:
            print("No recent actions, timing out")
            await server.voice.disconnect()


class SpotifyCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    async def play_song(self, server, guild_id, timestamp):
        server.voice.play(discord.FFmpegPCMAudio(str(guild_id) + ".mp3", before_options="-ss %s" % timestamp),
            after=lambda e: asyncio.run_coroutine_threadsafe(timeout(server), self.bot.loop))
        server.voice.source = discord.PCMVolumeTransformer(server.voice.source)
        server.voice.source.volume = .3


    @commands.command(aliases=['playwith'])
    async def pw(self, ctx, *args):
        global servers
        arg = ' '.join(args).lower()

        if ctx.guild.id in servers:
            server = servers[ctx.guild.id]
        else:
            server = Server()
            servers[ctx.guild.id] = server

        if not ctx.author.voice:
            print("Not in voice channel")
            return


        members = []
        for member in ctx.guild.members:
            if ("%s#%s" % (member.name.lower(), member.discriminator) == arg or (member.nick
                and "%s#%s" % (member.nick.lower(), member.discriminator) == arg)):
                print("Name#Discriminator found")
                members.append(member)
                break
            elif member.name.lower() == arg:
                members.append(member)
            elif member.nick and member.nick.lower() == arg:
                members.append(member)


        if len(members) == 0:
            print("Could not find user")
            return
        elif len(members) > 1:
            await messages.duplicate_members(ctx, member)

        member = members[0]

        if member == server.following:
            return


        server.following = member
        server.lastaction = datetime.datetime.utcnow()
        server.queue = []

        if (server.voice and server.voice.is_connected() and len(server.voice.channel.members) == 1):  
            await server.voice.disconnect()
            server.voice = await ctx.author.voice.channel.connect()

        if not server.voice or (server.voice and not server.voice.is_connected()):  
            server.voice = await ctx.author.voice.channel.connect()

        if server.voice.is_playing():
            server.voice.stop()


        song = await get_song(member.activities)

        if song:

            name = song[0]
            start = song[1]
            results = YoutubeSearch(name, max_results=1)
            if results.videos:
                url = 'https://youtube.com' + results.videos[0]['url_suffix']
                title = results.videos[0]['title']

                await messages.pw(ctx, member, title, url)

                await remove_mp3(ctx.guild.id)
                await download_song(url, ctx.guild.id)
                
                timestamp = (datetime.datetime.utcnow() - start).total_seconds()
                await self.play_song(server, ctx.guild.id, timestamp) 
        else:
            await messages.not_playing_song(ctx, member)


    @commands.Cog.listener()    
    async def on_member_update(self, before, after):
        if before.guild.id in servers:
            server = servers[before.guild.id]
            if before == server.following:
                before_song = await get_song(before.activities)
                after_song = await get_song(after.activities)


                if before_song and not after_song:
                    if server.voice.is_playing():
                        server.voice.stop()
                

                elif after_song:
                    name = after_song[0]
                    start = after_song[1]

                    results = YoutubeSearch(name, max_results=1)
                    if results.videos:
                        server.lastaction = datetime.datetime.utcnow()

                        url = 'https://youtube.com' + results.videos[0]['url_suffix']
                        await remove_mp3(before.guild.id)
                        await download_song(url, before.guild.id)


                        if not server.voice.is_connected():
                            print("Voice not connected")
                            return

                        if server.voice.is_playing():
                            server.voice.stop()


                        timestamp = (datetime.datetime.utcnow() - start).total_seconds()
                        await self.play_song(server, before.guild.id, timestamp) 


def setup(bot):
    bot.add_cog(SpotifyCog(bot))


