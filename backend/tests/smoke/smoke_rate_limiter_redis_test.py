from limits.storage import storage_from_string


def test_redis_storage_backend_available() -> None:
    """
    Deployment guard: fail fast when Redis client dependency is missing.
    This catches slowapi/limits storage backend prerequisites.
    """
    storage = storage_from_string("redis://localhost:6379")
    assert storage is not None
