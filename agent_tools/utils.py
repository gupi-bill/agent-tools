"""通用命令行工具函数。"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def err(msg: str) -> None:
    print(f"\033[31m❌ {msg}\033[0m", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"\033[32m✅ {msg}\033[0m")


def warn(msg: str) -> None:
    print(f"\033[33m⚠️  {msg}\033[0m")


def info(msg: str) -> None:
    print(f"ℹ️   {msg}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_date(s: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def is_private_ip(host: str) -> bool:
    return (
        host.startswith("10.")
        or host.startswith("192.168.")
        or host.startswith("172.")
        or host in ("localhost", "127.0.0.1", "::1")
    )


def mask_secret(value: str, show: int = 3) -> str:
    if len(value) <= show:
        return "*" * len(value)
    return value[:show] + "*" * (len(value) - show)


def count_lines(path: Path) -> dict[str, int]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {"lines": 0, "chars": 0, "words": 0}
    lines = text.count("\n")
    chars = len(text)
    words = len(text.split())
    return {"lines": lines, "chars": chars, "words": words}


def find_files(root: Path, pattern: str = "*", extensions: tuple[str, ...] | None = None) -> list[Path]:
    results = []
    ext_filter = set(extensions) if extensions else None
    for f in sorted(root.rglob(pattern)):
        if f.is_file():
            if ext_filter is None or f.suffix.lower() in ext_filter:
                results.append(f)
    return results


def find_python_files(root: Path) -> list[Path]:
    return find_files(root, pattern="*.py")


def detect_framework(project_root: Path) -> str:
    requirements = project_root / "requirements.txt"
    if not requirements.exists():
        return "unknown"
    content = requirements.read_text(encoding="utf-8").lower()
    for name in ("fastapi", "flask", "django", "click", "pytest"):
        if name in content:
            return name
    return "unknown"


def detect_language(root: Path) -> str:
    py = len(list(root.rglob("*.py")))
    js = len(list(root.rglob("*.js"))) + len(list(root.rglob("*.ts")))
    go = len(list(root.rglob("*.go")))
    rs = len(list(root.rglob("*.rs")))
    if py >= js and py >= go and py >= rs:
        return "python"
    if js >= go and js >= rs:
        return "typescript"
    if go >= rs:
        return "go"
    return "rust"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def terminal_width() -> int:
    try:
        cols, _ = shutil.get_terminal_size((80,))
        return cols
    except Exception:
        return 80


def color(text: str, code: int) -> str:
    return f"\033[{code}m{text}\033[0m"


def yellow(text: str) -> str:
    return color(text, 33)


def green(text: str) -> str:
    return color(text, 32)


def red(text: str) -> str:
    return color(text, 31)


def blue(text: str) -> str:
    return color(text, 34)


def cyan(text: str) -> str:
    return color(text, 36)


def bold(text: str) -> str:
    return color(text, 1)


def dim(text: str) -> str:
    return color(text, 2)


def box(title: str, content: str, width: int = 70) -> str:
    lines = content.split("\n")
    border = "╭" + "─" * (width - 2) + "╮"
    footer = "╰" + "─" * (width - 2) + "╯"
    result = [border, f"│ {bold(title):<{width - 4}} │"]
    for line in lines:
        result.append(f"│ {line:<{width - 4}} │")
    result.append(footer)
    return "\n".join(result)
