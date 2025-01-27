'''
    :module_name: test_matchlist
    :module_summary: unit test for the matchlist query runner class
    :module_author: CountTails
'''

from unittest.mock import patch, AsyncMock
from dataclasses import dataclass
from typing import Callable
import random

from match_scheduler_bot.model.runners.matchlist import MatchlistQueryRunner
from match_scheduler_bot.model.pool import AsyncConnectionPool

import pytest
import pytest_asyncio

import aiosqlite


@pytest.fixture(scope='function')
def mock_matchlist():
    return [
        (500, 'A', 'B'),
        (900, 'C', 'D'),
        (1700, 'A', 'C'),
        (2200, 'A', 'D'),
        (2900, 'B', 'D')
    ]


@pytest.fixture(scope='session')
def mock_row_factory():

    @dataclass
    class TeamRow:
        start: int
        team1: str
        team2: str

        @classmethod
        def from_row(cls, row):
            return cls(
                row[0],
                row[1],
                row[2]
            )

    return TeamRow.from_row


@pytest.fixture(scope='function')
def query_runner(mock_row_factory):
    return MatchlistQueryRunner(None, mock_row_factory)


@patch.object(
    MatchlistQueryRunner,
    '__aenter__',
    return_value=AsyncMock()
)
@patch.object(
    MatchlistQueryRunner,
    '__aexit__',
)
@pytest.mark.asyncio
async def test_create_matchlist_table_query_run(
    transact_cleanup,
    transact_init,
    query_runner
):

    conn = transact_init.return_value
    await query_runner.create_matchlist_table()

    transact_init.assert_awaited_once()
    conn.execute.assert_awaited_once_with(query_runner.create_table_stmt)
    transact_cleanup.assert_awaited_once()


@patch.object(
    MatchlistQueryRunner,
    '__aenter__',
    return_value=AsyncMock()
)
@patch.object(
    MatchlistQueryRunner,
    '__aexit__',
)
@pytest.mark.asyncio
@pytest.mark.parametrize('not_after', [500, 1000, 2500])
async def test_remove_match_rows_before_given_timestamp(
    transact_cleanup,
    transact_init,
    query_runner,
    mock_matchlist,
    mock_row_factory,
    not_after
):
    conn = transact_init.return_value
    conn.execute.return_value = AsyncMock()
    cursor = conn.execute.return_value
    cursor.fetchall.return_value = list(
        map(
            mock_row_factory,
            filter(
                lambda row: row[0] <= not_after,
                mock_matchlist
            )
        )
    )

    deleted = await query_runner.delete_past_matches(not_after)

    transact_init.assert_awaited_once()
    conn.execute.assert_awaited_with(
        query_runner.cleanup_past_matches_query,
        (not_after,)
    )
    transact_cleanup.assert_awaited_once()

    for delete in deleted:
        assert delete.start <= not_after
