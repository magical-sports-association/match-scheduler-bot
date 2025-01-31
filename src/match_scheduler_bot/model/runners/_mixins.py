'''
    :module_name: _mixins
    :module_summary: the base class of all query runner classes
    :module_author: CountTails
'''

import logging
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

    def __init__(
        self,
        pool: AsyncConnectionPool,
        row_factory: RowFactoryFn = aiosqlite.Row
    ):
        '''
            Initializes attributes for the matchlist query runner instance

            Parameters:
                pool [AsyncConnectionPool]: pool to borrow connections from
                row_factory [RowFactoryFn]: factory function for row conversion

            Returns:
                None
        '''
        self._pool = pool
        self._row_factory = row_factory
        self._conn = None

    async def __aenter__(self) -> aiosqlite.Connection:
        '''
            Magic method to operate sql transactions using a with statement

            Parameters:
                None
            Returns:
                [aiosqlite.Connection] connection to execute transaction on
        '''
        __LOGGER__.debug('Start new transaction...')
        self._conn = await self._pool.acquire(self._row_factory)
        __LOGGER__.debug('Acquired connection from pool')
        return self._conn

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        '''
            Magic method to conclude sql transactions based on the outcome

            Parameters:
                exc_type [Exception]: class of exception raised in transaction
                exc_value [Exception]: instance of raised exception
                traceback: traceback info of the raised exception
            Returns:
                None
        '''
        if exc_value:
            __LOGGER__.debug(
                'Rolling back because a problem occurred in the transaction'
            )
            await self._conn.rollback()
            __LOGGER__.error('Reason: %s', str(exc_value))
        else:
            __LOGGER__.debug('Transaction concluded without a problem')
            await self._conn.commit()

        __LOGGER__.debug('Cleaning up transaction')
        await self._pool.release(self._conn)
        self._conn = None
