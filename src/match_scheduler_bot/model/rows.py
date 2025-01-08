'''
    :module_name: rows
    :module_summary: factory functions that convert query results to python objects
    :module_author: CountTails
'''

from __future__ import annotations

import sqlite3

from typing import Tuple
from dataclasses import dataclass


@dataclass
class MatchToSchedule:
    proposed_start_timestamp: int
    team_1_id: int
    team_2_id: int

    @classmethod
    def with_determistic_team_ordering(
        cls,
        start_time: int,
        team1: int,
        team2: int
    ) -> MatchToSchedule:
        if team1 > team2:
            team1, team2 = team2, team1
        return cls(
            start_time,
            team1,
            team2
        )


@dataclass
class ScheduledMatch:
    start_time: int
    team_1_id: int
    team_2_id: int

    @classmethod
    def from_sql_row(
        cls,
        cursor: sqlite3.Cursor,
        row: Tuple[int]
    ) -> ScheduledMatch:
        return cls(
            row[0],
            row[1],
            row[2]
        )


@dataclass
class MatchToCancel:
    team_1_id: int
    team_2_id: int

    @classmethod
    def with_determistic_team_ordering(
        cls,
        team1: int,
        team2: int
    ) -> MatchToCancel:
        if team1 > team2:
            team1, team2 = team2, team1
        return cls(
            team1,
            team2
        )
