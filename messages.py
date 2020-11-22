import discord
from styling import style


async def send_queue_message(ctx, video_title, url):
    embed = discord.Embed(
        description = f"**{style('Queued')} [{style(video_title)}]({url}) [{ctx.author.mention}]**"
    )
    await ctx.send(embed=embed)


async def send_now_playing_message(ctx, video_title, url):
    embed = discord.Embed(
        title = f"{style('Now Playing')}",
        description = f"**[{style(video_title)}]({url}) [{ctx.author.mention}]**"
    )
    await ctx.send(embed=embed)


async def send_multiple_members_message(ctx, member):
    embed = discord.Embed(
        description = f"**{style('Listening with ')} {style(member.name)}#{member.discriminator}. {style('For more precise results include a tag in command (e.g. Name#0000)')} [{ctx.author.mention}]**"
    )
    await ctx.send(embed=embed)



async def send_playwith_message(ctx, member, video_title, url):
    embed = discord.Embed(
        title = f"**{style('Spotify with')} {style(member.name)}**",
        description = f"**{style('Now Playing')} [{style(video_title)}]({url}) [{ctx.author.mention}]**"
    )
    await ctx.send(embed=embed)


async def send_not_playing_song_message(ctx, member):
    embed = discord.Embed(
        title = f"**{style('Spotify with')} {style(member.name)}**",
        description = f"**{style('Waiting for')} {style(member.name)} {style('to play a song on Spotify')} [{ctx.author.mention}]**"
    )
    await ctx.send(embed=embed)


async def send_undo_message(ctx):
    embed = discord.Embed(
        description = f"**{style('Removed Song from Queue')}[{ctx.author.mention}]**"
    )
    await ctx.send(embed=embed)


async def send_clear_message(ctx):
    embed = discord.Embed(
        description = f"**{style('Cleared Queue')} [{ctx.author.mention}]**"
    )
    await ctx.send(embed=embed)
