'''
    :module_name: test_matchlist
    :module_summary: unit test for the matchlist query runner class
    :module_author: CountTails
'''

from unittest.mock import patch, AsyncMock
from dataclasses import dataclass, asdict

from match_scheduler_bot.model.runners.matchlist import MatchlistQueryRunner
from match_scheduler_bot.exceptions import (
    DuplicatedMatchDetected,
    CancellingNonexistantMatch
)

import pytest

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
        proposed_start_timestamp: int
        team_1_id: str
        team_2_id: str

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


@pytest.fixture(scope='function')
def proposed_match_scheduling(mock_row_factory):
    return mock_row_factory(
        (1500, 'B', 'C')
    )


@pytest.fixture(scope='function')
def proposed_match_cancelling(mock_row_factory):
    return mock_row_factory(
        (2900, 'B', 'D')
    )


@patch.object(
    MatchlistQueryRunner,
    '__aenter__'
)
@patch.object(
    MatchlistQueryRunner,
    '__aexit__'
)
@pytest.mark.asyncio
async def test_create_matchlist_table_query_run(
    transact_cleanup,
    transact_init,
    query_runner
):

    mock_conn = AsyncMock(
        execute=AsyncMock()
    )
    transact_init.return_value = mock_conn

    await query_runner.create_matchlist_table()

    transact_init.assert_awaited_once()
    mock_conn.execute.assert_awaited_once_with(query_runner.create_table_stmt)
    transact_cleanup.assert_awaited_once()


@patch.object(
    MatchlistQueryRunner,
    '__aenter__'
)
@patch.object(
    MatchlistQueryRunner,
    '__aexit__'
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
    mock_conn = AsyncMock(
        execute=AsyncMock(
            return_value=AsyncMock(
                fetchall=AsyncMock(
                    return_value=list(
                        map(
                            mock_row_factory,
                            filter(
                                lambda row: row[0] <= not_after,
                                mock_matchlist
                            )
                        )
                    )
                )
            )
        )
    )
    transact_init.return_value = mock_conn

    deleted = await query_runner.delete_past_matches(not_after)

    transact_init.assert_awaited_once()
    mock_conn.execute.assert_awaited_once_with(
        query_runner.cleanup_past_matches_query,
        (not_after,)
    )
    transact_cleanup.assert_awaited_once()

    for delete in deleted:
        assert delete.proposed_start_timestamp <= not_after


@patch.object(
    MatchlistQueryRunner,
    '__aenter__'
)
@patch.object(
    MatchlistQueryRunner,
    '__aexit__'
)
@pytest.mark.asyncio
async def test_add_proposed_match_to_matchlist(
    transact_cleanup,
    transact_init,
    query_runner,
    mock_matchlist,
    mock_row_factory,
    proposed_match_scheduling
):
    mock_conn = AsyncMock(
        execute=AsyncMock(
            return_value=AsyncMock(
                fetchone=AsyncMock(
                    return_value=proposed_match_scheduling
                )
            )
        )

    )
    transact_init.return_value = mock_conn

    scheduled = await query_runner.schedule_match(proposed_match_scheduling)

    assert scheduled == proposed_match_scheduling
    transact_init.assert_awaited_once()
    mock_conn.execute.assert_awaited_once_with(
        query_runner.schedule_match_query,
        asdict(proposed_match_scheduling)
    )
    transact_cleanup.assert_awaited_once()


@patch.object(
    MatchlistQueryRunner,
    '__aenter__'
)
@patch.object(
    MatchlistQueryRunner,
    '__aexit__',
)
@pytest.mark.asyncio
async def test_add_duplicate_proposed_match(
    transact_cleanup,
    transact_init,
    query_runner,
    mock_matchlist,
    mock_row_factory,
    proposed_match_scheduling
):
    def _mock_aexit_reraise(exc_type, exc_val, traceback):
        if exc_type is not None:
            raise exc_val

    mock_conn = AsyncMock(
        execute=AsyncMock(
            side_effect=aiosqlite.IntegrityError
        )
    )
    transact_init.return_value = mock_conn
    transact_cleanup.side_effect = _mock_aexit_reraise

    with pytest.raises(DuplicatedMatchDetected):
        await query_runner.schedule_match(proposed_match_scheduling)

    transact_init.assert_awaited_once()
    mock_conn.execute.assert_awaited_once_with(
        query_runner.schedule_match_query,
        asdict(proposed_match_scheduling)
    )
    transact_cleanup.assert_awaited_once()


@patch.object(
    MatchlistQueryRunner,
    '__aenter__'
)
@patch.object(
    MatchlistQueryRunner,
    '__aexit__',
)
@pytest.mark.asyncio
async def test_cancel_existing_match(
    transact_cleanup,
    transact_init,
    query_runner,
    mock_matchlist,
    mock_row_factory,
    proposed_match_cancelling
):
    mock_conn = AsyncMock(
        execute=AsyncMock(
            return_value=AsyncMock(
                fetchone=AsyncMock(
                    return_value=proposed_match_cancelling
                )
            )
        )
    )
    transact_init.return_value = mock_conn

    cancelled = await query_runner.cancel_match(proposed_match_cancelling)

    assert cancelled == proposed_match_cancelling
    transact_init.assert_awaited_once()
    mock_conn.execute.assert_awaited_once_with(
        query_runner.cancel_match_query,
        (
            proposed_match_cancelling.team_1_id,
            proposed_match_cancelling.team_2_id
        )
    )
    transact_cleanup.assert_awaited_once()


@patch.object(
    MatchlistQueryRunner,
    '__aenter__'
)
@patch.object(
    MatchlistQueryRunner,
    '__aexit__',
)
@pytest.mark.asyncio
async def test_cancel_nonexisting_match(
    transact_cleanup,
    transact_init,
    query_runner,
    mock_matchlist,
    mock_row_factory,
    proposed_match_cancelling
):
    def _mock_aexit_reraise(exc_type, exc_val, traceback):
        if exc_type is not None:
            raise exc_val

    transact_cleanup.side_effect = _mock_aexit_reraise
    mock_conn = AsyncMock(
        execute=AsyncMock(
            return_value=AsyncMock(
                fetchone=AsyncMock(
                    return_value=None
                )
            )
        )
    )
    transact_init.return_value = mock_conn

    with pytest.raises(CancellingNonexistantMatch):
        await query_runner.cancel_match(proposed_match_cancelling)

    transact_init.assert_awaited_once()
    mock_conn.execute.assert_awaited_once_with(
        query_runner.cancel_match_query,
        (
            proposed_match_cancelling.team_1_id,
            proposed_match_cancelling.team_2_id
        )
    )
    transact_cleanup.assert_awaited_once()


@patch.object(
    MatchlistQueryRunner,
    '__aenter__'
)
@patch.object(
    MatchlistQueryRunner,
    '__aexit__'
)
@pytest.mark.asyncio
@pytest.mark.parametrize('not_after', [500, 1000, 2500])
async def test_collect_match_rows_after_given_timestamp(
    transact_cleanup,
    transact_init,
    query_runner,
    mock_matchlist,
    mock_row_factory,
    not_after
):
    mock_conn = AsyncMock(
        execute=AsyncMock(
            return_value=AsyncMock(
                fetchall=AsyncMock(
                    return_value=list(
                        map(
                            mock_row_factory,
                            filter(
                                lambda row: row[0] > not_after,
                                mock_matchlist
                            )
                        )
                    )
                )
            )
        )
    )
    transact_init.return_value = mock_conn

    calendar = await query_runner.find_upcoming_match(not_after)

    transact_init.assert_awaited_once()
    mock_conn.execute.assert_awaited_once_with(
        query_runner.upcoming_matches_query,
        (not_after, 10, 0)
    )
    transact_cleanup.assert_awaited_once()

    for match in calendar:
        assert match.proposed_start_timestamp > not_after
