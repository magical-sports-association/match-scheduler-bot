'''
    :module_name: test_mixins
    :module_summary: unit tests for mixin class functionality
    :module_author: CountTails
'''

from unittest.mock import patch
from asyncio import sleep

from match_scheduler_bot.model.runners._mixins import TransactionalMixin

import pytest
import pytest_asyncio

import aiosqlite


@pytest.fixture(scope='function')
def transaction_mixin():
    return TransactionalMixin()


@patch(
    target='match_scheduler_bot.model.pool.AsyncConnectionPool',
    autospec=True
)
@pytest.mark.asyncio
async def test_mixin_commits_on_successful_transaction(
        mock_pool,
        transaction_mixin
):
    async with transaction_mixin.do_transaction(mock_pool, aiosqlite.Row) as conn:
        await sleep(3)  # Simulate running queries in transaction
        mock_pool.acquire.assert_awaited_once_with(aiosqlite.Row)

    mock_pool.release.assert_awaited_once_with(conn)
    conn.commit.assert_called_once()
    conn.rollback.assert_not_awaited()


@patch(
    target='match_scheduler_bot.model.pool.AsyncConnectionPool',
    autospec=True
)
@pytest.mark.asyncio
async def test_mixin_rollback_on_problematic_transaction(
    mock_pool,
    transaction_mixin
):
    with pytest.raises(aiosqlite.Error):
        async with transaction_mixin.do_transaction(mock_pool, aiosqlite.Row) as conn:
            await sleep(3)  # Simulate running queries in transaction
            mock_pool.acquire.assert_awaited_once_with(aiosqlite.Row)
            raise aiosqlite.Error()

    mock_pool.release.assert_awaited_once_with(conn)
    conn.rollback.assert_awaited_once()
    conn.commit.assert_not_awaited()
