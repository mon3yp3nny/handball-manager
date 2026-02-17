"""Rate limiting configuration using slowapi.

Import `limiter` and apply decorators to endpoints::

    from app.core.rate_limit import limiter

    @router.post("/login")
    @limiter.limit("5/minute")
    def login(request: Request, ...):
        ...
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
