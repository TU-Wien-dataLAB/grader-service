async def test_server_extension_loaded(jp_serverapp):
    """Test that the server extension loads without errors."""
    # Check that the extension is registered
    extensions = jp_serverapp.extension_manager.extensions
    assert "grader_labextension" in extensions

    # Check that handlers are registered
    handlers = jp_serverapp.web_app.default_router.rules
    assert len(handlers) > 0
