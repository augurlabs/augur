"""Defines the redis connection."""
import redis
from augur.tasks.init import get_redis_conn_values


def get_redis_connection():
    global redis_connection

    # Only load the redis connection values once
    if "redis_connection" not in globals():
        redis_db_number, redis_conn_string = get_redis_conn_values()
        redis_connection = redis.from_url(f'{redis_conn_string}{redis_db_number+2}', decode_responses=True)

    return redis_connection
