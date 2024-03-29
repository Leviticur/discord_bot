import discord
from styling import style


async def queued(ctx, title, url, send=True):
    embed = discord.Embed(
        description = "**%s [%s](%s) [%s]**" % (style("Queued "), style(title), url, ctx.author.mention)
    )
    return await ctx.send(embed=embed) if send else embed


async def now_playing(ctx, title, url, send=True):
    embed = discord.Embed(
        title = style("Now Playing"),
        description = "**[%s](%s) [%s]**" % (style(title), url, ctx.author.mention)
    )
    return await ctx.send(embed=embed) if send else embed


async def skip(ctx):
    emoji = '\U0001f595'
    await ctx.message.add_reaction(emoji)


async def undo(ctx):
    emoji = '\U0001f595'
    await ctx.message.add_reaction(emoji)


async def clear(ctx):
    emoji = '\U0001f595'
    await ctx.message.add_reaction(emoji)


async def pw(ctx, member, title, url, send=True):
    embed = discord.Embed(
        description = "**%s [%s](%s) %s [%s] [%s]**" % (style("Now Playing"), style(title), url, style("with"), member.mention, ctx.author.mention)
    )
    return await ctx.send(embed=embed) if send else embed


async def paused(ctx, member, title, url, send=True):
    embed = discord.Embed(
        description = "**[%s] %s [%s](%s) [%s]**" % (member.mention, style("Paused"), style(title), url, ctx.author.mention)
    )
    return await ctx.send(embed=embed) if send else embed


async def waiting_for_user(ctx, member):
    embed = discord.Embed(
        description = "**%s [%s]**" % (style("Waiting for [%s] to play a song on Spotify" % member.mention), ctx.author.mention)
    )
    return await ctx.send(embed=embed)


async def duplicate_members(ctx, member):
    embed = discord.Embed(
        description = "**%s [%s]**" % (style("Search found multiple users, Listening with [%s]. For more precise results include in tag in command (e.g. Name#0000)" % (member.mention)), ctx.author.mention)
    )
    return await ctx.send(embed=embed)
