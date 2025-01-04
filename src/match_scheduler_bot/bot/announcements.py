'''
    :module_name: announcements
    :module_summary: messages the bot posts without direct user intervention
    :module_author: CountTails
'''


import discord

from ..model.config import DiscordBotEmbedResponse


async def make_match_callendar_modified_announcement(
    format: DiscordBotEmbedResponse,
    target: discord.TextChannel,
    home_team: discord.Role,
    away_team: discord.Role,
    start_time: int
) -> None:
    msg = discord.Embed(
        title=format.title,
        color=discord.Color.from_str(format.color)
    ).add_field(
        name="",
        value="**Teams**: {} vs {}".format(
            away_team.mention,
            home_team.mention
        ),
        inline=False
    ).add_field(
        name="",
        value="**Date**: {}".format(
            f'<t:{start_time}:f>'
        )
    )
    await target.send(
        embed=msg
    )
