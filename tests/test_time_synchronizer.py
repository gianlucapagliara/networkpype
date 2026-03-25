"""Tests for the TimeSynchronizer class."""

import asyncio

import pytest

from networkpype.time_synchronizer import TimeSynchronizer


def test_initialization():
    """Test TimeSynchronizer initializes with empty samples."""
    ts = TimeSynchronizer()
    assert len(ts._time_offset_ms) == 0


def test_initialization_custom_max_samples():
    """Test TimeSynchronizer with custom max_samples."""
    ts = TimeSynchronizer(max_samples=10)
    assert ts._time_offset_ms.maxlen == 10


def test_logger():
    """Test logger creation and caching."""
    TimeSynchronizer._logger = None
    logger = TimeSynchronizer.logger()
    assert logger is not None
    # Second call returns cached logger
    assert TimeSynchronizer.logger() is logger


def test_add_time_offset_ms_sample():
    """Test adding time offset samples."""
    ts = TimeSynchronizer(max_samples=3)
    ts.add_time_offset_ms_sample(100.0)
    ts.add_time_offset_ms_sample(200.0)
    assert len(ts._time_offset_ms) == 2
    assert list(ts._time_offset_ms) == [100.0, 200.0]


def test_add_time_offset_ms_sample_rolling_window():
    """Test that samples roll off when exceeding max_samples."""
    ts = TimeSynchronizer(max_samples=2)
    ts.add_time_offset_ms_sample(100.0)
    ts.add_time_offset_ms_sample(200.0)
    ts.add_time_offset_ms_sample(300.0)
    assert len(ts._time_offset_ms) == 2
    assert list(ts._time_offset_ms) == [200.0, 300.0]


def test_clear_time_offset_ms_samples():
    """Test clearing all samples."""
    ts = TimeSynchronizer()
    ts.add_time_offset_ms_sample(100.0)
    ts.add_time_offset_ms_sample(200.0)
    ts.clear_time_offset_ms_samples()
    assert len(ts._time_offset_ms) == 0


def test_time_offset_ms_no_samples():
    """Test time_offset_ms with no samples falls back to system time diff."""
    ts = TimeSynchronizer()
    offset = ts.time_offset_ms
    # Should return a finite number (difference between time.time() and perf_counter)
    assert isinstance(offset, float)


def test_time_offset_ms_with_single_sample():
    """Test time_offset_ms with a single sample."""
    ts = TimeSynchronizer()
    ts.add_time_offset_ms_sample(500.0)
    offset = ts.time_offset_ms
    # With a single sample, median == weighted_average == 500.0
    assert offset == 500.0


def test_time_offset_ms_with_multiple_samples():
    """Test time_offset_ms with multiple samples uses median/weighted average."""
    ts = TimeSynchronizer(max_samples=5)
    ts.add_time_offset_ms_sample(100.0)
    ts.add_time_offset_ms_sample(200.0)
    ts.add_time_offset_ms_sample(300.0)
    offset = ts.time_offset_ms
    assert isinstance(offset, float)
    # Should be somewhere around 200 (median=200, weighted avg biased toward 300)
    assert 150.0 < offset < 350.0


def test_time_returns_synchronized_time():
    """Test time() returns perf_counter + offset."""
    ts = TimeSynchronizer()
    ts.add_time_offset_ms_sample(1000.0)  # 1 second offset
    t = ts.time()
    assert isinstance(t, float)
    assert t > 0


@pytest.mark.asyncio
async def test_update_server_time_offset_with_time_provider():
    """Test updating time offset with a time provider."""
    ts = TimeSynchronizer()

    # Create a coroutine that returns a server time in ms
    async def get_server_time():
        return ts._current_seconds_counter() * 1e3 + 500.0  # 500ms offset

    await ts.update_server_time_offset_with_time_provider(get_server_time())
    assert len(ts._time_offset_ms) == 1
    # The offset should be approximately 500ms
    assert abs(ts._time_offset_ms[0] - 500.0) < 50.0


@pytest.mark.asyncio
async def test_update_server_time_offset_error_handling():
    """Test that errors from the time provider are handled gracefully."""
    ts = TimeSynchronizer()

    async def failing_provider():
        raise ValueError("Server error")

    await ts.update_server_time_offset_with_time_provider(failing_provider())
    # Should not add any sample on error
    assert len(ts._time_offset_ms) == 0


@pytest.mark.asyncio
async def test_update_server_time_offset_cancelled_error():
    """Test that CancelledError is re-raised."""
    ts = TimeSynchronizer()

    async def cancelled_provider():
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await ts.update_server_time_offset_with_time_provider(cancelled_provider())


@pytest.mark.asyncio
async def test_update_server_time_if_not_initialized_empty():
    """Test update_server_time_if_not_initialized when no samples exist."""
    ts = TimeSynchronizer()

    async def get_server_time():
        return ts._current_seconds_counter() * 1e3 + 100.0

    await ts.update_server_time_if_not_initialized(get_server_time())
    assert len(ts._time_offset_ms) == 1


@pytest.mark.asyncio
async def test_update_server_time_if_not_initialized_already_initialized():
    """Test update_server_time_if_not_initialized skips when samples exist."""
    ts = TimeSynchronizer()
    ts.add_time_offset_ms_sample(500.0)

    async def get_server_time():
        return ts._current_seconds_counter() * 1e3 + 100.0

    await ts.update_server_time_if_not_initialized(get_server_time())
    # Should still have only 1 sample (the original one)
    assert len(ts._time_offset_ms) == 1
    assert ts._time_offset_ms[0] == 500.0


@pytest.mark.asyncio
async def test_update_server_time_if_not_initialized_closes_coroutine():
    """Test that an unused coroutine is closed when already initialized."""
    ts = TimeSynchronizer()
    ts.add_time_offset_ms_sample(500.0)

    called = False

    async def get_server_time():
        nonlocal called
        called = True
        return 1000.0

    await ts.update_server_time_if_not_initialized(get_server_time())
    assert not called
    assert len(ts._time_offset_ms) == 1
    assert ts._time_offset_ms[0] == 500.0


@pytest.mark.asyncio
async def test_update_server_time_if_not_initialized_lock_prevents_concurrent():
    """Test that the lock prevents concurrent callers from all triggering the provider."""
    ts = TimeSynchronizer()
    call_count = 0

    async def get_server_time():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)  # Simulate network delay
        return ts._current_seconds_counter() * 1e3 + 100.0

    # Launch multiple concurrent calls
    await asyncio.gather(
        ts.update_server_time_if_not_initialized(get_server_time()),
        ts.update_server_time_if_not_initialized(get_server_time()),
        ts.update_server_time_if_not_initialized(get_server_time()),
    )

    # Only one should have actually called the provider
    assert call_count == 1
    assert len(ts._time_offset_ms) == 1


@pytest.mark.asyncio
async def test_update_server_time_if_not_initialized_cleanup_on_cancellation():
    """Test that coroutine is cleaned up if cancelled while waiting for lock."""
    ts = TimeSynchronizer()

    async def slow_provider():
        await asyncio.sleep(10)
        return 1000.0

    async def get_server_time():
        return ts._current_seconds_counter() * 1e3 + 100.0

    # Start a first call that holds the lock for a while
    task1 = asyncio.create_task(
        ts.update_server_time_if_not_initialized(slow_provider())
    )
    await asyncio.sleep(0)  # Let task1 acquire the lock

    # Start a second call that will wait on the lock
    task2 = asyncio.create_task(
        ts.update_server_time_if_not_initialized(get_server_time())
    )
    await asyncio.sleep(0)  # Let task2 start waiting

    # Cancel task2 while it's waiting for the lock
    task2.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task2

    # Clean up task1
    task1.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task1
