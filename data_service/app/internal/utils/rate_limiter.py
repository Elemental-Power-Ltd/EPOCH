"""
Rate limiter for slow 3rd party APIs.

This is especially useful for Octopus, where we need a long lasting async rate limiter.
"""

import asyncio
import datetime


class RateLimiter:
    """
    Simple rate limiter for async requests using token bucket algorithm.

    This class implements a token bucket algorithm to control the rate of API requests.
    Tokens are added to the bucket based on time elapsed since the last request,
    and each request consumes one token. If no tokens are available, the limiter
    will cause the caller to wait until a token becomes available.
    Where you're performing batched request to an endpoint, prefer `aiometer.amap`
    but this will do for single requests in functions that are called regularly.

    Attributes
    ----------
    rate_limit : int
        Maximum number of tokens in the bucket.
    period : float
        Time period in seconds for the rate limit.
    tokens : float
        Current number of tokens available.
    updated_at : datetime.datetime
        Timestamp of the last token update.
    lock : asyncio.Lock
        Lock to ensure thread-safety in async environment.
    """

    def __init__(
        self, rate_limit_requests: int = 5, rate_limit_period: datetime.timedelta = datetime.timedelta(seconds=1.0)
    ) -> None:
        """
        Create a rate limiter, starting the timer and filling the token pool.

        Parameters
        ----------
        rate_limit_requests : int
            Maximum number of requests allowed in the rate limit period.
        rate_limit_period : float
            Time period in seconds for the rate limit.
        """
        self.rate_limit = rate_limit_requests
        self.period = rate_limit_period
        self.tokens = float(rate_limit_requests)
        self.updated_at = datetime.datetime.now(datetime.UTC)
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire a token for making a request, waiting if necessary.

        This method attempts to acquire a token from the bucket. If tokens are
        available, it decrements the count and returns immediately. If no tokens
        are available, it calculates the appropriate wait time and sleeps until
        a token becomes available.

        """
        async with self.lock:
            now = datetime.datetime.now(datetime.UTC)
            time_passed = now - self.updated_at
            self.updated_at = now

            # Add tokens based on time passed
            self.tokens = min(self.rate_limit, self.tokens + self.rate_limit * (time_passed / self.period))

            # If we don't have at least 1 token, wait
            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (self.period / self.rate_limit)
                await asyncio.sleep(wait_time.total_seconds())
                self.tokens = 1
                self.updated_at = datetime.datetime.now(datetime.UTC)

            # Consume one token
            self.tokens -= 1
