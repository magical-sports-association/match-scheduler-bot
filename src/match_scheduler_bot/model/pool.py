'''
    :module_name: pool
    :module_summary: an asyncronous connection management module
    :module_author: CountTails
'''

import logging
import asyncio

import aiosqlite


__LOGGER__ = logging.getLogger(__name__)


class AsyncConnectionPool:
    def __init__(self, path: str, pool_size: int):
        '''
            Lazily initializes the connection pool
            Parameters:
                path [str]: the path of the dbfile for these connections
                pool_size [int]: the number of connection to put in the pool
            Returns:
                None
        '''
        self._dbpath = path
        self._sz = pool_size
        self._pool = None

    @property
    def available_connections(self) -> int:
        '''
            Returns the number of connection currently in the pool
            or the number of requested connections pool is not initialized yet
            Returns:
                [int]: the number of connections
        '''
        return self._pool.qsize() if self._pool else self._sz

    @property
    def database_path(self) -> str:
        '''
            Returns the path of the dbfile for this connection pool
            Returns:
                [str]: path of the connections in this pool
        '''
        return self._dbpath

    async def _initialize_pool(self) -> None:
        '''
            Asyncronous initialization of connections in this pool
        '''
        self._pool = asyncio.Queue(maxsize=self._sz)
        for _ in range(self._sz):
            self._pool.put_nowait(
                await aiosqlite.connect(self._dbpath)
            )

    async def acquire(self, row_factory=aiosqlite.Row) -> aiosqlite.Connection:
        '''
            Get the next available connection from this pool
            Parameters:
                row_factory [callable]: factory function to convert sqlite rows
            Returns:
                conn [aiosqlite.Connection]: connection from the pool
        '''
        if not self._pool:
            await self._initialize_pool()

        conn = await self._pool.get()
        conn.row_factory = row_factory
        return conn

    async def release(self, connection: aiosqlite.Connection) -> None:
        '''
            Return the given connection to this pool
            Parameters:
                connection [aiosqlite.Connection]: connection to return
            Returns:
                None
        '''
        await self._pool.put(connection)

    async def destroy(self) -> None:
        '''
            Close all connections in this pool
        '''
        while self._pool and not self._pool.empty():
            conn = await self._pool.get()
            await conn.close()

        self._pool = None
