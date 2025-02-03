"""Tests for rate limit classes in the throttler module."""

import time

from networkpype.throttler.rate_limit import LinkedLimitWeightPair, RateLimit, TaskLog


def test_linked_limit_weight_pair_creation() -> None:
    """Test creation of LinkedLimitWeightPair with default and custom weights."""
    # Test with default weight
    pair = LinkedLimitWeightPair(limit_id="test_limit")
    assert pair.limit_id == "test_limit"
    assert pair.weight == 1

    # Test with custom weight
    pair = LinkedLimitWeightPair(limit_id="test_limit", weight=2)
    assert pair.limit_id == "test_limit"
    assert pair.weight == 2


def test_rate_limit_creation() -> None:
    """Test creation of RateLimit with various configurations."""
    # Test basic rate limit
    limit = RateLimit(limit_id="test", limit=100, time_interval=60.0)
    assert limit.limit_id == "test"
    assert limit.limit == 100
    assert limit.time_interval == 60.0
    assert limit.weight == 1
    assert limit.linked_limits == []

    # Test rate limit with custom weight and linked limits
    linked_limit = LinkedLimitWeightPair(limit_id="global", weight=2)
    limit = RateLimit(
        limit_id="test",
        limit=100,
        time_interval=60.0,
        weight=3,
        linked_limits=[linked_limit],
    )
    assert limit.weight == 3
    assert len(limit.linked_limits) == 1
    assert limit.linked_limits[0].limit_id == "global"
    assert limit.linked_limits[0].weight == 2


def test_rate_limit_repr() -> None:
    """Test string representation of RateLimit."""
    limit = RateLimit(
        limit_id="test",
        limit=100,
        time_interval=60.0,
        linked_limits=[LinkedLimitWeightPair("global", 2)],
    )
    repr_str = str(limit)
    assert "limit_id: test" in repr_str
    assert "limit: 100" in repr_str
    assert "time interval: 60.0" in repr_str
    assert "weight: 1" in repr_str
    assert "linked_limits: [LinkedLimitWeightPair" in repr_str


def test_task_log_creation() -> None:
    """Test creation of TaskLog entries."""
    rate_limit = RateLimit(limit_id="test", limit=100, time_interval=60.0)
    timestamp = time.time()

    # Test with default weight
    log = TaskLog(timestamp=timestamp, rate_limit=rate_limit)
    assert log.timestamp == timestamp
    assert log.rate_limit == rate_limit
    assert log.weight == 1

    # Test with custom weight
    log = TaskLog(timestamp=timestamp, rate_limit=rate_limit, weight=2)
    assert log.weight == 2


def test_rate_limit_filter() -> None:
    """Test filtering rate limits by ID."""
    limits = [
        RateLimit(limit_id="test1", limit=100, time_interval=60.0),
        RateLimit(limit_id="test2", limit=200, time_interval=60.0),
        RateLimit(limit_id="test3", limit=300, time_interval=60.0),
    ]

    # Filter single limit
    filtered = RateLimit.filter_rate_limits_list(limits, ["test1"])
    assert len(filtered) == 2
    assert all(limit.limit_id != "test1" for limit in filtered)

    # Filter multiple limits
    filtered = RateLimit.filter_rate_limits_list(limits, ["test1", "test2"])
    assert len(filtered) == 1
    assert filtered[0].limit_id == "test3"

    # Filter non-existent limit
    filtered = RateLimit.filter_rate_limits_list(limits, ["nonexistent"])
    assert len(filtered) == 3

    # Filter all limits
    filtered = RateLimit.filter_rate_limits_list(limits, ["test1", "test2", "test3"])
    assert len(filtered) == 0
