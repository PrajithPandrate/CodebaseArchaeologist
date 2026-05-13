"""
Splits source files into semantic chunks (function/class level when possible,
falling back to line-based windows).
"""
import re
import hashlib
from dataclasses import dataclass
from typing import Optional

MAX_CHUNK_LINES = 200
MIN_CHUNK_LINES = 10


@dataclass
class ChunkInfo:
    symbol_name: Optional[str]
    symbol_type: Optional[str]  # function | class | method | file_section
    start_line: int  # 1-based
    end_line: int
    content: str
    content_hash: str


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# --- Language-specific symbol detection ---

_PYTHON_FUNC = re.compile(r'^(\s*)(async\s+)?def\s+(\w+)\s*\(')
_PYTHON_CLASS = re.compile(r'^(\s*)class\s+(\w+)\s*[:(]')
_JS_FUNC = re.compile(r'^(\s*)(export\s+)?(async\s+)?function\s+(\w+)\s*\(')
_JS_ARROW = re.compile(r'^(\s*)(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s*)?\(')
_JS_CLASS = re.compile(r'^(\s*)(export\s+)?class\s+(\w+)\s*')
_GO_FUNC = re.compile(r'^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(')
_JAVA_METHOD = re.compile(r'^\s+(public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\(')
_RUST_FN = re.compile(r'^(\s*)(pub\s+)?(async\s+)?fn\s+(\w+)\s*')


def _detect_symbol(line: str, lang: str) -> Optional[tuple[str, str]]:
    """Returns (name, type) or None."""
    if lang == "python":
        m = _PYTHON_CLASS.match(line)
        if m:
            return m.group(2), "class"
        m = _PYTHON_FUNC.match(line)
        if m:
            name = m.group(3)
            indent = len(m.group(1))
            return name, "method" if indent > 0 else "function"
    elif lang in ("javascript", "typescript", "tsx", "jsx"):
        m = _JS_CLASS.match(line)
        if m:
            return m.group(3), "class"
        m = _JS_FUNC.match(line)
        if m:
            return m.group(4), "function"
        m = _JS_ARROW.match(line)
        if m:
            return m.group(4), "function"
    elif lang == "go":
        m = _GO_FUNC.match(line)
        if m:
            return m.group(1), "function"
    elif lang in ("java", "kotlin"):
        m = _JAVA_METHOD.match(line)
        if m:
            return m.group(2), "method"
    elif lang == "rust":
        m = _RUST_FN.match(line)
        if m:
            return m.group(4), "function"
    return None


def _language_from_path(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return {
        "py": "python",
        "js": "javascript",
        "jsx": "jsx",
        "ts": "typescript",
        "tsx": "tsx",
        "go": "go",
        "java": "java",
        "kt": "kotlin",
        "rs": "rust",
        "cpp": "cpp", "cc": "cpp", "cxx": "cpp",
        "c": "c",
        "rb": "ruby",
        "php": "php",
        "md": "markdown",
        "txt": "text",
    }.get(ext, "unknown")


def chunk_file(file_path: str, content: str) -> list[ChunkInfo]:
    lang = _language_from_path(file_path)
    lines = content.splitlines()

    if not lines:
        return []

    # For markdown/text, do simple line-window chunking
    if lang in ("markdown", "text", "unknown"):
        return _line_window_chunks(lines, "file_section")

    # Try symbol-based chunking
    chunks = _symbol_chunks(lines, lang)
    if chunks:
        return chunks

    # Fallback: line windows
    return _line_window_chunks(lines, "file_section")


def _symbol_chunks(lines: list[str], lang: str) -> list[ChunkInfo]:
    """Split by top-level symbols. Returns empty list if no symbols found."""
    boundaries: list[tuple[int, str, str]] = []  # (line_idx, name, type)

    for i, line in enumerate(lines):
        result = _detect_symbol(line, lang)
        if result:
            name, stype = result
            boundaries.append((i, name, stype))

    if not boundaries:
        return []

    chunks = []
    for idx, (start, name, stype) in enumerate(boundaries):
        end = boundaries[idx + 1][0] - 1 if idx + 1 < len(boundaries) else len(lines) - 1
        # Split large chunks further
        chunk_lines = lines[start: end + 1]
        if len(chunk_lines) > MAX_CHUNK_LINES:
            sub = _line_window_chunks(chunk_lines, stype, start_offset=start, symbol_name=name)
            chunks.extend(sub)
        else:
            content = "\n".join(chunk_lines)
            chunks.append(ChunkInfo(
                symbol_name=name,
                symbol_type=stype,
                start_line=start + 1,
                end_line=end + 1,
                content=content,
                content_hash=_hash(content),
            ))

    return chunks


def _line_window_chunks(
    lines: list[str],
    stype: str,
    start_offset: int = 0,
    symbol_name: Optional[str] = None,
) -> list[ChunkInfo]:
    """Fixed-size sliding window fallback."""
    chunks = []
    step = MAX_CHUNK_LINES - 20  # 20-line overlap

    for i in range(0, max(1, len(lines)), step):
        window = lines[i: i + MAX_CHUNK_LINES]
        if not window:
            break
        content = "\n".join(window)
        chunks.append(ChunkInfo(
            symbol_name=symbol_name,
            symbol_type=stype,
            start_line=start_offset + i + 1,
            end_line=start_offset + i + len(window),
            content=content,
            content_hash=_hash(content),
        ))

    return chunks
