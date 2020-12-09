import os
import datetime
import asyncio

import discord
from discord.ext import commands
from youtube_search import YoutubeSearch

from downloads import remove_mp3, download_song

from bot import Server, servers

import youtube
import messages


async def timeout(server):
    await asyncio.sleep(60)
    if (datetime.datetime.utcnow() - server.lastaction).total_seconds() > 60:
        await server.voice.disconnect()


class PlayCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot



    @commands.command(aliases=['p'])
    async def play(self, ctx, *args):
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
            # url_parse(url) if /playlsit playlist(url)
            url = arg
            if '&' in url:
                url = url[:url.find("&")]
            title = youtube.get_title(url)
        else:
            results = YoutubeSearch(arg, max_results=1)
            if results:
                url = "https://youtube.com" + results.videos[0]['url_suffix']
                title = results.videos[0]['title']
            else:
                print("Search terms yielded no results")


        if (ctx.author.voice and server.voice and server.voice.is_connected()
            and len(server.voice.channel.members) == 1):  

            await server.voice.disconnect()  
            server.voice = await ctx.author.voice.channel.connect()

            if server.queue:
                await next_song(ctx, server)


        if server.voice and server.voice.is_playing():  
            queue_message = await messages.queued(ctx, title, url)
            server.queue.append(dict(title=title, url=url, message=queue_message))


        elif ctx.author.voice:  


            if ctx.author.voice.channel == server.voice.channel:
                server.lastaction = datetime.datetime.utcnow() 
                await messages.now_playing(ctx, title, url)
                await remove_mp3(ctx.guild.id)
                await download_song(url, ctx.guild.id)
                await self.play_song(ctx, server)


    async def next_song(self, ctx, server):
        if not server.queue:
            print("No songs in queue")
            await timeout(server)

        elif server.voice.is_connected():  
            now_playing_message = await messages.now_playing(ctx, server.queue[0]['title'], server.queue[0]['url'], send=False)

            try:
                await server.queue[0]['message'].edit(embed=now_playing_message)
            except discord.NotFound:
                print("Queue message has been deleted")

            await remove_mp3(ctx.guild.id)
            await download_song(server.queue[0]['url'], ctx.guild.id)
            await self.play_song(ctx, server)
            server.queue.pop(0)

        else:
            print("Not connected to voice")
        

    async def play_song(self, ctx, server):
        server.voice.play(discord.FFmpegPCMAudio(str(ctx.guild.id) + ".mp3"), after=lambda e: asyncio.run_coroutine_threadsafe(self.next_song(ctx, server), self.bot.loop))
        server.voice.source = discord.PCMVolumeTransformer(server.voice.source)
        server.voice.source.volume = .3
    

def setup(bot):
    bot.add_cog(PlayCog(bot))

