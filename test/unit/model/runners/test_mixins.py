'''
    :module_name: test_mixins
    :module_summary: unit tests for mixin class functionality
    :module_author: CountTails
'''

from unittest.mock import patch
from asyncio import sleep

from match_scheduler_bot.model.runners._mixins import TransactionalMixin

import pytest

import aiosqlite


@patch(
    target='match_scheduler_bot.model.pool.AsyncConnectionPool',
    autospec=True
)
@pytest.mark.asyncio
async def test_mixin_commits_on_successful_transaction(
        mock_pool,
):
    mixin = TransactionalMixin(mock_pool, aiosqlite.Row)
    async with mixin as conn:
        await sleep(1)  # Simulate running queries in transaction
        mock_pool.acquire.assert_awaited_once_with(aiosqlite.Row)

    mock_pool.release.assert_awaited_once_with(conn)
    conn.commit.assert_awaited_once()
    conn.rollback.assert_not_awaited()


@patch(
    target='match_scheduler_bot.model.pool.AsyncConnectionPool',
    autospec=True
)
@pytest.mark.asyncio
async def test_mixin_rollback_on_problematic_transaction(
    mock_pool,
):
    with pytest.raises(aiosqlite.Error):
        mixin = TransactionalMixin(mock_pool, aiosqlite.Row)
        async with mixin as conn:
            await sleep(1)  # Simulate running queries in transaction
            raise aiosqlite.Error()

    mock_pool.acquire.assert_awaited_once_with(aiosqlite.Row)
    mock_pool.release.assert_awaited_once_with(conn)
    conn.rollback.assert_awaited_once()
    conn.commit.assert_not_awaited()
