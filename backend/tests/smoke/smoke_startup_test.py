def test_app_import_startup_contract() -> None:
    """
    Deployment gate: fail fast on import-time regressions.
    This catches startup issues like missing MCP client exports.
    """
    from app.main import app  # noqa: F401

    assert app is not None
