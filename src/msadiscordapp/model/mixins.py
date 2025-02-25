'''
    :module_name: mixins
    :module_summary: the base class of all query runner classes
    :module_author: CountTails
'''

import logging
from typing import Callable, Optional
from contextlib import asynccontextmanager

from .processing.pool import AsyncConnectionPool

import aiosqlite

__LOGGER__ = logging.getLogger(__name__)
type RowFactoryFn = Callable[[aiosqlite.Cursor, aiosqlite.Row], object]


class TransactionalMixin:

    '''
        Mixin class that provides an asynccontextmanager to manage transactions
        Classes that manage a domain of database interactions for the app
        can inherit from this mixin to automatically include transactions
    '''

    def __init__(
        self,
        pool: AsyncConnectionPool,
    ) -> None:
        '''
            Initializes attributes for the matchlist query runner instance

            Parameters:
                pool [AsyncConnectionPool]: pool to borrow connections from

            Returns:
                None
        '''
        self._pool = pool

    @asynccontextmanager
    async def begin(
        self,
        row_factory: RowFactoryFn = aiosqlite.Row
    ) -> aiosqlite.Connection:
        '''
            Begins a SQL transaction by borrowing a connection from the pool
            On exit, cleans up the transaction and returns the connection

            Parameters:
                row_factory [RowFactoryFn]: function to map rows to objects

            Yields:
                aiosqlite.Connection -> the borrowed connection
        '''
        conn: Optional[aiosqlite.Connection] = None
        try:
            __LOGGER__.debug('Requesting connection from the pool')
            conn = await self._pool.acquire(row_factory)
            __LOGGER__.debug('Acquired connection from the pool')
            yield conn
        except Exception as err:
            __LOGGER__.debug(
                'Rolling back because a problem occurred in the transaction'
            )
            await conn.rollback()
            __LOGGER__.error('Reason: %s', str(err))
            raise
        else:
            __LOGGER__.debug(
                'Transaction concluded without a problem'
            )
            await conn.commit()
        finally:
            __LOGGER__.debug('Returning borrowed connection')
            if conn:
                await self._pool.release(conn)
