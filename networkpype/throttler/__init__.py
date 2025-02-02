"""Rate limiting functionality for API request throttling.

This package provides a comprehensive solution for managing API rate limits in
asynchronous applications. It supports complex rate limiting scenarios including
multiple concurrent limits, weighted requests, and linked limits.

Key Components:
    AsyncThrottler: Main class for managing rate limits and executing requests.
    RateLimit: Configuration class for defining rate limit rules.
    LinkedLimitWeightPair: Class for linking rate limits with weights.
    TaskLog: Class for tracking rate limit consumption.

Example:
    ```python
    from networkpype.throttler import AsyncThrottler, RateLimit

    # Create a throttler with multiple rate limits
    throttler = AsyncThrottler(
        rate_limits=[
            RateLimit(
                limit_id="endpoint",
                limit=100,
                time_interval=60.0,  # 100 requests per minute
                weight=1
            ),
            RateLimit(
                limit_id="global",
                limit=1000,
                time_interval=3600.0,  # 1000 requests per hour
                weight=1
            )
        ],
        safety_margin_pct=0.05  # 5% safety margin
    )

    # Use the throttler to execute rate-limited tasks
    async with throttler.execute_task("endpoint"):
        await make_api_request()
    ```
"""
