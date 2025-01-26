'''
    :module_name: _mixins
    :module_summary: the base class of all query runner classes
    :module_author: CountTails
'''

import logging
from contextlib import asynccontextmanager
from typing import Callable

from ..pool import AsyncConnectionPool

import aiosqlite

__LOGGER__ = logging.getLogger(__name__)
type RowFactoryFn = Callable[[aiosqlite.Cursor, aiosqlite.Row], object]


class TransactionalMixin:

    '''
        Mixin class that provides an asynccontextmanager to manage transactions
        Classes that manage a domain of database interactions for the app
        can inherit from this mixin to automatically include transactions
    '''

    @asynccontextmanager
    async def do_transaction(
        self,
        pool: AsyncConnectionPool,
        row_factory: RowFactoryFn
    ):
        '''
            A decorated async generator that provides transaction management

            Parameters:
                pool [AsyncConnectionPool]: pool to borrow a connection from
                row_factory [RowFactoryFn]: factory function for row conversion
            Yields:
                conn [aiosqlite.Connection] borrowed connection to run queries
            Raises:
                err [aiosqlite.Error] database error halting transaction
        '''
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
            await conn.rollback()
            __LOGGER__.error('Reason: %s', str(err))
            raise err
        else:
            __LOGGER__.debug(
                'Transaction concluded without errors; committing'
            )
            await conn.commit()
        finally:
            __LOGGER__.debug('Cleaning up Transaction.')
            if conn is not None:
                await pool.release(conn)
