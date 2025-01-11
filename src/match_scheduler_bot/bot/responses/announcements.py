'''
    :module_name: announcements
    :module_summary: factories for bot announcements
    :module_author: CountTails
'''

from ...model.rows import ScheduledMatch
from . import AccentColor, Emoji

import discord


class PublicLog:

    @staticmethod
    def match_scheduled(
        interaction: discord.Interaction,
        match: ScheduledMatch
    ) -> discord.Embed:
        return discord.Embed(
            title='{}{}Match Scheduled!{}{}'.format(
                Emoji.CALENDAR,
                Emoji.SEPARATOR,
                Emoji.SEPARATOR,
                Emoji.CHECK
            ),
            color=AccentColor.SUCCESS.value
        ).add_field(
            name='',
            value='- **Teams:** {} vs {}'.format(
                interaction.guild.get_role(match.team_1_id).mention,
                interaction.guild.get_role(match.team_2_id).mention
            ),
            inline=False
        ).add_field(
            name='',
            value='- **Date:** <t:{}:f>'.format(match.start_time),
            inline=False
        )

    @staticmethod
    def match_cancelled(
        interaction: discord.Interaction,
        match: ScheduledMatch
    ) -> discord.Embed:
        return discord.Embed(
            title='{}{}Match Cancelled!{}{}'.format(
                Emoji.CALENDAR,
                Emoji.SEPARATOR,
                Emoji.SEPARATOR,
                Emoji.STOP
            ),
            color=AccentColor.ERROR.value
        ).add_field(
            name='',
            value='- **Teams:** {} vs {}'.format(
                interaction.guild.get_role(match.team_1_id).mention,
                interaction.guild.get_role(match.team_2_id).mention
            ),
            inline=False
        ).add_field(
            name='',
            value='- **Date:** <t:{}:f>'.format(match.start_time),
            inline=False
        )

    @staticmethod
    def match_starting_soon(
        guild: discord.Guild,
        match: ScheduledMatch
    ) -> discord.Embed:
        return discord.Embed(
            title='{}{}Match Incoming!{}{}'.format(
                Emoji.CALENDAR,
                Emoji.SEPARATOR,
                Emoji.SEPARATOR,
                Emoji.STADIUM
            ),
            color=AccentColor.INFO.value
        ).add_field(
            name='**Matchup Information:**',
            value='- {} vs. {}\n- Match begins <t:{}:R>'.format(
                guild.get_role(match.team_1_id).mention,
                guild.get_role(match.team_2_id).mention,
                match.start_time
            ),
            inline=False
        ).add_field(
            name='**How to Watch**:',
            value="- If staff can stream the matchup, tune in to MSA's official [Twitch]({}) or [YouTube]({}) channel to view our official commentary of the matchup.\n\t- If staff cannot stream the matchup, tune in to the players' individual Twitch or YouTube channels to watch their gameplay.".format(
                'https://www.twitch.tv/msaleagueqc',
                'https://www.youtube.com/@MagicalSportsAssociation'
            ),
            inline=False
        ).add_field(
            name='**Team Instructions:**',
            value="- Join your respective voice channel 15 minutes before the match starts.\n- If staff can stream the matchup, begin to stream your gameplay to broadcasters within Discord. (at least one team member must be streaming.)\n\t- If staff cannot stream the matchup, prepare/begin to record and or stream your gameplay on Twitch or YouTube. (at least one team member must be streaming.)\n- Meet in Queue Setup before and after each match for queue sniping\n- Enable Discord streamer mode to hide user joined and user left notifications."
        )
