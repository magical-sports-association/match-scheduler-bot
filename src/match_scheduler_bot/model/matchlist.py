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
    away_team: str
    home_team: str
    scheduled_at: Annotated[int, pydantic.Field(gt=0)]
    scheduled_by: str


class MatchListRepository:
    def __init__(self, connecturi: str):
        self._conn = sqlite3.connect(connecturi)
        self._create_matchlist_table()

    def find_match(self, start_time, home, away) -> ScheduledMatch:
        pass

    def find_matches(self) -> List[ScheduledMatch]:
        pass

    def schedule_match(self, match: ScheduledMatch) -> None:
        pass

    def cancel_match(self, match: ScheduledMatch) -> None:
        pass

    def _create_matchlist_table(self) -> None:
        pass
