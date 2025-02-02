'''
    :module_name: test_filecache
    :module_summary: unit tests for the file cache module
    :module_author: CountTails
'''

import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from pathlib import Path

from match_scheduler_bot.exceptions import MissingMessageFormat
from match_scheduler_bot.model.filecache import (
    FileCacheProvider,
    CachedContents
)

from freezegun import freeze_time


@pytest.fixture(scope='function')
def file_cache(tmp_path):
    cache = FileCacheProvider(
        tmp_path,
        900
    )

    cache._cache = {
        Path('message1.txt'): CachedContents(
            round(datetime(
                2025,
                1,
                31,
                12,
                30,
                tzinfo=timezone.utc
            ).timestamp()),
            'Hello world\n'
        ),
        Path('message2.txt'): CachedContents(
            round(datetime(
                2025,
                1,
                31,
                12,
                tzinfo=timezone.utc
            ).timestamp()),
            'This is an important message.\nIt needs to remain up to date.'
        )
    }

    with open(tmp_path / Path('message1.txt'), mode='w') as f:
        f.write("Hello world\n")

    with open(tmp_path / Path('message2.txt'), mode='w') as f:
        f.write(
            'The important message has been updated.\nPlease update the cache.'
        )

    with open(tmp_path / Path('message3.txt'), mode='w') as f:
        f.write(
            'The contents of this file have not been cached.'
        )

    return cache


@pytest.mark.parametrize(
    ["expire", "stuff"],
    [
        (5, "Hello world\n"),
        (50, "Lorem ipsum odor amet"),
        (500, '')
    ]
)
def test_caching_container_attributes(expire, stuff):
    cached = CachedContents(expire, stuff)

    assert cached.expires_at == expire
    assert cached.contents == stuff


@freeze_time('2025-01-31 12:15:00')
@pytest.mark.parametrize(
    ["offset", "expired"],
    [
        (-timedelta(minutes=15), True),
        (timedelta(minutes=15), False)
    ]
)
def test_caching_container_expiration_check(offset, expired):
    now = datetime.now(timezone.utc)
    expires_at = now + offset
    cached = CachedContents(round(expires_at.timestamp()), str())

    assert cached.is_expired() is expired


@freeze_time('2025-01-31 12:15:00')
@pytest.mark.asyncio
async def test_file_cache_retrieve_with_no_filename(file_cache):
    assert file_cache.BLANK == await file_cache.get_text()


@freeze_time('2025-01-31 12:15:00')
@pytest.mark.asyncio
async def test_file_cache_retrieve_from_cache(file_cache):
    caching_record = file_cache._cache[Path('message1.txt')]
    precall_timestamp = caching_record.expires_at
    precall_contents = caching_record.contents

    cached_contents = await file_cache.get_text(Path('message1.txt'))

    assert cached_contents == precall_contents
    assert caching_record.expires_at == precall_timestamp
    assert caching_record.contents == precall_contents


@freeze_time('2025-01-31 12:15:00')
@pytest.mark.asyncio
async def test_file_cache_retrieve_from_refresh(file_cache):
    caching_record = file_cache._cache[Path('message2.txt')]
    precall_timestamp = caching_record.expires_at
    precall_contents = caching_record.contents

    cached_contents = await file_cache.get_text(Path('message2.txt'))

    assert caching_record.expires_at != precall_timestamp
    assert caching_record.contents != precall_contents
    assert cached_contents != precall_contents


@freeze_time('2025-01-31 12:15:00')
@pytest.mark.asyncio
async def test_file_cache_retrieve_from_disk(file_cache):
    precall_caching_record = file_cache._cache.get(Path('message3.txt'))
    cached_contents = await file_cache.get_text(Path('message3.txt'))
    postcall_caching_record = file_cache._cache.get(Path('message3.txt'))

    assert precall_caching_record is None
    assert postcall_caching_record is not None and \
        isinstance(postcall_caching_record, CachedContents)
    assert len(cached_contents) > 0


@freeze_time('2025-01-31 12:15:00')
@pytest.mark.asyncio
async def test_file_cache_response_to_filesystem_failures(file_cache):
    with pytest.raises(MissingMessageFormat):
        await file_cache.get_text(Path('.'))

    with pytest.raises(MissingMessageFormat):
        await file_cache.get_text(Path('message4.txt'))
