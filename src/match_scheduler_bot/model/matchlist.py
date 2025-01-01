"""
    :module_name: matchlist
    :module_summary: a repository for schedule matches
    :module_author: CountTails
"""

import pydantic
from typing_extensions import Annotated

import time
import sqlite3


class ScheduledMatch(pydantic.BaseModel):
    scheduled_timestamp: Annotated[int, pydantic.Field(gt=0)]
    away_team: int
    home_team: int
    scheduled_at: Annotated[int, pydantic.Field(gt=0)]
    scheduled_by: int


class MatchListRepository:
    def __init__(self, dbpath: str):
        self._conn = sqlite3.connect(dbpath)
        self._create_matchlist_table()

    def find_matches(self) -> sqlite3.Cursor:
        return self._conn.execute(
            '''
            SELECT * FROM matches
            WHERE start_time > ?
            ORDER BY start_time ASC
            LIMIT 10
            ''',
            (int(time.time()),)
        )

    def schedule_match(self, match: ScheduledMatch) -> None:
        self._conn.execute(
            '''
                INSERT INTO matches VALUES(
                    :scheduled_timestamp,
                    :away_team,
                    :home_team,
                    :scheduled_at,
                    :scheduled_by
                );
            ''',
            match.model_dump()
        )

    def cancel_match(self, home: int, away: int) -> sqlite3.Cursor:
        return self._conn.execute(
            '''
            DELETE FROM MATCHES
            WHERE home_team = ? AND away_team = ?;
            ''',
            (home, away)
        )

    def _create_matchlist_table(self) -> None:
        self._conn.execute(
            '''
                CREATE TABLE IF NOT EXISTS matches (
                    start_time BIG INT,
                    away_team BIG INT,
                    home_team BIG INT,
                    scheduled_at BIG INT,
                    scheduled_by BIG INT,
                    PRIMARY KEY (home_team, away_team)
                );
            '''
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if exc_type:
            self._conn.rollback()
        else:
            self._conn.commit()
