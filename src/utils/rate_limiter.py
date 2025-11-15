"""Rate limiting utilities to prevent abuse and DoS attacks.

This module provides rate limiting functionality for API calls and user actions
to prevent abuse and ensure fair resource usage.
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        max_requests: Maximum number of requests allowed
        time_window: Time window in seconds
        identifier: Identifier for this rate limit (e.g., "ollama_api", "conversation")
    """
    max_requests: int
    time_window: int
    identifier: str


class RateLimiter:
    """Token bucket rate limiter for controlling request rates.

    This implements a sliding window rate limiter to prevent abuse
    and ensure fair resource usage.
    """

    def __init__(self):
        """Initialize rate limiter with empty tracking."""
        # Track requests per identifier
        self._requests: dict[str, deque] = defaultdict(deque)
        # Track violations per identifier
        self._violations: dict[str, int] = defaultdict(int)
        # Lock times for identifiers that exceeded limits
        self._locked_until: dict[str, datetime] = {}

    def is_allowed(
        self,
        identifier: str,
        config: RateLimitConfig,
        session_id: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """Check if a request is allowed under the rate limit.

        Args:
            identifier: Unique identifier for the requester (e.g., session_id, user_id)
            config: Rate limit configuration
            session_id: Optional session ID for more granular tracking

        Returns:
            Tuple of (is_allowed: bool, error_message: Optional[str])

        Security:
            - Prevents DoS attacks via rate limiting
            - Tracks violations and implements progressive penalties
            - Uses sliding window for accurate rate limiting
        """
        key = f"{config.identifier}:{identifier}"
        if session_id:
            key = f"{key}:{session_id}"

        current_time = time.time()

        # Check if currently locked due to violations
        if key in self._locked_until:
            lock_time = self._locked_until[key]
            if datetime.now() < lock_time:
                remaining = (lock_time - datetime.now()).seconds
                return False, f"Rate limit exceeded. Locked for {remaining} more seconds."
            else:
                # Lock expired, remove it and reset violations
                del self._locked_until[key]
                self._violations[key] = 0

        # Get request history for this key
        request_times = self._requests[key]

        # Remove requests outside the time window
        cutoff_time = current_time - config.time_window
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()

        # Check if limit exceeded
        if len(request_times) >= config.max_requests:
            # Record violation
            self._violations[key] += 1

            # Implement progressive penalties
            if self._violations[key] >= 3:
                # Lock for increasing duration based on violations
                lock_duration = min(300, 60 * self._violations[key])  # Max 5 minutes
                self._locked_until[key] = datetime.now() + timedelta(seconds=lock_duration)
                return False, f"Too many rate limit violations. Locked for {lock_duration} seconds."

            wait_time = int(request_times[0] + config.time_window - current_time) + 1
            return False, f"Rate limit exceeded. Please wait {wait_time} seconds."

        # Request is allowed, add to tracking
        request_times.append(current_time)
        return True, None

    def reset(self, identifier: str, config: RateLimitConfig) -> None:
        """Reset rate limit tracking for an identifier.

        Args:
            identifier: Identifier to reset
            config: Rate limit configuration
        """
        key = f"{config.identifier}:{identifier}"
        if key in self._requests:
            del self._requests[key]
        if key in self._violations:
            del self._violations[key]
        if key in self._locked_until:
            del self._locked_until[key]

    def get_remaining(
        self,
        identifier: str,
        config: RateLimitConfig,
        session_id: Optional[str] = None
    ) -> int:
        """Get number of remaining requests allowed.

        Args:
            identifier: Unique identifier for the requester
            config: Rate limit configuration
            session_id: Optional session ID

        Returns:
            Number of requests remaining in current window
        """
        key = f"{config.identifier}:{identifier}"
        if session_id:
            key = f"{key}:{session_id}"

        current_time = time.time()
        request_times = self._requests[key]

        # Remove old requests
        cutoff_time = current_time - config.time_window
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()

        return max(0, config.max_requests - len(request_times))


# Global rate limiter instance
_global_limiter = RateLimiter()


# Predefined rate limit configurations
RATE_LIMITS = {
    "ollama_api": RateLimitConfig(
        max_requests=30,  # 30 requests
        time_window=60,   # per minute
        identifier="ollama_api"
    ),
    "conversation_turn": RateLimitConfig(
        max_requests=100,  # 100 turns
        time_window=300,   # per 5 minutes
        identifier="conversation_turn"
    ),
    "manual_message": RateLimitConfig(
        max_requests=20,   # 20 messages
        time_window=60,    # per minute
        identifier="manual_message"
    ),
    "auto_run": RateLimitConfig(
        max_requests=1000, # 1000 turns
        time_window=3600,  # per hour
        identifier="auto_run"
    ),
}


def check_rate_limit(
    limit_type: str,
    identifier: str,
    session_id: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """Check if request is within rate limit.

    Args:
        limit_type: Type of rate limit to check (key in RATE_LIMITS)
        identifier: Unique identifier for requester
        session_id: Optional session ID

    Returns:
        Tuple of (is_allowed, error_message)

    Example:
        allowed, error = check_rate_limit("ollama_api", "user123", "session456")
        if not allowed:
            print(error)
    """
    if limit_type not in RATE_LIMITS:
        return True, None  # No limit configured

    config = RATE_LIMITS[limit_type]
    return _global_limiter.is_allowed(identifier, config, session_id)


def get_remaining_quota(
    limit_type: str,
    identifier: str,
    session_id: Optional[str] = None
) -> int:
    """Get remaining quota for a rate limit.

    Args:
        limit_type: Type of rate limit
        identifier: Unique identifier
        session_id: Optional session ID

    Returns:
        Number of remaining requests
    """
    if limit_type not in RATE_LIMITS:
        return -1  # Unlimited

    config = RATE_LIMITS[limit_type]
    return _global_limiter.get_remaining(identifier, config, session_id)


def reset_rate_limit(limit_type: str, identifier: str) -> None:
    """Reset rate limit for an identifier.

    Args:
        limit_type: Type of rate limit
        identifier: Identifier to reset
    """
    if limit_type in RATE_LIMITS:
        config = RATE_LIMITS[limit_type]
        _global_limiter.reset(identifier, config)
