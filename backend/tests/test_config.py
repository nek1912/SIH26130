"""CORS origin configuration — env-driven allowlist for deployment."""
from __future__ import annotations

from app.core.config import get_settings, parse_cors_origins


class TestParseCorsOrigins:
    def test_default_origins_cover_local_dev(self):
        assert parse_cors_origins(get_settings().cors_allow_origins) == [
            "http://localhost:5173",
            "http://localhost:3000",
        ]

    def test_custom_origins_parsed(self):
        assert parse_cors_origins(
            "https://app.example.com, https://staff.example.com"
        ) == ["https://app.example.com", "https://staff.example.com"]

    def test_blank_entries_dropped(self):
        assert parse_cors_origins("https://a.example.com,, ,https://b.example.com") == [
            "https://a.example.com",
            "https://b.example.com",
        ]

    def test_empty_string_yields_empty_list(self):
        assert parse_cors_origins("") == []

    def test_env_override_is_honored(self, monkeypatch):
        monkeypatch.setenv(
            "CORS_ALLOW_ORIGINS", "https://prod.example.com"
        )
        from app.core.config import Settings

        assert Settings().cors_allow_origins == "https://prod.example.com"
        assert parse_cors_origins(Settings().cors_allow_origins) == [
            "https://prod.example.com"
        ]
