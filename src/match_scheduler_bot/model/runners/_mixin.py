'''
    :module_name: _mixin
    :module_summary: the base class of all query runner classes
    :module_author: CountTails
'''

import logging
from contextlib import asynccontextmanager
from typing import Callable

from ..pool import AsyncConnectionPool

import aiosqlite

__LOGGER__ = logging.getLogger(__name__)


class QueryRunnerMixin:

    @asynccontextmanager
    async def do_transaction(
        self,
        pool: AsyncConnectionPool,
        row_factory: Callable[[aiosqlite.Cursor, aiosqlite.Row], object]
    ):
        __LOGGER__.debug('Beginning new transaction...')
        conn = None
        try:
            conn = await pool.acquire(row_factory)
            __LOGGER__.debug(
                'Successfully acquired a connection from given pool'
            )
            yield conn
        except aiosqlite.Error as err:
            __LOGGER__.debug(
                'Transaction stopped; rolling back',
            )
            conn.rollback()
            __LOGGER__.error('Reason: %s', str(err))
            raise err
        else:
            __LOGGER__.debug(
                'Transaction concluded without errors; committing'
            )
            conn.commit()
        finally:
            __LOGGER__.debug('Cleaning up Transaction.')
            if conn is not None:
                await pool.release(conn)
