'''
    :module_name: filecache
    :module_summary: file reader utility that caches contents
    :module_author: CountTails
'''

import logging
from typing import Dict
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone

from ..exceptions import MissingMessageFormat


import aiofiles


__LOGGER__ = logging.getLogger(__name__)


@dataclass
class CachedContents:
    '''
        Container for the contents of a file read and the expiration timestamp

        Attributes:
            expires_at [int]: unix timestamp marking the expiration time
            contents [str]: contents of file read
    '''
    expires_at: int
    contents: str

    def is_expired(self) -> bool:
        '''
            Checks if this content has expired

            Returns:
                [bool] True is expired, otherwise False
        '''
        now = round(datetime.now(timezone.utc).timestamp())
        __LOGGER__.debug(
            'Contents expire at %d; current time is %d',
            self.expires_at,
            now
        )
        return now > self.expires_at


class FileCacheProvider:
    '''
        Asyncronous file reader with caching capabilities.
        Reads file contents into a cache lazily and uses cache if ttl is ok.
        Rereads file contents if ttl has been exceeded.
    '''
    BLANK = ''

    def __init__(
        self,
        root_path: Path,
        time_to_live: int
    ):
        '''
            Initializes the provider with the given path and ttl

            Parameters:
                root_path [Path]: absolute path to directory containing files
                time_to_live [int]: number of seconds to consider data valid

            Returns:
                None
        '''
        self._root = root_path
        self._ttl = time_to_live
        self._cache: Dict[Path, CachedContents] = {}

    async def get_text(self, filename: Path = None) -> str:
        '''
            Gets the contents associated with filename from cache or on disk

            Parameters:
                filename [Path] name of file to obtain contents from

            Returns:
                [str] cached contents if available or contents from disk
        '''
        try:
            if filename is None:
                __LOGGER__.info(
                    'No filename provided, returning the empty string'
                )
                return self.BLANK

            __LOGGER__.debug(
                'Attempting to fulfill request for %s from cache',
                filename.name
            )
            cached = self._cache[filename]

            if cached.is_expired():
                __LOGGER__.debug(
                    'Cache contained requested file %s, but is out of date',
                    filename.name
                )
                refreshed = await self._refresh(filename)
                self._update_cache(cached, refreshed)

            __LOGGER__.info(
                'Returning contents of %s',
                str(self._root / filename)
            )
            return cached.contents
        except KeyError:
            __LOGGER__.error(
                'Cache did not contain requested file: %s',
                str(self._root / filename)
            )
            __LOGGER__.debug(
                'Attempting to fulfill request for %s from disk',
                filename.name
            )
            contents_from_disk = await self._refresh(filename)
            new_cached = CachedContents(int(), str())
            self._cache[filename] = new_cached
            self._update_cache(new_cached, contents_from_disk)
            return contents_from_disk

    async def _refresh(self, file: Path) -> str:
        '''
            Coroutine for reading a file's contents

            Parameters:
                file [Path]: file (relative to self._root) to read

            Returns:
                [str]: file contents read

            Raises:
                [MissingMessageFormat] if file is not found or is a directory
        '''
        try:
            __LOGGER__.debug('Attempting to read %s from disk', str(file))
            async with aiofiles.open(self._root / file, mode='r') as f_in:
                return await f_in.read()
        except FileNotFoundError as err:
            __LOGGER__.error(
                'Cannot read %s because it does not exist on disk',
                str(file)
            )
            raise MissingMessageFormat(
                f'No such message format file on disk: {file}'
            ) from err

        except IsADirectoryError as err:
            __LOGGER__.error(
                'Cannot read %s because it is a directory',
                str(file)
            )
            raise MissingMessageFormat(
                f'Specified message format file is a directory: {file}'
            ) from err

    def _update_cache(
        self,
        caching: CachedContents,
        new_contents: str
    ) -> None:
        '''
            Updates the attributes of the given caching object

            Parameters:
                caching [CachedContents]: caching object to update
                new_contents [str]: new data to replace existing cache data

            Returns:
                None
        '''
        now = round(datetime.now(timezone.utc).timestamp())
        new_ttl = now + self._ttl
        __LOGGER__.debug(
            'New expiration time for cached content is: %d',
            new_ttl
        )
        caching.contents = new_contents
        caching.expires_at = new_ttl
        __LOGGER__.debug(
            'Updated the contents of the caching object'
        )
