"""Tests for canonical key generation and versioning."""
from __future__ import annotations

import pytest

from app.rules.canonical import canonicalize, version
from app.rules.models import ObligationType


class TestCanonicalize:
    def test_basic_format(self):
        result = canonicalize("IN/companies-act-2013", None, ObligationType.FILING)
        assert result == "IN/companies-act-2013||filing"

    def test_with_section(self):
        result = canonicalize(
            "IN-KA/factories-rules-1969", "r.105", ObligationType.FILING
        )
        assert result == "IN-KA/factories-rules-1969|r.105|filing"

    def test_with_empty_section(self):
        result = canonicalize("IN/test", "", ObligationType.REGISTRATION)
        assert result == "IN/test||registration"

    def test_empty_instrument_id_raises(self):
        with pytest.raises(ValueError, match="instrument_id must be a non-empty string"):
            canonicalize("", None, ObligationType.FILING)

    def test_all_obligation_types(self):
        for ot in ObligationType:
            result = canonicalize("IN/test", None, ot)
            assert result == f"IN/test||{ot.value}"


class TestVersion:
    def test_first_commit(self):
        assert version(None) == "1"

    def test_increment(self):
        assert version("1") == "2"
        assert version("5") == "6"
        assert version("99") == "100"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            version("")

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            version("abc")

    def test_float_string_raises(self):
        with pytest.raises(ValueError):
            version("1.5")
