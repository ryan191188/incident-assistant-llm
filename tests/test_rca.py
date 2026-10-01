from rca.context_builder import context_hash, redact


def test_redact_masks_common_secrets():
    text = "key AKIAABCDEFGHIJKLMNOP token=abc123 slack xoxb-123-456"
    redacted = redact(text)
    assert "AKIA" not in redacted
    assert "abc123" not in redacted
    assert "xoxb" not in redacted


def test_context_hash_is_order_independent():
    assert context_hash({"a": 1, "b": 2}) == context_hash({"b": 2, "a": 1})
