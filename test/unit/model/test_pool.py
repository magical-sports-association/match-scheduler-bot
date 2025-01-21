'''
    :module_name: test_pool
    :module_summary: unit tests for an asyncronous connection pool class
    :module_author: CountTails
'''

import pytest
import pytest_asyncio

from match_scheduler_bot.model.pool import AsyncConnectionPool


import aiosqlite


@pytest_asyncio.fixture(scope='function', loop_scope='session')
async def apool():
    pool = AsyncConnectionPool(
        path=':memory:',
        pool_size=3
    )
    yield pool
    await pool.destroy()


@pytest.fixture(scope='session')
def custom_row_factory():
    def f(cursor, row):
        return

    return f


@pytest.mark.asyncio
async def test_new_pool_attributes_are_as_specified(apool):
    print(apool)
    assert apool.available_connections == 3
    assert apool.database_path == ':memory:'


@pytest.mark.asyncio
async def test_can_acquire_connection_from_pool(apool):
    conn = await apool.acquire()
    assert isinstance(conn, aiosqlite.Connection)
    assert apool.available_connections < 3

    await apool.release(conn)
    assert apool.available_connections == 3


@pytest.mark.asyncio
async def test_can_acquire_connection_from_pool_with_custom_row_factory(
        apool,
        custom_row_factory
):
    conn = await apool.acquire(custom_row_factory)
    assert isinstance(conn, aiosqlite.Connection)
    assert apool.available_connections < 3
    assert conn.row_factory == custom_row_factory

    await apool.release(conn)
    assert apool.available_connections == 3
