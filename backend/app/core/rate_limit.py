"""Rate limiting configuration using slowapi.

The limiter instance is created here (not in main.py) to avoid circular imports,
since chat routes need to reference it via decorators.
"""

import json

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def _chat_rate_limit_key(request: Request) -> str:
    """Extract user_id from the JSON body for per-user rate limiting.

    Falls back to client IP if user_id is unavailable.
    """
    try:
        body = request._body  # populated by slowapi before the key function runs
        data = json.loads(body)
        user_id = data.get("user_id")
        if user_id:
            return str(user_id)
    except Exception:
        pass
    return get_remote_address(request)


limiter = Limiter(key_func=_chat_rate_limit_key)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                f"Rate limit exceeded: {exc.detail}. " "Please wait before sending more messages."
            )
        },
    )
