'''
    :module_name: matchlist
    :module_summary: a query runner for manipulating the live matchlist
    :module_author: CountTails
'''

import logging
from dataclasses import asdict
from typing import List

from ..mixins import TransactionalMixin
from ..adts import (
    MatchToSchedule,
    ScheduledMatch,
    MatchToCancel
)
from ...exceptions import (
    MatchToScheduleAlreadyExists,
    MatchToCancelDoesNotExist
)

import aiosqlite

__LOGGER__ = logging.getLogger(__name__)


class MatchlistQueryRunner(TransactionalMixin):
    '''
        Query runner class handling database interactions in the
        matchlist domain area of the application
    '''

    async def create_matchlist_table(self, conn: aiosqlite.Connection) -> None:
        '''
            Coroutine to ensure existence of the required table

            Parameters:
                conn [aiosqlite.Connection]: the connection to execute query on

            Returns:
                None
        '''
        __LOGGER__.debug("Creating matchlist table if it does not exist")
        await conn.execute(self.create_table_stmt)

    async def delete_past_matches(
        self,
        conn: aiosqlite.Connection,
        not_after: int
    ) -> List[ScheduledMatch]:
        '''
            Coroutine for removing matches that start after a given timestamp

            Parameters:
                conn [aiosqlite.Connection]: connection to execute query on
                not_after [int]: unix timestamp used as the cutoff for deletion

            Returns:
                List[ScheduledMatch] -> list of matches removed from table
        '''
        __LOGGER__.debug(
            'Deleting matches starting after %d',
            not_after
        )
        purged_cursor = await conn.execute(
            self.cleanup_past_matches_query,
            (not_after,)
        )
        return await purged_cursor.fetchall()

    async def schedule_match(
        self,
        conn: aiosqlite.Connection,
        match: MatchToSchedule
    ) -> ScheduledMatch:
        '''
            Coroutine that inserts a proposed match to the matchlist table

            Parameters:
                conn [aiosqlite.Connection]: connection to execute query on
                match [MatchToSchedule]: object holding proposed match details

            Returns:
                [ScheduledMatch] -> object holding confirmed match details

            Raises:
                MatchToScheduleAlreadyExists -> if duplicate match is proposed
        '''
        try:
            __LOGGER__.debug(
                'Attempting to schedule match at %d',
                match.proposed_start.isoformat()
            )
            scheduled_cursor = await conn.execute(
                self.schedule_match_query,
                {
                    "proposed_start": round(match.proposed_start.timestamp()),
                    "team_1_id": match.team_1_id,
                    "team_2_id": match.team_2_id
                }
            )
            return await scheduled_cursor.fetchone()
        except aiosqlite.IntegrityError as err:
            __LOGGER__.error(
                'Match cannot be scheduled: %s',
                str(err)
            )
            raise MatchToScheduleAlreadyExists(
                'Match between provided teams is already provided',
                match.team_1_id,
                match.team_2_id
            ) from err

    async def cancel_match(
        self,
        conn: aiosqlite.Connection,
        match: MatchToCancel
    ) -> ScheduledMatch:
        '''
            Coroutine that removes a specific match from the matchlist table

            Parameters:
                conn [aiosqlite.Connection]: connection to execute query on
                match [MatchToCancel]: object holding match cancel request

            Returns:
                ScheduledMatch -> details of match removed from the matchlist

            Raises:
                MatchToCancelDoesNotExist -> if cancelling a match that DNE
        '''
        __LOGGER__.debug(
            'Attempting to cancel match between %d and %d',
            match.team_1_id,
            match.team_2_id
        )
        cancelled_cursor = await conn.execute(
            self.cancel_match_query,
            (match.team_1_id, match.team_2_id)
        )
        cancelled_match = await cancelled_cursor.fetchone()

        if cancelled_match:
            __LOGGER__.info(
                'Specified match was found and removed from matchlist'
            )
            return cancelled_match
        __LOGGER__.error(
            'Specified match was not found'
        )
        raise MatchToCancelDoesNotExist(
            'Match cannot be cancelled because it does not exist',
            match.team_1_id,
            match.team_2_id
        )

    async def find_upcoming_matches(
        self,
        conn: aiosqlite.Connection,
        not_before: int,
        page_size: int = 10,
        page_num: int = 0
    ) -> List[ScheduledMatch]:
        '''
            Coroutine that fetches the upcoming matches in the matchlist

            Parameters:
                conn [aiosqlite.Connection]: connection to execute query on
                not_before [int]: unix timestamp of earliest matches considered
                page_size [int]: limit on result size, defaults to 10
                page_num [int]: result page number, defaults to 0

            Returns:
                List[ScheduledMatch] -> the upcoming matches
        '''
        __LOGGER__.debug(
            'Selecting rows with start time after %d',
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
                :proposed_start,
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
