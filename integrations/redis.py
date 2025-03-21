from redis import Redis

from project_base.config import get_settings

settings = get_settings()

if settings.REDIS_URL is None:
    connection, connections = None, []
else:
    connection = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    connections = [connection]  # For closing connections in lifespan (main.py)
