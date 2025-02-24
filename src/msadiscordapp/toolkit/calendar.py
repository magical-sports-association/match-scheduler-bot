'''
    :module_name: calendar
    :module_summary: Functions for maintaining and viewing MSA match calendar
    :module_author: CountTails
'''

import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import timezone, datetime, timedelta

from ..model.adts import ScheduledMatch, SchedulingEventType
from ..model.processing import MatchlistQueryRunner
from .msgpaths import CoreContentPaths, SchedulingAnnouncementPaths

import discord
from discord.ext import tasks

__LOGGER__ = logging.getLogger(__name__)


class MatchCalendarCog(discord.ext.commands.Cog):
    '''
        Cog containing tasks that assist with maintaining or viewing the
        MSA match calendar
    '''

    def __init__(self, bot: discord.ext.commands.Bot) -> None:
        '''
            Initializes this Cog with the bot it is extending

            Parameters:
                bot [discord.ext.commands.Bot] bot being extended

            Returns:
                None
        '''
        self._bot = bot
        self._matchlist = MatchlistQueryRunner(
            self._bot.dbpool,
            ScheduledMatch.from_sql_row
        )
        self._start_tasks()

    def _start_tasks(self) -> None:
        '''
            Starts the looped tasks associated with this Cog
        '''
        self.announce_incoming_matches.start()
        self.announce_scheduling_event.start()
        self.remove_past_matches_from_schedule.start()

    def cog_unload(self) -> None:
        '''
            Unloads this Cog, primarily by cancelling looped tasks
            associated with this Cog
        '''
        self.announce_incoming_matches.cancel()
        self.announce_scheduling_event.cancel()
        self.remove_past_matches_from_schedule.cancel()

    @tasks.loop(seconds=15)
    async def announce_scheduling_event(self):
        '''
            Attempts to pop from the bot's scheduling events queue

            If successful, pushes an announcement message to the bot's build
            summarizing the scheduling event details

            If unsuccessful, task terminates and tries again on next loop start
        '''
        __LOGGER__.info(
            'Task start: announcing scheduling events in the last minute'
        )
        event = self._bot.get_next_scheduling_event()
        if event is not None:
            __LOGGER__.debug(
                'Got event from queue: %s',
                str(event)
            )
            match event.kind:
                case SchedulingEventType.SCHEDULED:
                    await self._announce_newly_scheduled_match(
                        event.data,
                        event.guild
                    )
                case SchedulingEventType.CANCELLED:
                    await self._announce_newly_cancelled_match(
                        event.data,
                        event.guild
                    )
                case _:
                    await self._ignore_unknown_scheduling_event()
        else:
            __LOGGER__.debug('No scheduling event found; terminating task')

        __LOGGER__.info(
            'Task end: announcing scheduling events in the last minute'
        )

    @tasks.loop(minutes=1)
    async def remove_past_matches_from_schedule(self):
        __LOGGER__.info('Task start: remove past matches from match list')

        purged = await self._matchlist.delete_past_matches(
            round(
                datetime.now(tz=timezone.utc).timestamp()
            )
        )

        __LOGGER__.info(
            'Task end: removed %d matches from match list',
            len(purged)
        )

    @tasks.loop(minutes=1)
    async def announce_incoming_matches(self):
        __LOGGER__.info('Task start: announcing matches starting soon')

        upcoming = await self._matchlist.find_upcoming_match(
            not_before=round(
                datetime.now(
                    tz=timezone.utc
                ).timestamp()
            )
        )

        if server := self._bot.get_guild(self._bot.guild.id):
            embeds = [
                self._match_starting_soon(server, m)
                for m in filter(self._starts_in(minutes=30), upcoming)
            ]
            if embeds:
                await server.get_channel(
                    self._bot.public_log_channel.id
                ).send(
                    content=' '.join(
                        server.get_role(r).mention
                        for r in self._bot.public_log_pings
                    ),
                    embeds=embeds
                )

        __LOGGER__.info(
            'Task end: announced %d matches starting soon',
            len(embeds)
        )

    async def _format_message_template(
        self,
        msgpath: Optional[Path] = None,
        **kwargs: Dict[str, Any]
    ) -> str:
        '''
            Coroutine that retrieves a formattable string from the bot's
            msgcache property and applies the string formatting with the
            given value mapping

            Parameters:
                msgpath [Optional[Path]]: file containing string template
                kwargs [Dict[str, Any]]: values to substitute for placeholders

            Returns:
                [str]: the formatted string

            Raises:
                KeyError: if kwargs does not contain a specified placeholder
                    - This is typically a programming error
        '''
        content_template = await self._bot.msgcache.get_text(msgpath)
        return content_template.format(**kwargs)

    async def _announce_newly_scheduled_match(
        self,
        event: ScheduledMatch,
        guild: discord.Guild
    ) -> None:
        __LOGGER__.debug(
            'Creating embed to publish news of the newly scheduled math'
        )

        async with asyncio.TaskGroup() as group:
            notice_title = group.create_task(
                self._format_message_template(
                    SchedulingAnnouncementPaths.MATCH_SCHEDULED_TITLE.value
                )
            )
            team_matchup = group.create_task(
                self._format_message_template(
                    CoreContentPaths.TEAMS_MATCHUP.value,
                    team1=guild.get_role(event.team_1_id).mention,
                    team2=guild.get_role(event.team_2_id).mention
                )
            )
            matchup_date = group.create_task(
                self._format_message_template(
                    CoreContentPaths.MATCHUP_DATE.value,
                    dt=discord.utils.format_dt(
                        datetime.fromtimestamp(
                            event.start_time,
                            timezone.utc
                        ),
                    )
                )
            )

        notice = discord.Embed(
            title=notice_title.result(),
            color=self._bot.AccentColor.SUCCESS.value
        ).add_field(
            name=await self._format_message_template(),
            value=team_matchup.result(),
            inline=False
        ).add_field(
            name=await self._format_message_template(),
            value=matchup_date.result(),
            inline=False
        )

        public_announce = guild.get_channel(
            self._bot.public_log_channel.id
        )
        public_pings = [
            guild.get_role(r.id)
            for r in self._bot.public_log_pings
        ]
        staff_announce = guild.get_channel(
            self._bot.audit_log_channel.id
        )
        staff_pings = [
            guild.get_role(r.id)
            for r in self._bot.audit_log_pings
        ]

        __LOGGER__.debug(
            'Got public announcement channel: %s',
            str(public_announce)
        )
        __LOGGER__.debug(
            'Public announcement will ping: %s',
            str(public_pings)
        )
        __LOGGER__.debug(
            'Got audit announcement channel: %s',
            str(staff_announce)
        )
        __LOGGER__.debug(
            'Audit announcement will ping: %s',
            str(staff_pings)
        )

        if public_announce:
            await public_announce.send(
                content=' '.join(
                    r.mention for r in public_pings if r is not None
                ),
                embed=notice
            )

        if staff_announce:
            await staff_announce.send(
                content=' '.join(
                    r.mention for r in staff_pings if r is not None
                ),
                embed=notice
            )

    async def _announce_newly_cancelled_match(
        self,
        event: ScheduledMatch,
        guild: discord.Guild
    ) -> None:
        __LOGGER__.debug(
            'Creating embed to publish news of the newly cancelled match'
        )

        async with asyncio.TaskGroup() as group:
            notice_title = group.create_task(
                self._format_message_template(
                    SchedulingAnnouncementPaths.MATCH_CANCELLED_TITLE.value
                )
            )
            team_matchup = group.create_task(
                self._format_message_template(
                    CoreContentPaths.TEAMS_MATCHUP.value,
                    team1=guild.get_role(event.team_1_id).mention,
                    team2=guild.get_role(event.team_2_id).mention
                )
            )
            matchup_date = group.create_task(
                self._format_message_template(
                    CoreContentPaths.MATCHUP_DATE.value,
                    dt=discord.utils.format_dt(
                        datetime.fromtimestamp(
                            event.start_time,
                            timezone.utc
                        ),
                    )
                )
            )

        notice = discord.Embed(
            title=notice_title.result(),
            color=self._bot.AccentColor.SUCCESS.value
        ).add_field(
            name=await self._format_message_template(),
            value=team_matchup.result(),
            inline=False
        ).add_field(
            name=await self._format_message_template(),
            value=matchup_date.result(),
            inline=False
        )

        public_announce = guild.get_channel(
            self._bot.public_log_channel.id
        )
        public_pings = [
            guild.get_role(r.id)
            for r in self._bot.public_log_pings
        ]
        staff_announce = guild.get_channel(
            self._bot.audit_log_channel.id
        )
        staff_pings = [
            guild.get_role(r.id)
            for r in self._bot.audit_log_pings
        ]

        __LOGGER__.debug(
            'Got public announcement channel: %s',
            str(public_announce)
        )
        __LOGGER__.debug(
            'Public announcement will ping: %s',
            str(public_pings)
        )
        __LOGGER__.debug(
            'Got audit announcement channel: %s',
            str(staff_announce)
        )
        __LOGGER__.debug(
            'Audit announcement will ping: %s',
            str(staff_pings)
        )

        if public_announce:
            await public_announce.send(
                content=' '.join(
                    r.mention for r in public_pings if r is not None
                ),
                embed=notice
            )

        if staff_announce:
            await staff_announce.send(
                content=' '.join(
                    r.mention for r in staff_pings if r is not None
                ),
                embed=notice
            )

    def _starts_in(
        self,
        **kwargs: Dict[str, Any]
    ) -> Callable[[ScheduledMatch], bool]:
        '''
            Creates a predicate function to check if a match starts soon

            Parameters:
                kwargs: arguments passed to timedelta constructor

            Returns:
                Callable[[ScheduledMatch], bool]: predicate
        '''
        announce_time_start = timedelta(**kwargs)
        announce_time_end = announce_time_start + \
            timedelta(seconds=60)
        now = round(
            datetime.now(tz=datetime.timezone.utc).timestamp()
        )

        def is_soon(m: ScheduledMatch) -> bool:
            '''
                Predicate that determines if a match is starting soon

                Parameters:
                    m [ScheduledMatch]: the match under test of this predicate

                Returns:
                    [bool]: True is match is starting soon, False otherwise
            '''
            time_diff = m.start_time - now
            before = announce_time_start.total_seconds()
            after = announce_time_end.total_seconds()
            return before <= time_diff <= after

        return is_soon

    async def _match_starting_soon(
        self,
        match: ScheduledMatch,
        guild: discord.Guild
    ) -> discord.Embed:
        '''
            Creates the embed for a match starting soon announcement

            Parameters:
                match [ScheduledMatch]: the match starting soon
                guild [discord.Guild]: guild object for obtaining match info

            Returns:
                [discord.Embed]: announcement content
        '''
        async with asyncio.TaskGroup() as group:
            notice_title = group.create_task(
                self._format_message_template(
                    SchedulingAnnouncementPaths.INCOMING_MATCH_TITLE.value
                )
            )
            notice_matchup_info_head = group.create_task(
                self._format_message_template(
                    SchedulingAnnouncementPaths.INCOMING_MATCH_INFO_HEAD.value
                )
            )
            notice_matchup_info_body = group.create_task(
                self._format_message_template(
                    SchedulingAnnouncementPaths.INCOMING_MATCH_INFO_BODY.value,
                    team1=guild.get_role(match.team_1_id).mention,
                    team2=guild.get_role(match.team_2_id).mention,
                    time_to_start=discord.utils.format_dt(
                        datetime.fromtimestamp(
                            match.start_time,
                            timezone.utc
                        ),
                        style='R'
                    )
                )
            )
            notice_watchinfo_head = group.create_task(
                self._format_message_template(
                    SchedulingAnnouncementPaths.INCOMING_STREAM_INFO_HEAD.value
                )
            )
            notice_watchinfo_body = group.create_task(
                self._format_message_template(
                    SchedulingAnnouncementPaths.INCOMING_STREAM_INFO_BODY.value
                )
            )
            notice_playerinfo_head = group.create_task(
                self._format_message_template(
                    SchedulingAnnouncementPaths.INCOMING_TEAM_INFO_HEAD.value
                )
            )
            notice_playerinfo_body = group.create_task(
                self._format_message_template(
                    SchedulingAnnouncementPaths.INCOMING_TEAM_INFO_BODY.value
                )
            )

        return discord.Embed(
            title=notice_title.result(),
            color=self._bot.AccentColor.INFO.value
        ).add_field(
            name=notice_matchup_info_head.result(),
            value=notice_matchup_info_body.result(),
            inline=False
        ).add_field(
            name=notice_watchinfo_head.result(),
            value=notice_watchinfo_body.result(),
            inline=False
        ).add_field(
            name=notice_playerinfo_head.result(),
            value=notice_playerinfo_body.result(),
            inline=False
        )

    async def _ignore_unknown_scheduling_event(self):
        '''
            Issues a logging statement about an unknown event

            This is mostly here to keep the match case statement neat.
        '''
        __LOGGER__.debug(
            'Recieved unknown event from queue, not announcing anything'
        )


async def setup(bot: discord.ext.commands.Bot) -> None:
    '''
        Adds the functionality in this module to the provided bot

        Parameters:
            bot [discord.ext.commands.Bot] the bot set up

        Returns:
            None
    '''
    await bot.add_cog(
        MatchCalendarCog(bot),
        guild=bot.guild
    )
