"""
Redis cache layer for TaskHub.
Caches GET /projects/{id}/tasks responses with automatic invalidation.
"""
import hashlib
import json
import logging
from typing import Optional

from app.core.redis import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)

CACHE_PREFIX = "taskhub:project"


def _build_cache_key(project_id: int, query_params: dict) -> str:
    """Build a deterministic cache key from project ID and query parameters."""
    # Sort params to ensure consistent key regardless of param order
    sorted_params = json.dumps(query_params, sort_keys=True, default=str)
    param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
    return f"{CACHE_PREFIX}:{project_id}:tasks:{param_hash}"


def _build_invalidation_pattern(project_id: int) -> str:
    """Build pattern to match all cache keys for a given project."""
    return f"{CACHE_PREFIX}:{project_id}:tasks:*"


async def get_task_cache(project_id: int, query_params: dict) -> Optional[str]:
    """Get cached task list response from Redis."""
    try:
        redis = await get_redis()
        key = _build_cache_key(project_id, query_params)
        cached = await redis.get(key)
        if cached:
            logger.info(f"Cache HIT for project {project_id}")
        else:
            logger.info(f"Cache MISS for project {project_id}")
        return cached
    except Exception as e:
        logger.warning(f"Redis cache get failed: {e}")
        return None


async def set_task_cache(project_id: int, query_params: dict, data: str) -> None:
    """Store task list response in Redis cache with TTL."""
    try:
        redis = await get_redis()
        key = _build_cache_key(project_id, query_params)
        await redis.set(key, data, ex=settings.CACHE_TTL_SECONDS)
        logger.info(f"Cache SET for project {project_id} (TTL={settings.CACHE_TTL_SECONDS}s)")
    except Exception as e:
        logger.warning(f"Redis cache set failed: {e}")


async def invalidate_task_cache(project_id: int) -> None:
    """Invalidate all cached task responses for a given project."""
    try:
        redis = await get_redis()
        pattern = _build_invalidation_pattern(project_id)
        cursor = 0
        deleted_count = 0
        while True:
            cursor, keys = await redis.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await redis.delete(*keys)
                deleted_count += len(keys)
            if cursor == 0:
                break
        if deleted_count > 0:
            logger.info(f"Cache INVALIDATED {deleted_count} keys for project {project_id}")
    except Exception as e:
        logger.warning(f"Redis cache invalidation failed: {e}")
