"""Tests for the TimeSynchronizerRESTPreProcessor class."""

import pytest

from networkpype.rest.method import RESTMethod
from networkpype.rest.processor.time_synchronizer import (
    TimeSynchronizerRESTPreProcessor,
)
from networkpype.rest.request import RESTRequest
from networkpype.time_synchronizer import TimeSynchronizer


@pytest.mark.asyncio
async def test_pre_process_initializes_time():
    """Test that pre_process calls update_server_time_if_not_initialized."""
    ts = TimeSynchronizer()

    async def time_provider():
        return ts._current_seconds_counter() * 1e3 + 100.0

    processor = TimeSynchronizerRESTPreProcessor(
        synchronizer=ts,
        time_provider=time_provider,
    )

    request = RESTRequest(method=RESTMethod.GET, url="https://example.com/data")
    result = await processor.pre_process(request)

    assert result is request
    # Should have added a time offset sample
    assert len(ts._time_offset_ms) == 1


@pytest.mark.asyncio
async def test_pre_process_skips_if_already_initialized():
    """Test that pre_process skips update if already initialized."""
    ts = TimeSynchronizer()
    ts.add_time_offset_ms_sample(500.0)

    call_count = 0

    async def time_provider():
        nonlocal call_count
        call_count += 1
        return ts._current_seconds_counter() * 1e3

    processor = TimeSynchronizerRESTPreProcessor(
        synchronizer=ts,
        time_provider=time_provider,
    )

    request = RESTRequest(method=RESTMethod.GET, url="https://example.com/data")
    await processor.pre_process(request)

    # Should still have only the original sample
    assert len(ts._time_offset_ms) == 1
    assert ts._time_offset_ms[0] == 500.0


@pytest.mark.asyncio
async def test_pre_process_returns_request_unchanged():
    """Test that the request is passed through unchanged."""
    ts = TimeSynchronizer()

    async def time_provider():
        return ts._current_seconds_counter() * 1e3

    processor = TimeSynchronizerRESTPreProcessor(
        synchronizer=ts,
        time_provider=time_provider,
    )

    request = RESTRequest(
        method=RESTMethod.GET,
        url="https://example.com/data",
        headers={"X-Custom": "value"},
    )
    result = await processor.pre_process(request)

    assert result.url == "https://example.com/data"
    assert result.headers == {"X-Custom": "value"}
