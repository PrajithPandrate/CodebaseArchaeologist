from ..services.redaction import redact_secrets


def test_api_key_redacted():
    code = 'api_key = "sk-live-abc123def456789012345678"'
    result = redact_secrets(code)
    assert "sk-live-abc123" not in result
    assert "REDACTED" in result


def test_password_redacted():
    code = 'password = "supersecret123"'
    result = redact_secrets(code)
    assert "supersecret123" not in result


def test_aws_key_redacted():
    code = "AKIAIOSFODNN7EXAMPLE"
    result = redact_secrets(code)
    assert "AKIAIOSFODNN7EXAMPLE" not in result
    assert "AWS_KEY" in result


def test_normal_code_untouched():
    code = "def retry(max_retries=3):\n    return True"
    result = redact_secrets(code)
    assert "def retry" in result
    assert "max_retries=3" in result


def test_empty_string():
    assert redact_secrets("") == ""
