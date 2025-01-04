'''
    :module_name: announcements
    :module_summary: messages the bot posts without direct user intervention
    :module_author: CountTails
'''


import discord

from ..model.config import DiscordBotEmbedResponseTemplate


async def make_match_callendar_modified_announcement(
    format: DiscordBotEmbedResponseTemplate,
    target: discord.TextChannel,
    home_team: discord.Role,
    away_team: discord.Role,
    start_time: int
) -> None:
    msg = discord.Embed(
        title=format.title,
        description=format.description,
        color=discord.Color.from_str(format.color)
    ).add_field(
        name=format.get_field("match_participants").name,
        value=format.get_field("match_participants").value.format(
            away_team.mention,
            home_team.mention
        ),
        inline=format.get_field("match_participants").inline
    ).add_field(
        name=format.get_field("match_time").name,
        value=format.get_field("match_time").value.format(
            f'<t:{start_time}:f>'
        ),
        inline=format.get_field("match_time").inline
    )
    await target.send(
        embed=msg
    )
