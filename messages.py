import discord
from styling import style


async def queued(ctx, title, url):
    embed = discord.Embed(
        description = "**%s [%s](%s) [%s]**" % (style("Queued "), style(title), url, ctx.author.mention)
    )
    await ctx.send(embed=embed)


async def now_playing(ctx, title, url):
    embed = discord.Embed(
        title = style("Now Playing"),
        description = "**[%s](%s) [%s]**" % (style(title), url, ctx.author.mention)
    )
    await ctx.send(embed=embed)

async def skip(ctx):
    emoji = '\U0001f595'
    await ctx.message.add_reaction(emoji)


async def pw(ctx, member, title, url):
    embed = discord.Embed(
        description = "**%s [%s](%s) [%s]**" % (style("Now Playing"), style(title), url, ctx.author.mention)
    )
    await ctx.send(embed=embed)


async def not_playing_song(ctx, member):
    embed = discord.Embed(
        description = "**%s [%s]**" % (style("Waiting for %s to play a song on Spotify" % member.name), ctx.author.mention)
    )
    await ctx.send(embed=embed)


async def duplicate_members(ctx, member):
    embed = discord.Embed(
        description = "**%s [%s]**" % (style("Listening with %s#%s For more precise results include in tag in command (e.g. Name#0000)" % (member.name, member.discriminator)), ctx.author.mention)
    )
    await ctx.send(embed=embed)
