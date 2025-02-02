'''
    :module_name: test_filecache
    :module_summary: unit tests for the file cache module
    :module_author: CountTails
'''

import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from match_scheduler_bot.model.filecache import (
    FileCacheProvider,
    CachedContents
)

from freezegun import freeze_time


@pytest.fixture(scope='function')
def file_cache(tmp_path):
    return FileCacheProvider(
        tmp_path,
        15
    )


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
