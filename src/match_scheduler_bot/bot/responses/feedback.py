'''
    :module_name: feedback
    :module_summary: factories for feedback messages given to the bot
    :module_author: CountTails
'''

from typing import List

from ...model.rows import ScheduledMatch
from ...exceptions import (
    MatchSchedulerBotException
)
from . import AccentColor, Emoji

import discord


class AcknowledgeCommandUsage:

    @staticmethod
    def create_match_used(
        used_by: discord.Member,
        friend: discord.Role,
        foe: discord.Role
    ) -> str:
        return '**Loading...'

    @staticmethod
    def delete_match_used(
        used_by: discord.Member,
        friend: discord.Role,
        foe: discord.Role
    ) -> str:
        return '**Loading...*'

    @staticmethod
    def get_match_used(used_by: discord.Member) -> str:
        return '**Loading...**'


class CommandSucceeded:

    @staticmethod
    def created_match(
            interaction: discord.Interaction,
            match: ScheduledMatch
    ) -> discord.Embed:
        return discord.Embed(
            title='Your Match Has Been Scheduled!',
            color=AccentColor.SUCCESS.value
        ).add_field(
            name='',
            value='- **Teams:** __{}__ vs. __{}__'.format(
                interaction.guild.get_role(match.team_1_id).name,
                interaction.guild.get_role(match.team_2_id).name
            ),
            inline=False
        ).add_field(
            name='',
            value='- **Date:** <t:{}:f>'.format(match.start_time),
            inline=False
        )

    @staticmethod
    def deleted_match(
        interaction: discord.Interaction,
        match: ScheduledMatch
    ) -> discord.Embed:
        return discord.Embed(
            title='Your Match Has Been Cancelled!',
            color=AccentColor.SUCCESS.value
        ).add_field(
            name='',
            value='- **Teams:** __{}__ vs. __{}__'.format(
                interaction.guild.get_role(match.team_1_id).name,
                interaction.guild.get_role(match.team_2_id).name
            ),
            inline=False
        ).add_field(
            name='',
            value='- **Date:** <t:{}:f>'.format(match.start_time),
            inline=False
        )

    @staticmethod
    def got_match(
        interaction: discord.Interaction,
        matches: List[ScheduledMatch]
    ):
        msg = discord.Embed(
            title='{}{}Match Calendar{}{}'.format(
                Emoji.CALENDAR,
                Emoji.SEPARATOR,
                Emoji.SEPARATOR,
                Emoji.CALENDAR
            ),
            description='Below is a list of the matches currently scheduled:',
            color=AccentColor.INFO.value
        )
        has_matches = False
        for m in matches:
            msg.add_field(
                name='',
                value='- {} vs. {} | <t:{}:f>'.format(
                    interaction.guild.get_role(m.team_1_id).mention,
                    interaction.guild.get_role(m.team_2_id).mention,
                    m.start_time
                ),
                inline=False
            )
            has_matches = True
        else:
            if not has_matches:
                msg.add_field(
                    name='',
                    value='-# There are no matches scheduled at this time.'
                )
        return msg


class CommandFailed:

    @staticmethod
    def managed_failure(
        error: MatchSchedulerBotException
    ) -> discord.Embed:
        return discord.Embed(
            title='{}{}Issue Encountered!{}{}'.format(
                Emoji.WARN,
                Emoji.SEPARATOR,
                Emoji.SEPARATOR,
                Emoji.WARN
            ),
            color=AccentColor.WARN.value
        ).add_field(
            name='',
            value=f'**{error.what}.**',
            inline=False
        ).add_field(
            name='',
            value='If this error continues to occur, please report it to our staff using our ticket system, accessible [here.]({})'.format(
                'https://discord.com/channels/1250641659780141056/1251692245028045021'
            ),
            inline=False
        )

    @staticmethod
    def forbidden(
        interaction: discord.Interaction,
        allowed: List[discord.Role]
    ) -> discord.Embed:
        return discord.Embed(
            title='{}{}Issue Encountered!{}{}'.format(
                Emoji.WARN,
                Emoji.SEPARATOR,
                Emoji.SEPARATOR,
                Emoji.WARN
            ),
            color=AccentColor.ERROR.value
        ).add_field(
            name='**It appears that you do not possess the necessary permissions to execute this command.**',
            value='',
            inline=False
        ).add_field(
            value='To proceed, you must hold at least one of the following roles: {}.'.format(
                ', '.join(r.mention for r in allowed)
            ),
            name='',
            inline=False
        )

    @staticmethod
    def unexpected_failure() -> discord.Embed:
        return discord.Embed(
            title='{}{}Error Encounted!{}{}'.format(
                Emoji.WARN,
                Emoji.SEPARATOR,
                Emoji.SEPARATOR,
                Emoji.WARN
            ),
            color=AccentColor.ERROR.value
        ).add_field(
            name='**An unexpected error has been encountered.**',
            value='',
            inline=False
        ).add_field(
            name='',
            value='If this error continues to occur, please report it to our staff using our ticket system, accessible [here.]({})'.format(
                'https://discord.com/channels/1250641659780141056/1251692245028045021'
            ),
            inline=False
        )
