"""
Redis Queue (RQ) and Redis connection management.
"""

import redis
from rq import Queue

from app.core.config import get_settings

settings = get_settings()

# Global Redis connection and queue
_redis_conn = None
_rq_queue = None

def get_redis_connection() -> redis.Redis:
    """
    Get a singleton Redis connection.
    """
    global _redis_conn
    if _redis_conn is None:
        _redis_conn = redis.from_url(f'redis://{settings.redis_host}:{settings.redis_port}')
    return _redis_conn

def get_queue() -> Queue:
    """
    Get a singleton RQ Queue instance.
    """
    global _rq_queue
    if _rq_queue is None:
        conn = get_redis_connection()
        _rq_queue = Queue(connection=conn)
    return _rq_queue
