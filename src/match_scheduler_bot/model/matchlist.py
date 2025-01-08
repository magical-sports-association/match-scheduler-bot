"""
    :module_name: matchlist
    :module_summary: a repository for schedule matches
    :module_author: CountTails
"""

import logging
import time
import sqlite3

from dataclasses import asdict
from typing import List

from .rows import (
    MatchToSchedule,
    ScheduledMatch,
    MatchToCancel
)
from ..exceptions import (
    DuplicatedMatchDetected,
    MatchScheduleNotObtained,
    CancellingNonexistantMatch
)


__LOGGER__ = logging.getLogger(__name__)


class MatchListRepository:
    def __init__(self, dbpath: str):
        self._conn = sqlite3.connect(dbpath)
        self._conn.row_factory = ScheduledMatch.from_sql_row
        self._create_matchlist_table()

    def find_upcoming_matches(
            self,
            not_before: int,
            page_size: int = 10,
            page_num: int = 0
    ) -> List[ScheduledMatch]:
        return self._conn.execute(
            '''
                SELECT * FROM matches
                WHERE start_time > ?
                ORDER BY start_time ASC
                LIMIT ?
                OFFSET ?
            ''',
            (not_before, page_size, page_num * page_size)
        ).fetchall()

    def delete_match(
        self,
        match: MatchToCancel
    ) -> ScheduledMatch:
        cancelled_match = self._conn.execute(
            '''
                DELETE FROM matches
                WHERE team_1_id = ? AND team_2_id = ?
                RETURNING *;
            ''',
            (match.team_1_id, match.team_2_id)
        ).fetchone()
        if cancelled_match:
            return cancelled_match
        raise CancellingNonexistantMatch(
            'Match cannot be cancelled because it does not exist'
        )

    def insert_match(
        self,
        match: MatchToSchedule
    ) -> ScheduledMatch:
        try:
            return self._conn.execute(
                '''
                    INSERT INTO matches VALUES (
                        :proposed_start_timestamp,
                        :team_1_id,
                        :team_2_id
                    ) RETURNING *;
                ''',
                asdict(match)
            ).fetchone()
        except sqlite3.IntegrityError as err:
            raise DuplicatedMatchDetected(
                'Match between provided teams is already scheduled'
            ) from err

    def _create_matchlist_table(self) -> None:
        self._conn.execute(
            '''
                CREATE TABLE IF NOT EXISTS matches (
                    start_time BIG INT,
                    team_1_id BIG INT,
                    team_2_id BIG INT,
                    PRIMARY KEY (team_1_id, team_2_id)
                );
            '''
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if exc_val:
            self._conn.rollback()
        else:
            self._conn.commit()
