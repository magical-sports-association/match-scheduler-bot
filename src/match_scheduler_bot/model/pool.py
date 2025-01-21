'''
    :module_name: pool
    :module_summary: an asyncronous connection management module
    :module_author: CountTails
'''

import logging
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from typing import List

import aiosqlite


__LOGGER__ = logging.getLogger(__name__)


class AsyncConnectionPool:
    def __init__(self, path: str, pool_size: int):
        self._dbpath = path
        self._sz = pool_size
        self._pool = None

    @property
    def available_connections(self):
        return self._pool.qsize() if self._pool else self._sz

    @property
    def database_path(self):
        return self._dbpath

    async def _initialize_pool(self):
        self._pool = asyncio.Queue(maxsize=self._sz)
        for _ in range(self._sz):
            self._pool.put_nowait(
                await aiosqlite.connect(self._dbpath)
            )

    async def acquire(self, row_factory=aiosqlite.Row):
        if not self._pool:
            await self._initialize_pool()

        conn = await self._pool.get()
        conn.row_factory = row_factory
        return conn

    async def release(self, connection: aiosqlite.Connection):
        await self._pool.put(connection)

    async def destroy(self):
        while self._pool and not self._pool.empty():
            conn = await self._pool.get()
            await conn.close()
