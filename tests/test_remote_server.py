import pytest

from projects.remote_server import resolve_remote_relative, validate_fingerprint, validate_remote_root_path


def test_validate_remote_root_path_absolute():
    assert validate_remote_root_path("/var/www/app") == "/var/www/app"


def test_validate_remote_root_path_rejects_relative():
    with pytest.raises(ValueError):
        validate_remote_root_path("relative/path")


def test_resolve_remote_relative_blocks_traversal():
    root = "/var/www/app"
    assert resolve_remote_relative(root, "src/main.py") == "/var/www/app/src/main.py"
    with pytest.raises(ValueError):
        resolve_remote_relative(root, "../etc/passwd")


def test_resolve_remote_relative_absolute_when_allowed():
    root = "/var/www/app"
    assert (
        resolve_remote_relative(root, "/etc/nginx/nginx.conf", allow_server_wide=True)
        == "/etc/nginx/nginx.conf"
    )
    with pytest.raises(ValueError):
        resolve_remote_relative(root, "/etc/../etc/passwd", allow_server_wide=True)


def test_validate_fingerprint_format():
    assert validate_fingerprint("") == ""
    with pytest.raises(ValueError):
        validate_fingerprint("md5:deadbeef")
