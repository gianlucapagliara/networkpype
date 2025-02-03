"""Tests for the rate limiter."""

import asyncio
from decimal import Decimal

import pytest

from networkpype.throttler.rate_limit import LinkedLimitWeightPair, RateLimit
from networkpype.throttler.throttler import AsyncThrottler


@pytest.fixture
def basic_rate_limits() -> list[RateLimit]:
    """Create basic rate limits for testing."""
    return [
        RateLimit(
            limit_id="per_second",
            limit=10,
            time_interval=1.0,
        ),
        RateLimit(
            limit_id="per_minute",
            limit=100,
            time_interval=60.0,
        ),
    ]


@pytest.fixture
def linked_rate_limits() -> list[RateLimit]:
    """Create rate limits with linked limits for testing."""
    return [
        RateLimit(
            limit_id="endpoint",
            limit=10,
            time_interval=1.0,
            linked_limits=[LinkedLimitWeightPair(limit_id="global", weight=2)],
        ),
        RateLimit(
            limit_id="global",
            limit=100,
            time_interval=60.0,
        ),
    ]


def test_throttler_initialization(basic_rate_limits: list[RateLimit]) -> None:
    """Test AsyncThrottler initialization with various configurations."""
    # Test basic initialization
    throttler = AsyncThrottler(rate_limits=basic_rate_limits)
    assert len(throttler.rate_limits) == 2
    assert throttler.limits_share_percentage == Decimal("100")

    # Test with custom share percentage
    throttler = AsyncThrottler(
        rate_limits=basic_rate_limits, limits_share_percentage=Decimal("50")
    )
    assert throttler.limits_share_percentage == Decimal("50")
    # Check that limits are adjusted
    assert throttler.rate_limits[0].limit == 5  # 10 * 50%
    assert throttler.rate_limits[1].limit == 50  # 100 * 50%

    # Test with custom retry interval and safety margin
    throttler = AsyncThrottler(
        rate_limits=basic_rate_limits,
        retry_interval=0.5,
        safety_margin_pct=0.1,
    )
    assert throttler._retry_interval == 0.5
    assert throttler._safety_margin_pct == 0.1


def test_throttler_copy(basic_rate_limits: list[RateLimit]) -> None:
    """Test the copy method of AsyncThrottler."""
    original = AsyncThrottler(
        rate_limits=basic_rate_limits,
        retry_interval=0.5,
        safety_margin_pct=0.1,
        limits_share_percentage=Decimal("50"),
    )
    copy = original.copy()

    assert copy is not original
    assert copy.limits_share_percentage == original.limits_share_percentage
    assert copy._retry_interval == original._retry_interval
    assert copy._safety_margin_pct == original._safety_margin_pct
    assert len(copy.rate_limits) == len(original.rate_limits)


def test_get_related_limits(linked_rate_limits: list[RateLimit]) -> None:
    """Test retrieving related rate limits."""
    throttler = AsyncThrottler(rate_limits=linked_rate_limits)

    # Test getting existing limit with linked limits
    limit, related = throttler.get_related_limits("endpoint")
    assert limit is not None
    assert limit.limit_id == "endpoint"
    assert len(related) == 2  # endpoint itself + global
    assert any(r[0].limit_id == "global" and r[1] == 2 for r in related)

    # Test getting limit without linked limits
    limit, related = throttler.get_related_limits("global")
    assert limit is not None
    assert limit.limit_id == "global"
    assert len(related) == 1  # only global itself
    assert related[0][0].limit_id == "global"

    # Test getting non-existent limit
    limit, related = throttler.get_related_limits("nonexistent")
    assert limit is None
    assert len(related) == 0


@pytest.mark.asyncio
async def test_throttler_execute_task(basic_rate_limits: list[RateLimit]) -> None:
    """Test executing tasks with rate limiting."""
    throttler = AsyncThrottler(rate_limits=basic_rate_limits)

    # Test executing a single task
    async with throttler.execute_task("per_second"):
        # Each task creates one log per limit
        assert len(throttler._task_logs) == 1


@pytest.mark.asyncio
async def test_throttler_with_linked_limits(
    linked_rate_limits: list[RateLimit],
) -> None:
    """Test rate limiting with linked limits."""
    throttler = AsyncThrottler(rate_limits=linked_rate_limits)

    # Execute tasks that affect both endpoint and global limits
    tasks = []
    for _ in range(5):  # Each task counts as 2 against global limit
        tasks.append(asyncio.create_task(execute_dummy_task(throttler, "endpoint")))
    await asyncio.gather(*tasks)

    # Check task logs
    endpoint_logs = [
        log for log in throttler._task_logs if log.rate_limit.limit_id == "endpoint"
    ]
    global_logs = [
        log for log in throttler._task_logs if log.rate_limit.limit_id == "global"
    ]
    # Each task creates one log for endpoint and one for global
    assert len(endpoint_logs) == 5
    assert len(global_logs) == 5


@pytest.mark.asyncio
async def test_invalid_limit_id(basic_rate_limits: list[RateLimit]) -> None:
    """Test behavior with invalid limit IDs."""
    throttler = AsyncThrottler(rate_limits=basic_rate_limits)

    with pytest.raises(ValueError, match="Rate limit not found for ID: invalid"):
        async with throttler.execute_task("invalid"):
            pass


async def execute_dummy_task(throttler: AsyncThrottler, limit_id: str) -> None:
    """Helper function to execute a dummy task."""
    async with throttler.execute_task(limit_id):
        await asyncio.sleep(0.01)  # Simulate some work
