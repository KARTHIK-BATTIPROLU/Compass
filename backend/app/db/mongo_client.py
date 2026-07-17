from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    client = get_client()
    # Database name from URI path, or default "edtech"
    settings = get_settings()
    db_name = "edtech"
    uri = settings.mongodb_uri
    if "/" in uri.rsplit("@", 1)[-1]:
        path = uri.rsplit("/", 1)[-1].split("?")[0]
        if path:
            db_name = path
    return client[db_name]


async def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
