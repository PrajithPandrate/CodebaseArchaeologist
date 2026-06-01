import re

# Patterns that look like secrets
_SECRET_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?'), r'\1=***REDACTED***'),
    (re.compile(r'(?i)(secret[_-]?key|secret)\s*[=:]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?'), r'\1=***REDACTED***'),
    (re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^\s\'"]{8,})["\']?'), r'\1=***REDACTED***'),
    (re.compile(r'(?i)(token|auth_token|access_token)\s*[=:]\s*["\']?([A-Za-z0-9_\-\.]{20,})["\']?'), r'\1=***REDACTED***'),
    (re.compile(r'(?i)(private[_-]?key)\s*[=:]\s*["\']?([^\s]{20,})["\']?'), r'\1=***REDACTED***'),
    # AWS patterns
    (re.compile(r'AKIA[0-9A-Z]{16}'), '***AWS_KEY***'),
    # Generic long base64-ish strings that look like secrets
    (re.compile(r'(?<![A-Za-z0-9])[A-Za-z0-9+/]{40,}={0,2}(?![A-Za-z0-9])'), '***REDACTED_SECRET***'),
]


def redact_secrets(text: str) -> str:
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text
