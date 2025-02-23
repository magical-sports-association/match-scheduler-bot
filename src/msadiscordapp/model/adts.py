'''
    :module_name: adts
    :module_summary: hub for abstract data types used in this package
    :module_author: CountTails
'''

from __future__ import annotations
from typing import Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
import logging

import aiosqlite
import discord


__LOGGER__ = logging.getLogger(__name__)


@dataclass
class MatchupDetails:
    '''
        An data class for representing the two teams facing off

        Attributes:
            team_1_id [int]: discord role id of the first team in this matchup
            team_2_id [int]: discord role id of the second team in this Matchup

        Methods:
            cls fixed_order(): constructs instance so id attributes are ordered
    '''
    team_1_id: int
    team_2_id: int

    @classmethod
    def fixed_order(
        cls: MatchupDetails,
        team1: int,
        team2: int
    ) -> MatchupDetails:
        '''
            Alternative constructor that ensures the following:
                - id attributes are ordered (team1 <= team2)
                - order ids are passed does not affect internal structuring

            Parameters:
                team1 [int]: discord role id of team 1
                team2 [int]: discord role id of team 2

            Returns:
                MatchupDetails -> new instance with ensured ordering of ids
        '''
        if team1 > team2:
            __LOGGER__.debug(
                'Received team IDs out of order; swapping to restore order'
            )
            team1, team2 = team2, team1
        return cls(team1, team2)


@dataclass
class MatchToSchedule(MatchupDetails):
    '''
        A data class that represents a request to schedule a match

        Attributes:
            proposed_start [datetime]: proposed starting time of the match

        Methods:
            cls fixed_order(): constructs instance so id attributes are ordered
    '''
    proposed_start: datetime

    @classmethod
    def fixed_order(
        cls: MatchToSchedule,
        team1: int,
        team2: int,
        start_at: datetime
    ) -> MatchToSchedule:
        matchup = MatchupDetails.fixed_order(team1, team2)
        return cls(
            matchup.team_1_id,
            matchup.team_2_id,
            start_at,
        )


@dataclass
class MatchToCancel(MatchupDetails):
    '''
        A data class that represents a request to cancel a match
    '''


@dataclass
class ScheduledMatch:
    '''
        A data class that represents a scheduled match in the matchlist

        Attributes:
            start_at [datetime]: starting date/time of the match
            team1 [int]: first participating team in the matchup
            team2 [int]: second participating team in the matchup

        Methods:
            cls from_row(): destructures an SQL table row into an instance
    '''
    start_at: datetime
    team1: int
    team2: int

    @classmethod
    def from_row(
        cls: ScheduledMatch,
        cursor: aiosqlite.Cursor,
        row: Tuple[int]
    ) -> ScheduledMatch:
        '''
            Destructures a row from an SQL table in the form (int, int, int)
            into an instance of this class.

            Parameters:
                cursor [aiosqlite.Cursor]: pointer to the source of the SQL row
                row [Tuple[int]]: raw data from the SQL row

            Returns:
                ScheduledMatch -> interpreted details of the match row
        '''
        dt, t1, t2 = row
        __LOGGER__.debug(
            'Deconstructed fields from row:\n\tdt=%d\n\tt1=%d\n\tt2=%d',
            dt,
            t1,
            t2
        )
        return cls(
            start_at=datetime.fromtimestamp(dt, timezone.utc),
            team1=t1,
            team2=t2
        )


@dataclass
class CachingRecord:
    '''
        Container for the string contents and an expiration timestamp

        Attributes:
            expires_at [datetime]: timestamp of when the cache becomes invalid
            contents [str]: cached contents of the file

        Methods:
            def is_expired(): predicate determine this cache record's validity
    '''
    expires_at: datetime
    contents: str

    def is_expired(self) -> bool:
        '''
            Checks if this caching record is still valid

            Returns:
                bool -> True if expired, otherwise False
        '''
        now = datetime.now(tz=timezone.utc)
        expired = now > self.expires_at

        __LOGGER__.debug(
            'Validity check:\n\tTime is: %s\n\tRecord valid? %s',
            now.isoformat(),
            'No' if expired else 'Yes'
        )
        return expired


class SchedulingEventType(IntEnum):
    '''
        Enumerates the event scheduling events the result from bot commands

        Variants:
            Scheduled [int]: indicates an event where a match was scheduled
            Cancelled [int]: indicates an event where a match was cancelled
    '''
    SCHEDULED = 0
    CANCELLED = 1


@dataclass
class SchedulingEvent:
    '''
        Represents a event where the matchlist was manipulated

        Attributes:
            kind [SchedulingEventType]: indicates the event type that occurred
            data [ScheduledMatch]: the match details resulting from the event
            guild [discord.Guild]: guild whether event originated from
    '''
    kind: SchedulingEventType
    data: ScheduledMatch
    guild: discord.Guild
