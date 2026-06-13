import pytest
from ..services.code_chunker import chunk_file, ChunkInfo


PYTHON_CODE = '''
def hello(name: str) -> str:
    return f"Hello, {name}!"


class PaymentService:
    def __init__(self, db):
        self.db = db

    def charge(self, amount: float) -> bool:
        return True

    def retry(self, payment_id: str) -> bool:
        for i in range(3):
            if self.charge(10.0):
                return True
        return False
'''


def test_python_chunking():
    chunks = chunk_file("payments.py", PYTHON_CODE)
    assert len(chunks) >= 2
    names = [c.symbol_name for c in chunks]
    assert "hello" in names
    assert "PaymentService" in names


def test_chunk_has_content():
    chunks = chunk_file("payments.py", PYTHON_CODE)
    for chunk in chunks:
        assert chunk.content.strip()
        assert chunk.start_line > 0
        assert chunk.end_line >= chunk.start_line
        assert chunk.content_hash


def test_empty_file():
    chunks = chunk_file("empty.py", "")
    assert chunks == []


def test_line_window_fallback():
    long_content = "\n".join([f"line {i}" for i in range(500)])
    chunks = chunk_file("data.csv", long_content)
    assert len(chunks) >= 2
    for chunk in chunks:
        lines = chunk.content.split("\n")
        assert len(lines) <= 220  # MAX_CHUNK_LINES + overlap buffer


def test_typescript_chunking():
    ts_code = '''
export function processPayment(id: string): Promise<Result> {
  return fetch(`/api/pay/${id}`)
}

export class PaymentClient {
  constructor(private url: string) {}

  async charge(amount: number) {
    return this.http.post("/charge", { amount })
  }
}
'''
    chunks = chunk_file("client.ts", ts_code)
    names = [c.symbol_name for c in chunks]
    assert "processPayment" in names or "PaymentClient" in names


def test_redaction_in_chunk():
    code_with_secret = '''
API_KEY = "sk-prod-abc123def456789012345678901234"
def get_client():
    return requests.Session()
'''
    chunks = chunk_file("config.py", code_with_secret)
    for chunk in chunks:
        assert "sk-prod-abc123def456" not in chunk.content


def test_content_hash_unique():
    chunks = chunk_file("payments.py", PYTHON_CODE)
    hashes = [c.content_hash for c in chunks]
    assert len(set(hashes)) == len(hashes)
