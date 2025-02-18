'''
    :module_name: pool
    :module_summary: an asyncronous connection management module
    :module_author: CountTails
'''

from __future__ import annotations
from typing import Callable
import logging
import asyncio
import pathlib

import aiosqlite


__LOGGER__ = logging.getLogger(__name__)
type RowFactoryFn = Callable[[aiosqlite.Cursor, aiosqlite.Row], object]


class AsyncConnectionPool:
    '''
        Manages a set of connections that can be borrowed from in an async env

        Attributes:
            None

        Methods:
            await acquire(): borrows a connection from this pool
            await release(): returns the given connection to this pool
            async with x: use this pool in an async env and destroy it on exit
    '''

    def __init__(self, path: str | pathlib.Path, size: int) -> None:
        '''
            Initializes the internal structure of this instance for allow
            for pool creation. The pool is NOT populated during initialization.
            Instead, connections are created lazily and are returned to the
            pool after they are first used.

            Parameters:
                path [str | pathlib.Path]: path to the database file
                size [int]: number of connection this pool will manage
        '''
        self._dbpath = path
        self._sz = size
        self._pool = asyncio.Queue(maxsize=self._sz)
        self._lock = asyncio.Lock()
        __LOGGER__.debug(
            'Connections in this pool with use dbfile: %s',
            self._dbpath
        )
        __LOGGER__.debug(
            'Up to %d connections will reside in this pool',
            self._sz
        )

    async def acquire(
        self,
        row_factory: RowFactoryFn = aiosqlite.Row
    ) -> aiosqlite.Connection:
        '''
            Acquires a proxied connection from this pool

            Parameters:
                row_factory [RowFactoryFn]: function to map rows to objects

            Returns:
                aiosqlite.Connection -> borrowed database connection
        '''
        __LOGGER__.info('Retrieving the next available connection')
        conn = await self._get_or_make_conn(row_factory)
        __LOGGER__.debug(
            'Setting connection\'s row factory to %s',
            str(row_factory)
        )
        conn.row_factory = row_factory
        __LOGGER__.debug('Lending connection %s to the caller', str(conn))
        return conn

    async def release(self, conn: aiosqlite.Connection) -> None:
        '''
            Returns the given connection to this pool

            Parameters:
                conn [aiosqlite.Connection]: the connection to return

            Returns:
                None
        '''
        __LOGGER__.info(
            'Returning borrowed connection to the pool: %s',
            str(conn)
        )
        await self._pool.put(conn)

    async def _get_or_make_conn(
        self,
    ) -> aiosqlite.Connection:
        '''
            Get a connection from the pool if available.
            If none available, try to create a new one lazily
            If no more can be created, yield and wait for the next one

            Returns:
                aiosqlite.Connection -> proxied connection to use
        '''
        if self._pool.empty():
            __LOGGER__.debug(
                'Pool is currently empty, trying to create a new connection'
            )
            async with self._lock:
                if self._sz > 0:
                    __LOGGER__.debug(
                        'Not all connections created, creating one lazily'
                    )
                    self._sz -= 1
                    await self._pool.put(
                        await aiosqlite.connect(self._dbpath)
                    )
                    __LOGGER__.debug(
                        'New connection added to pool'
                    )

        __LOGGER__.info('Awaiting next available connection from pool')
        return await self._pool.get()

    async def _destroy(self) -> None:
        '''
            Destroys this pools by closing all connections
            Typically used in the __aexit__ method of this class

            Returns:
                None
        '''
        __LOGGER__.debug('Closing all connections in this pool')
        while not self._pool.empty():
            conn = await self._pool.get()
            await conn.close()
            __LOGGER__.debug('Connection %s has been closed', str(conn))

    async def __aenter__(self) -> AsyncConnectionPool:
        '''
            Allows for the `async with x` operation to work

            Returns:
                AsyncConnectionPool -> pool to use in an `async with x` env
        '''
        return self

    async def __aexit__(self, exc_type, exc_val, traceback) -> None:
        '''
            Concludes the `async with x` block by cleaning up this pool

            Parameters:
                exc_type [Optional[type]]: Exception class causing the exit
                exc_val [Optional[Exception]]: Actual exception causing exit
                traceback [Optional[traceback]]: Traceback info, if any

            Returns:
                None
        '''
        await self._destroy()
