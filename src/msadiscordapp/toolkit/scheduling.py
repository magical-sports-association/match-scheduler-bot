'''
    :module_name: scheduling
    :module_summary: command group for scheduling MSA league matches
    :module_author: CountTails
'''

from __future__ import annotations
import logging
import asyncio
from datetime import datetime, timezone, MAXYEAR
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..model.adts import (
    MatchToSchedule,
    ScheduledMatch,
    MatchToCancel,
    SchedulingEvent,
    SchedulingEventType
)
from ..model.processing import MatchlistQueryRunner
from ..model.config import CommandSpec, GroupSpec
from ..exceptions import MSADiscordAppCommandError
from .. import get_config
from .autocomplete import autocomplete_timezone
from .validators import (
    date_in_near_future,
    date_parts
)
from .msgpaths import CoreContentPaths, SchedulingConfirmationPaths

import discord


__LOGGER__ = logging.getLogger(__name__)
__SPEC__: GroupSpec = get_config().commands["scheduling"]


@discord.app_commands.guilds(get_config().auth.server)
class MatchSchedulingCommandGroup(discord.app_commands.Group):
    '''
        Command group implementing the slash commands to schedule MSA matches
    '''
    __CREATE__: CommandSpec = __SPEC__.group_commands["create_match"]
    __READ__: CommandSpec = __SPEC__.group_commands["get_match"]
    __DELETE__: CommandSpec = __SPEC__.group_commands["delete_match"]

    def __init__(self, bot: discord.ext.commands.Bot) -> None:
        self._bot = bot
        self._scheduler = MatchlistQueryRunner(
            bot.dbpool
        )
        super().__init__(
            name=__SPEC__.group_name,
            description=__SPEC__.group_description,
            guild_only=True
        )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ) -> None:
        '''
            Coroutine to handle check failures or execution issues
            in the logic for match scheduling commands

            Parameters:
                interaction [discord.Interaction]: command usage context
                error: [AppCommandError]: error halting command execution

            Returns:
                None
        '''
        if isinstance(error, discord.app_commands.MissingAnyRole):
            await self._deny_usage(
                interaction=interaction,
                allowlist=[
                    interaction.guild.get_role(r)
                    for r in error.missing_roles
                ],
                edit_response=interaction.response.is_done()
            )
        elif isinstance(error, discord.app_commands.CommandInvokeError) and \
                isinstance(error.original, MSADiscordAppCommandError):
            await self._explain_managed_failure(
                interaction,
                error.original,
                interaction.response.is_done()
            )
        else:
            await self._explain_unexpected_failure(
                interaction,
                error,
                interaction.response.is_done()
            )

    @discord.app_commands.command(
        name=__CREATE__.invoke_with,
        description=__CREATE__.description
    )
    @discord.app_commands.describe(
        **__CREATE__.parameters
    )
    @discord.app_commands.rename(
        **__CREATE__.renames
    )
    @discord.app_commands.autocomplete(
        timezone=autocomplete_timezone
    )
    @discord.app_commands.checks.has_any_role(
        *__CREATE__.allowlist
    )
    async def add_match(
        self,
        interaction: discord.Interaction,
        team_1: discord.Role,
        team_2: discord.Role,
        year: discord.app_commands.Range[int, 1970, MAXYEAR],
        month: discord.app_commands.Range[int, 1, 12],
        day: discord.app_commands.Range[int, 1, 31],
        hour: discord.app_commands.Range[int, 0, 23],
        minute: discord.app_commands.Range[int, 0, 59],
        timezone: str
    ) -> None:
        '''
            Coroutine that implements command logic to schedule a match

            Parameters:
                interaction [discord.Interaction]: command usage context
                team_1 [discord.Role]: first team of match scheduling
                team_2 [discord.Role]: second team of match scheduling
                year [int]: year the match will be scheduled for
                month [int]: month the match will be scheduled for
                day [int]: day the match will be scheduled for
                hour [int]: hour (24hr time) the match will be scheduled for
                minute [int] minute of hour the match will be scheduled for
                timezone [str]: zone identifier for localizing date/time info

            Returns:
                None

            Raises:
                discord.app_commands.MissingAnyRole: if usage not permitted
                discord.app_commands.CommandInvokeError: if match not scheduled
        '''
        await self._acknowledge_command_usage(interaction)
        start_time = self._validate_date_input(
            year,
            month,
            day,
            hour,
            minute,
            timezone
        )
        async with self._scheduler.begin(ScheduledMatch.from_row) as conn:
            scheduled = await self._scheduler.schedule_match(
                conn,
                MatchToSchedule.fixed_order(
                    team_1.id,
                    team_2.id,
                    start_time
                )
            )
            await self._report_new_match_scheduled(interaction, scheduled)
            await self._publish_match_scheduled_event(
                scheduled,
                interaction.guild
            )

    @discord.app_commands.command(
        name=__DELETE__.invoke_with,
        description=__DELETE__.description
    )
    @discord.app_commands.describe(
        **__DELETE__.parameters
    )
    @discord.app_commands.rename(
        **__DELETE__.renames
    )
    @discord.app_commands.checks.has_any_role(
        *__DELETE__.allowlist
    )
    async def delete_match(
        self,
        interaction: discord.Interaction,
        team_1: discord.Role,
        team_2: discord.Role
    ):
        '''
            Coroutine that implements logic to cancel a match

            Parameters:
                interaction [discord.Interaction]: command usage context
                team_1 [discord.Role]: first team in match
                team_2 [discord.Role]: second time in match

            Returns:
                None

            Raises:
                [discord.app_commands.MissingAnyRole]: if not permitted
                [discord.app_commands.CommandInvokeError]: if match not cancelled
        '''
        await self._acknowledge_command_usage(interaction)
        async with self._scheduler.begin(ScheduledMatch.from_row) as conn:
            cancelled = await self._scheduler.cancel_match(
                conn,
                MatchToCancel.fixed_order(
                    team_1.id,
                    team_2.id
                )
            )
            await self._report_match_cancelled(interaction, cancelled)
            await self._publish_match_cancelled_event(
                cancelled,
                interaction.guild
            )

    @discord.app_commands.command(
        name=__READ__.invoke_with,
        description=__READ__.description
    )
    async def show_matches(self, interaction: discord.Interaction):
        await self._acknowledge_command_usage(interaction)
        async with self._scheduler.begin(ScheduledMatch.from_row) as conn:
            upcoming = await self._scheduler.find_upcoming_matches(
                conn,
                round(datetime.now(tz=timezone.utc).timestamp())
            )
            await self._report_upcoming_matches(interaction, upcoming)

    async def _acknowledge_command_usage(
        self,
        interaction: discord.Interaction
    ) -> None:
        '''
            Coroutine to acknowledge a commands usage (after passing checks)

            Warnings:
                This coroutine **responds** to the given interaction
                ANY further communication with the given interaction
                requires using other interaction response methods,
                such as `followup()` or `edit_original_response()`

            Parameters:
                interation [discord.Interaction]: command usage context

            Returns:
                None
        '''
        __LOGGER__.info(
            '/%s invoked by %s',
            interaction.command.qualified_name,
            interaction.user.display_name
        )
        acknowledgement = await self._format_message_template(
            CoreContentPaths.ACK_CMD_USE.value,
            command_used=interaction.command.qualified_name,
            used_by=interaction.user.display_name
        )
        await interaction.response.send_message(
            content=acknowledgement,
            ephemeral=True
        )
        await asyncio.sleep(2)

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
        content_template = await self._bot.messages.fetch_text(msgpath)
        return content_template.format(**kwargs)

    async def _deny_usage(
        self,
        interaction: discord.Interaction,
        allowlist: List[discord.Role],
        edit_response: bool
    ) -> None:
        '''
            Coroutine that alerts the command user that they are not permitted
            to use the invoked command

            Parameters:
                interaction [discord.Interaction]: command usage context
                allowlist [List[discord.Role]]: roles that ARE permitted
                edit_response [bool]: False if fresh interaction, otherwise True

            Returns:
                None
        '''
        __LOGGER__.info(
            '%s attempted to use %s, but does lacks an allowed role',
            interaction.user.display_name,
            interaction.command.qualified_name
        )
        __LOGGER__.debug(
            'Creating embed to notify %s of their insufficient permissions',
            interaction.user.display_name
        )

        async with asyncio.TaskGroup() as group:
            notice_title = group.create_task(
                self._format_message_template(
                    CoreContentPaths.CMD_ISSUE.value
                )
            )
            denied_msg = group.create_task(
                self._format_message_template(
                    CoreContentPaths.INSUFFICIENT_PERMISSIONS.value
                )
            )
            allowed_msg = group.create_task(
                self._format_message_template(
                    CoreContentPaths.ALLOWED_ROLES.value,
                    roleslist='\n'.join([
                        f'- {r.mention}'
                        for r in allowlist
                        if r is not None
                    ])
                )
            )

        forbidden_notice = discord.Embed(
            title=notice_title.result(),
            color=self._bot.AccentColor.ERROR.value
        ).add_field(
            name=denied_msg.result(),
            value=allowed_msg.result(),
            inline=False
        )

        __LOGGER__.debug('Sending forbidden notice as the response')
        if edit_response:
            await interaction.edit_original_response(
                content=None,
                embed=forbidden_notice
            )
        else:
            await interaction.response.send_message(
                embed=forbidden_notice,
                ephemeral=True
            )

    async def _explain_managed_failure(
        self,
        interaction: discord.Interaction,
        exc: MSADiscordAppCommandError,
        edit_response: bool
    ) -> None:
        '''
            Coroutine that sends appropriate messages to anticipated errors

            Parameters:
                interaction [discord.Interaction]: command usage context
                exc [MatchlistOperationFailure]: possibly an anticipated error
                edit_response [bool]: False if fresh interaction, otherwise True

            Returns:
                None
        '''
        __LOGGER__.info(
            'Encountered error %s; handling anticipated error gracefully',
            exc.__class__.__name__
        )
        __LOGGER__.debug(
            'Creating embed to notify %s of the issue encountered',
            interaction.user.display_name
        )

        async with asyncio.TaskGroup() as group:
            notice_title = group.create_task(
                self._format_message_template(
                    CoreContentPaths.CMD_ISSUE.value
                )
            )
            support_link = group.create_task(
                self._format_message_template(
                    CoreContentPaths.SUPPORT_LINK.value
                )
            )

        error_notice = discord.Embed(
            title=notice_title.result(),
            color=self._bot.AccentColor.WARN.value
        ).add_field(
            name=await self._format_message_template(),
            value=f'**{exc.reason}**',
            inline=False
        ).add_field(
            name=await self._format_message_template(),
            value=support_link.result(),
            inline=False
        )

        __LOGGER__.debug('Sending error notice as the response')
        if edit_response:
            await interaction.edit_original_response(
                content=None,
                embed=error_notice
            )
        else:
            await interaction.response.send_message(
                embed=error_notice,
                ephemeral=True
            )
        __LOGGER__.error(
            'Details of error: %s',
            exc.reason
        )

    async def _explain_unexpected_failure(
        self,
        interaction: discord.Interaction,
        exc: Exception,
        edit_response: bool
    ) -> None:
        '''
            Coroutine that attempts to respond to unanticipated errors

            Parameters:
                interaction [discord.Interaction]: command usage context
                exc [Exception]: the unanticipated error
                edit_response [bool]: False if fresh interaction, else True

            Returns:
                None
        '''
        __LOGGER__.info(
            'Encountered error %s; attempting to handle unanticipated error',
            exc.__class__.__name__
        )
        __LOGGER__.debug(
            'Creating embed to notify %s of the error encountered',
            interaction.user.display_name
        )

        async with asyncio.TaskGroup() as group:
            notice_title = group.create_task(
                self._format_message_template(
                    CoreContentPaths.CMD_ERROR.value
                )
            )
            error_msg = group.create_task(
                self._format_message_template(
                    CoreContentPaths.CMD_ERROR_MSG.value
                )
            )
            support_link = group.create_task(
                self._format_message_template(
                    CoreContentPaths.SUPPORT_LINK.value
                )
            )

        error_notice = discord.Embed(
            title=notice_title.result(),
            color=self._bot.AccentColor.ERROR.value
        ).add_field(
            name=error_msg.result(),
            value=await self._format_message_template(),
            inline=False
        ).add_field(
            name=await self._format_message_template(),
            value=support_link.result(),
            inline=False
        )

        __LOGGER__.debug('Sending error notice as the response')
        if edit_response:
            await interaction.edit_original_response(
                content=None,
                embed=error_notice
            )
        else:
            await interaction.response.send_message(
                embed=error_notice,
                ephemeral=True
            )
        __LOGGER__.exception(
            'Details of error: %s',
            str(exc)
        )

    def _validate_date_input(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        timezone: str
    ) -> datetime:
        '''
            Validates date input to schedule a match for the following
                - The date is a valid calendar date
                - The date is at most 1 year into the future
            Exceptions raised will not be handled directly
            Instead, discord.py will wrap them in CommandInvokeError
            and the corresponding command error coroutines will address them

            Parameters:
                year [int]: year being validated
                month [int]: month being validated
                day [int]: day being validated
                hour [int]: hour of day being validated
                minute [int]: minute of hour being validated
                timezone [str]: timezone name being validated

            Returns:
                [datetime]: the validated date/time info as a datetime object

            Raises:
                [InvalidTimeZoneSpecified]: if timezone is not recognizable
                [InvalidStartTimeGiven]: if not a calendar date
                [InvalidStartTimeGiven]: if too far in the future
        '''
        return date_in_near_future(date_parts(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            tzkey=timezone
        ))

    async def _report_new_match_scheduled(
        self,
        interaction: discord.Interaction,
        new_match: ScheduledMatch
    ) -> None:
        '''
            Coroutine to confirm the match was scheduled successfully

            Parameters:
                interaction [discord.Interaction]: command usage context
                new_match [ScheduledMatch]: the newly scheduled match info

            Returns:
                None
        '''
        __LOGGER__.debug('Creating embed to confirm match scheduling')

        async with asyncio.TaskGroup() as group:
            notice_title = group.create_task(
                self._format_message_template(
                    SchedulingConfirmationPaths.MATCH_SCHEDULED_TITLE.value
                )
            )
            team_matchup = group.create_task(
                self._format_message_template(
                    CoreContentPaths.TEAMS_MATCHUP.value,
                    team1=interaction.guild.get_role(new_match.team1).mention,
                    team2=interaction.guild.get_role(new_match.team2).mention
                )
            )
            matchup_date = group.create_task(
                self._format_message_template(
                    CoreContentPaths.MATCHUP_DATE.value,
                    dt=discord.utils.format_dt(new_match.start_at)
                )
            )

        schedule_confirmation = discord.Embed(
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

        __LOGGER__.debug(
            'Replacing original interaction response with confirmation embed'
        )
        await interaction.edit_original_response(
            content=None,
            embed=schedule_confirmation
        )

    async def _report_match_cancelled(
        self,
        interaction: discord.Interaction,
        cancelled_match: ScheduledMatch
    ) -> None:
        '''
            Coroutine to confirm a match was cancelled successfully

            Parameters:
                interaction [discord.Interaction]: command usage context
                cancelled_match [ScheduledMatch]: structured match information

            Returns:
                None
        '''

        __LOGGER__.debug('Creating embed to conficm match cancellation')

        async with asyncio.TaskGroup() as group:
            notice_title = group.create_task(
                self._format_message_template(
                    SchedulingConfirmationPaths.MATCH_CANCELLED_TITLE.value
                )
            )
            team_matchup = group.create_task(
                self._format_message_template(
                    CoreContentPaths.TEAMS_MATCHUP.value,
                    team1=interaction.guild.get_role(
                        cancelled_match.team1).mention,
                    team2=interaction.guild.get_role(
                        cancelled_match.team2).mention
                )
            )
            matchup_date = group.create_task(
                self._format_message_template(
                    CoreContentPaths.MATCHUP_DATE.value,
                    dt=discord.utils.format_dt(cancelled_match.start_at)
                )
            )

        cancel_confirmation = discord.Embed(
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

        __LOGGER__.debug(
            'Replacing original interaction response with confirmation embed'
        )
        await interaction.edit_original_response(
            content=None,
            embed=cancel_confirmation
        )

    async def _report_upcoming_matches(
        self,
        interaction: discord.Interaction,
        matches: List[ScheduledMatch]
    ) -> None:
        '''
            Coroutine that displayed an ordered list of upcoming matches

            Parameters:
                interaction [discord.Interaction]: command usage context
                matches [List[ScheduledMatch]]: list of matches to show

            Returns:
                None
        '''

        __LOGGER__.debug('Creating embed to showcase upcoming matches')

        async with asyncio.TaskGroup() as group:
            notice_title = group.create_task(
                self._format_message_template(
                    SchedulingConfirmationPaths.MATCH_CALENDAR_TITLE.value
                )
            )
            notice_subtitle = group.create_task(
                self._format_message_template(
                    SchedulingConfirmationPaths.MATCH_CALENDAR_SUBTITLE.value
                )
            )
            notice_details = await asyncio.gather(*[
                self._format_message_template(
                    SchedulingConfirmationPaths.MATCH_CALENDAR_SOME.value,
                    team1=interaction.guild.get_role(m.team1).mention,
                    team2=interaction.guild.get_role(m.team2).mention,
                    kickoff_at=discord.utils.format_dt(m.start_at)
                )
                for m in matches]
            ) if matches else await self._format_message_template(
                SchedulingConfirmationPaths.MATCH_CALENDAR_NONE.value
            )

        calendar_notice = discord.Embed(
            title=notice_title.result(),
            description=notice_subtitle.result(),
            color=self._bot.AccentColor.INFO.value
        )

        if isinstance(notice_details, List):
            for line in notice_details:
                calendar_notice.add_field(
                    name=await self._format_message_template(),
                    value=line,
                    inline=False
                )
        else:
            calendar_notice.add_field(
                name=await self._format_message_template(),
                value=notice_details,
                inline=False
            )

        __LOGGER__.debug(
            'Replacing original interaction response with confirmation embed'
        )
        await interaction.edit_original_response(
            content=None,
            embed=calendar_notice
        )

    async def _publish_match_scheduled_event(
        self,
        scheduled_match: ScheduledMatch,
        scheduled_in: discord.Guild,
    ) -> None:
        '''
            Coroutine to publish a match scheduled event for later consuming

            Parameters:
                scheduled_match [ScheduledMatch] details of match scheduled
                scheduled_in [discord.Guild] guild match was scheduled in

            Returns:
                None
        '''
        __LOGGER__.debug(
            'Pushing a scheduled match event to the bot event queue: %s',
            str(scheduled_match)
        )
        await self._bot.publish_scheduling_event(
            SchedulingEvent(
                SchedulingEventType.SCHEDULED,
                scheduled_match,
                scheduled_in
            )
        )

    async def _publish_match_cancelled_event(
        self,
        cancelled_match: ScheduledMatch,
        canelled_in: discord.Guild
    ) -> None:
        '''
            Coroutine to publish a match cancelled event for later consuming

            Parameters:
                cancelled_match [ScheduledMatch] details of match cancelled

            Returns:
                None
        '''
        __LOGGER__.debug(
            'Pushing a cancelled match event to the bot event queue: %s',
            str(cancelled_match)
        )
        await self._bot.publish_scheduling_event(
            SchedulingEvent(
                SchedulingEventType.CANCELLED,
                cancelled_match,
                canelled_in
            )
        )


async def setup(bot: discord.ext.commands.Bot) -> None:
    '''
        Adds the functionality in this module to the provided bot

        Parameters:
            bot [discord.ext.commands.Bot] the bot set up

        Returns:
            None
    '''
    bot.tree.add_command(MatchSchedulingCommandGroup(bot))
