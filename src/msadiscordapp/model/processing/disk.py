'''
    :module_name: disk
    :module_summary: disk access with builtin caching capabilities
    :module_author: CountTails
'''

import logging
from typing import Dict, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from ..adts import CachingRecord
from ...exceptions import MessageContentNotReadable


import aiofiles


__LOGGER__ = logging.getLogger(__name__)


class DiskCache:
    '''
        Provides caching capabilities to an asychronous file reader

        Attributes:
            None

        Methods:
            async fetch_text(): retrieve a path's content (from cache or disk)
    '''

    BLANK = ''

    def __init__(
        self,
        root_path: Path,
        time_to_live: timedelta
    ) -> None:
        '''
            Initializes the instance with the given path and ttl

            Parameters:
                root_path [Path]: absolute path to search for cache population
                time_to_live [timedelta]: time to consider cache valid

            Returns:
                None
        '''
        self._root = root_path
        self._ttl = time_to_live
        self._cache: Dict[Path, CachingRecord] = {}

    async def fetch_text(self, filename: Optional[Path] = None) -> str:
        '''
            Gets the contents associated with filename from cache or on disk

            Paramters:
                filename [Optional[Path]]: file's contents to obtain

            Returns:
                str -> cached contents if still valid, or refreshed from disk
        '''
        try:
            if filename is None:
                __LOGGER__.debug(
                    'No filename provided, returning the empty string'
                )
                return self.BLANK

            __LOGGER__.debug(
                'Attempting to fetch contents of `%s` from cache', filename
            )
            cached = self._cache[filename]

            if cached.is_expired():
                __LOGGER__.debug(
                    'Cache contained requested file, but is out of date'
                )
                refreshed = await self._refresh(filename)
                self._update_cache(cached, refreshed)

            __LOGGER__.info(
                'Returning contents for `%s`',
                self._root / filename
            )
            return cached.contents
        except KeyError:
            __LOGGER__.error(
                'Cache did not contain requested file: `%s`',
                self._root / filename
            )
            __LOGGER__.debug(
                'Attempting to fulfill request from disk'
            )
            contents_from_disk = await self._refresh(filename)
            new_cached = CachingRecord(datetime.today(), str())
            self._cache[filename] = new_cached
            self._update_cache(new_cached, contents_from_disk)
            return contents_from_disk

    async def _refresh(self, file: Path) -> str:
        '''
            Coroutine to retrieve a file's contents from disk

            Parameters:
                file [Path]: file to read (relative to self._root)

            Returns:
                str -> the file's contents

            Raises:
                MessageContentNotReadable: if contents could not be read
        '''
        try:
            __LOGGER__.debug(
                'Attempting to read `%s` from disk',
                self._root / file
            )
            async with aiofiles.open(self._root / file, mode='r') as f_in:
                return await f_in.read()
        except FileNotFoundError as err:
            __LOGGER__.error('File `%s` not found on disk', self._root / file)
            raise MessageContentNotReadable(
                err.strerror,
                self._root / file
            ) from err
        except IsADirectoryError as err:
            __LOGGER__.error('Path `%s` is a directory', self._root / file)
            raise MessageContentNotReadable(
                err.strerror,
                self._root / file
            ) from err
        except PermissionError as err:
            __LOGGER__.error('Path `%s` is inaccessible', self._root / file)
            raise MessageContentNotReadable(
                err.strerror,
                self._root / file
            )

    def _update_cache(
        self,
        caching: CachingRecord,
        new_contents: str
    ) -> None:
        '''
            Updates the attributes of the given caching object

            Parameters:
                caching [CachingRecord]: caching object to update
                new_contents [str]: new data to replace existing cache data

            Returns:
                None
        '''
        now = datetime.now(tz=timezone.utc)
        new_ttl = now + self._ttl
        __LOGGER__.debug('New expiration time is: %s', new_ttl.isoformat())
        caching.expires_at = new_ttl
        caching.contents = new_contents
        __LOGGER__.debug('Updated the contents of the caching record')
