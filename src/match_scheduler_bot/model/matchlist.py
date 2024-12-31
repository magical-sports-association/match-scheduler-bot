"""
    :module_name: matchlist
    :module_summary: a repository for schedule matches
    :module_author: CountTails
"""

import pydantic
from typing_extensions import Annotated
from typing import List
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

    def find_match(self, start_time, home, away) -> ScheduledMatch:
        pass

    def find_matches(self) -> List[ScheduledMatch]:
        pass

    def schedule_match(self, match: ScheduledMatch) -> None:
        self._conn.execute(
            '''
                INSERT INTO matches VALUES(
                    :scheduled_timestamp,
                    :home_team,
                    :away_team,
                    :scheduled_at,
                    :scheduled_by
                );
            ''',
            match.model_dump()
        )

    def cancel_match(self, match: ScheduledMatch) -> None:
        pass

    def _create_matchlist_table(self) -> None:
        self._conn.execute(
            '''
                CREATE TABLE IF NOT EXISTS matches (
                    start_time BIG INT,
                    home_team BIG INT,
                    away_team BIG INT,
                    scheduled_at BIG INT,
                    scheduled_by BIG INT
                );
            '''
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        pass
