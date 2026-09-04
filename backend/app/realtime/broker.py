import json
import logging
from typing import Any

from redis import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


def channel_for_board(board_id: int) -> str:
    return f"teamflow:board:{board_id}"


def publish_board_event(board_id: int, event: dict[str, Any]) -> None:
    """Publish a best-effort event; persistence remains the source of truth."""
    client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
    try:
        client.publish(channel_for_board(board_id), json.dumps(event, ensure_ascii=False, default=str))
    except Exception:
        logger.warning("Realtime broker unavailable", exc_info=True)
    finally:
        client.close()
