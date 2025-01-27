'''
    :module_name: matchlist
    :module_summary: a query runner for manipulating the live matchlist
    :module_author: CountTails
'''

import logging
from dataclasses import asdict
from typing import List, Callable

from ._mixins import TransactionalMixin, RowFactoryFn
from ..pool import AsyncConnectionPool
from ..rows import (
    MatchToSchedule,
    ScheduledMatch,
    MatchToCancel
)
from ...exceptions import (
    DuplicatedMatchDetected,
    CancellingNonexistantMatch
)

import aiosqlite

__LOGGER__ = logging.getLogger(__name__)


class MatchlistQueryRunner(TransactionalMixin):

    '''
        Query runner class handling database interactions in the
        matchlist domain area of the application
    '''

    async def create_matchlist_table(self) -> None:
        '''
            Coroutine to ensure existant of the required table

            Parameters:
                None

            Returns:
                None
        '''
        async with self as conn:
            __LOGGER__.info('Creating matchlist table if it does not exists')
            await conn.execute(self.create_table_stmt)

    async def delete_past_matches(
        self,
        not_after: int
    ) -> List[ScheduledMatch]:
        '''
            Coroutine that removes matches that start before a given timestamp

            Parameters:
                not_after [int]: unix timestamp used as the cutoff for deletion

            Returns
                [List[ScheduledMatch]]: list of matches removed from the table
        '''
        async with self as conn:
            __LOGGER__.info(
                'Deleting rows with timestamp before %d',
                not_after
            )
            purged_cursor = await conn.execute(
                self.cleanup_past_matches_query,
                (not_after,)
            )
            return await purged_cursor.fetchall()

    async def schedule_match(self, match: MatchToSchedule) -> ScheduledMatch:
        '''
            Coroutine that inserts a proposed match to the matchlist table

            Parameters:
                match [MatchToSchedule] object holding proposed match details

            Returns:
                [ScheduledMatch] object holding confirmed match details

            Raises:
                DuplicatedMatchDetected: if proposed match is a duplicate match
        '''
        try:
            async with self as conn:
                __LOGGER__.info(
                    'Attempting to schedule match at %d',
                    match.proposed_start_timestamp
                )
                scheduled_cursor = await conn.execute(
                    self.schedule_match_query,
                    asdict(match)
                )
                return await scheduled_cursor.fetchone()
        except aiosqlite.IntegrityError as err:
            __LOGGER__.error(
                'Match cannot be scheduled: %s',
                str(err)
            )
            raise DuplicatedMatchDetected(
                'Match between provided teams is already scheduled'
            ) from err

    async def cancel_match(self, match: MatchToCancel) -> ScheduledMatch:
        '''
            Coroutine that removes a specific match from the matchlist table

            Parameters:
                match [MatchToCancel] object holding match cancellation request

            Returns:
                [ScheduledMatch] object holding cancelled match details

            Raises:
                [CancellingNonexistantMatch] if cancelling a match that DNE
        '''
        async with self as conn:
            __LOGGER__.info(
                'Attempting the cancel a match between %d and %d',
                match.team_1_id,
                match.team_2_id
            )
            cancelled_cursor = await conn.execute(
                self.cancel_match_query,
                (match.team_1_id, match.team_2_id)
            )
            cancelled_match = cancelled_cursor.fetchone()

        if cancelled_match:
            __LOGGER__.info(
                'Specified match was found and removed from matchlist'
            )
            return cancelled_match
        __LOGGER__.error(
            'Specified match was not found'
        )
        raise CancellingNonexistantMatch(
            'Match cannot be cancelled because it does not exist'
        )

    async def find_upcoming_match(
        self,
        not_before: int,
        page_size: int = 10,
        page_num: int = 0
    ) -> List[ScheduledMatch]:
        '''
            Coroutine that fetches the upcoming matches in the matchlist

            Parameters:
                not_before [int]: unix timestamp of earliest match considered
                page_size [int]: result size limiter. Defaults to 10
                page_num [int]: result page count. Defaults to 0
            Returns:
                [List[ScheduledMatch]] upcoming match list sorted by start time
        '''
        async with self as conn:
            __LOGGER__.info(
                'Selecting rows with timestampt after %d',
                not_before
            )
            match_cursor = await conn.execute(
                self.upcoming_matches_query,
                (not_before, page_size, page_num * page_size)
            )
            return await match_cursor.fetchall()

    @property
    def create_table_stmt(self) -> str:
        __LOGGER__.debug('Read SQL code that creates matchlist table')
        return '''
            CREATE TABLE IF NOT EXISTS matches (
                start_time BIG INT,
                team_1_id BIG INT,
                team_2_id BIG INT,
                PRIMARY KEY (team_1_id, team_2_id)
            )
        '''

    @property
    def upcoming_matches_query(self) -> str:
        __LOGGER__.debug('Read SQL code that selects upcoming match rows')
        return '''
            SELECT * FROM matches
            WHERE start_time > ?
            ORDER BY start_time ASC
            LIMIT ?
            OFFSET ?
        '''

    @property
    def cancel_match_query(self) -> str:
        __LOGGER__.debug('Read SQL code that removes a specific match row')
        return '''
            DELETE FROM matches
            WHERE team_1_id = ? AND team_2_id = ?
            RETURNING *;
        '''

    @property
    def schedule_match_query(self) -> str:
        __LOGGER__.debug('Read SQL code that adds a row to the matchlist')
        return '''
            INSERT INTO matches VALUES (
                :proposed_start_timestamp,
                :team_1_id,
                :team_2_id
            )
            RETURNING *;
        '''

    @property
    def cleanup_past_matches_query(self) -> str:
        __LOGGER__.debug('Read SQL code that removes match rows from the past')
        return '''
            DELETE FROM matches
            WHERE start_time < ?
            RETURNING *;
        '''
