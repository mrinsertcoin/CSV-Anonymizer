import pytest

from anonymizer.crypto import pseudonymize


def test_deterministic_same_key():
    assert pseudonymize("alice@example.com", b"secret") == pseudonymize("alice@example.com", b"secret")


def test_different_keys_different_output():
    assert pseudonymize("alice@example.com", b"a") != pseudonymize("alice@example.com", b"b")


def test_prefix_and_length():
    out = pseudonymize("üñîçødë", b"secret", prefix="PID_", length=12)
    assert out.startswith("PID_")
    assert len(out) == 12


def test_none_passthrough():
    assert pseudonymize(None, b"secret") is None


def test_empty_key_rejected():
    with pytest.raises(ValueError):
        pseudonymize("x", b"")
