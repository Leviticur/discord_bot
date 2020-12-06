from discord.ext import commands

from bot import servers
import messages


class CommandsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases=['s', 'stop'])
    async def skip(self, ctx):
        if ctx.guild.id in servers:
            server = servers[ctx.guild.id]
            await messages.skip(ctx)
            if server.following and server.voice.is_playing():
                server.voice.stop()
                server.following = None
            elif server.voice.is_playing():
                server.voice.stop()
            elif server.queue:
                server.queue.pop(0)


    
    @commands.command(aliases=['l'])
    async def leave(self, ctx):
        if ctx.guild.id in servers:
            server = servers[ctx.guild.id]
            if server.voice.is_connected():
                await server.voice.disconnect()


def setup(bot):
    bot.add_cog(CommandsCog(bot))
