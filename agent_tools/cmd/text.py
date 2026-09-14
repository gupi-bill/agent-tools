"""text: 文本处理工具。"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def register(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("count", help="统计字数/行数/字符数")
    p.add_argument("files", nargs="+")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("sort", help="排序文件行")
    p.add_argument("input")
    p.add_argument("--output", "-o")
    p.add_argument("--reverse", action="store_true")
    p.add_argument("--unique", action="store_true")

    p = sub.add_parser("uniq", help="去重连续重复行")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("reverse", help="反转文件行")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("strip", help="去除行尾空白")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("dedup", help="全局去重行")
    p.add_argument("input")
    p.add_argument("--output", "-o")
    p.add_argument("--keep", choices=["first", "last"], default="first")

    p = sub.add_parser("truncate", help="截断文件到 N 行")
    p.add_argument("input")
    p.add_argument("--lines", type=int, required=True)
    p.add_argument("--output", "-o")

    p = sub.add_parser("head", help="取前 N 行")
    p.add_argument("input")
    p.add_argument("--n", type=int, default=10)

    p = sub.add_parser("tail", help="取后 N 行")
    p.add_argument("input")
    p.add_argument("--n", type=int, default=10)

    p = sub.add_parser("slice", help="取行范围")
    p.add_argument("input")
    p.add_argument("--start", type=int, required=True)
    p.add_argument("--end", type=int, required=True)
    p.add_argument("--output", "-o")

    p = sub.add_parser("shuffle", help="随机打乱行")
    p.add_argument("input")
    p.add_argument("--output", "-o")
    p.add_argument("--seed", type=int, default=42)

    p = sub.add_parser("chunk", help="分割文件为块")
    p.add_argument("input")
    p.add_argument("--size", type=int, default=100, help="每块行数")
    p.add_argument("--output-dir", default=".")

    p = sub.add_parser("flatten", help="扁平化嵌套 JSON/数组")
    p.add_argument("input")
    p.add_argument("--key", help="提取的字段名")

    p = sub.add_parser("transform", help="对每行应用变换")
    p.add_argument("input")
    p.add_argument("--upper", action="store_true")
    p.add_argument("--lower", action="store_true")
    p.add_argument("--trim", action="store_true")
    p.add_argument("--filter", help="正则过滤保留行")
    p.add_argument("--output", "-o")

    p = sub.add_parser("zip", help="文件压缩")
    p.add_argument("files", nargs="+")
    p.add_argument("--output", "-o", required=True)
    p.add_argument("--password", help="加密密码")

    p = sub.add_parser("unzip", help="解压文件")
    p.add_argument("input")
    p.add_argument("--output", "-o", default=".")
    p.add_argument("--password", help="解密密码")

    p = sub.add_parser("base64-encode", help="Base64 编码")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("base64-decode", help="Base64 解码")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("url-encode", help="URL 编码")
    p.add_argument("text")

    p = sub.add_parser("url-decode", help="URL 解码")
    p.add_argument("text")

    p = sub.add_parser("slugify", help="生成 URL 友好 slug")
    p.add_argument("text")

    p = sub.add_parser("uuid", help="生成 UUID")
    p.add_argument("--count", type=int, default=1)

    p = sub.add_parser("md5", help="计算文本 MD5")
    p.add_argument("text")

    p = sub.add_parser("case", help="大小写转换")
    p.add_argument("input")
    p.add_argument("--title", action="store_true")
    p.add_argument("--camel", action="store_true")
    p.add_argument("--snake", action="store_true")
    p.add_argument("--kebab", action="store_true")
    p.add_argument("--output", "-o")

    p = sub.add_parser("wordfreq", help="词频统计")
    p.add_argument("input")
    p.add_argument("--top", type=int, default=20)

    p = sub.add_parser("table", help="文本转 Markdown 表格")
    p.add_argument("input")
    p.add_argument("--header", action="store_true")
    p.add_argument("--delimiter", default="\t")

    p = sub.add_parser("regex-test", help="测试正则表达式")
    p.add_argument("--pattern", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--flags", help="re 标志，如 i,m,s")


def cmd_count(args: argparse.Namespace) -> int:
    from ..utils import count_lines
    for f in args.files:
        p = Path(f)
        stats = count_lines(p)
        print(f"  {stats['lines']:>8} lines  {stats['chars']:>8} chars  {stats['words']:>8} words  {p}")
    return 0


def cmd_sort(args: argparse.Namespace) -> int:
    inp = Path(args.input)
    lines = inp.read_text(encoding="utf-8").splitlines()
    lines.sort(reverse=args.reverse)
    if args.unique:
        lines = list(dict.fromkeys(lines))
    out = args.output and Path(args.output) or inp
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"排序完成，{len(lines)} 行")
    return 0


def cmd_uniq(args: argparse.Namespace) -> int:
    inp = Path(args.input)
    lines = inp.read_text(encoding="utf-8").splitlines()
    out_lines = []
    last = None
    for line in lines:
        if line != last:
            out_lines.append(line)
        last = line
    out = Path(args.output) if args.output else inp
    out.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"去重: {len(lines)} → {len(out_lines)} 行")
    return 0


def cmd_reverse(args: argparse.Namespace) -> int:
    inp = Path(args.input)
    lines = inp.read_text(encoding="utf-8").splitlines()[::-1]
    out = Path(args.output) if args.output else inp
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


def cmd_strip(args: argparse.Namespace) -> int:
    inp = Path(args.input)
    text = inp.read_text(encoding="utf-8")
    fixed = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    out = Path(args.output) if args.output else inp
    out.write_text(fixed, encoding="utf-8")
    return 0


def cmd_dedup(args: argparse.Namespace) -> int:
    inp = Path(args.input)
    lines = inp.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    out = []
    for line in reversed(lines) if args.keep == "last" else lines:
        if line not in seen:
            seen.add(line)
            out.append(line)
    if args.keep == "last":
        out.reverse()
    out_path = Path(args.output) if args.output else inp
    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"去重: {len(lines)} → {len(out)} 行")
    return 0


def cmd_truncate(args: argparse.Namespace) -> int:
    inp = Path(args.input)
    lines = inp.read_text(encoding="utf-8").splitlines()[: args.lines]
    out = Path(args.output) if args.output else inp
    out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print(f"截断到 {len(lines)} 行")
    return 0


def cmd_head(args: argparse.Namespace) -> int:
    lines = Path(args.input).read_text(encoding="utf-8").splitlines()[: args.n]
    print("\n".join(lines))
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    lines = Path(args.input).read_text(encoding="utf-8").splitlines()[-args.n:]
    print("\n".join(lines))
    return 0


def cmd_slice(args: argparse.Namespace) -> int:
    lines = Path(args.input).read_text(encoding="utf-8").splitlines()
    chunk = lines[args.start - 1 : args.end]
    if args.output:
        Path(args.output).write_text("\n".join(chunk) + "\n", encoding="utf-8")
    else:
        print("\n".join(chunk))
    return 0


def cmd_shuffle(args: argparse.Namespace) -> int:
    import random
    lines = Path(args.input).read_text(encoding="utf-8").splitlines()
    rng = random.Random(args.seed)
    rng.shuffle(lines)
    out = Path(args.output) if args.output else Path(args.input)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


def cmd_chunk(args: argparse.Namespace) -> int:
    inp = Path(args.input)
    lines = inp.read_text(encoding="utf-8").splitlines()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i in range(0, len(lines), args.size):
        chunk = lines[i:i + args.size]
        out = out_dir / f"chunk_{i // args.size + 1:04d}.txt"
        out.write_text("\n".join(chunk) + "\n", encoding="utf-8")
        print(f"  {out}")
    print(f"\n拆分完成，共 {len(lines)} 行")
    return 0


def cmd_transform(args: argparse.Namespace) -> int:
    lines = Path(args.input).read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        if args.upper:
            line = line.upper()
        if args.lower:
            line = line.lower()
        if args.trim:
            line = line.strip()
        if args.filter and not re.search(args.filter, line):
            continue
        out.append(line)
    result = "\n".join(out) + ("\n" if out else "")
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


def cmd_zip(args: argparse.Namespace) -> int:
    import zipfile
    out = zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED)
    for f in args.files:
        out.write(f)
    out.close()
    print(f"已压缩 {len(args.files)} 个文件")
    return 0


def cmd_unzip(args: argparse.Namespace) -> int:
    import zipfile
    with zipfile.ZipFile(args.input, "r") as z:
        if args.password:
            z.extractall(Path(args.output), pwd=args.password.encode())
        else:
            z.extractall(Path(args.output))
        print(f"已解压 {len(z.namelist())} 个文件")
    return 0


def cmd_base64_encode(args: argparse.Namespace) -> int:
    import base64
    data = Path(args.input).read_bytes()
    encoded = base64.b64encode(data).decode()
    out = Path(args.output) if args.output else Path(args.input).with_suffix(".b64")
    out.write_text(encoded, encoding="utf-8")
    print(f"已编码到 {out}")
    return 0


def cmd_base64_decode(args: argparse.Namespace) -> int:
    import base64
    data = Path(args.input).read_text(encoding="utf-8")
    decoded = base64.b64decode(data)
    out = Path(args.output) if args.output else Path(args.input).with_suffix("")
    out.write_bytes(decoded)
    print(f"已解码到 {out}")
    return 0


def cmd_url_encode(args: argparse.Namespace) -> int:
    import urllib.parse
    print(urllib.parse.quote(args.text))
    return 0


def cmd_url_decode(args: argparse.Namespace) -> int:
    import urllib.parse
    print(urllib.parse.unquote(args.text))
    return 0


def cmd_slugify(args: argparse.Namespace) -> int:
    text = args.text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    print(text)
    return 0


def cmd_uuid(args: argparse.Namespace) -> int:
    import uuid
    for _ in range(args.count):
        print(uuid.uuid4())
    return 0


def cmd_md5(args: argparse.Namespace) -> int:
    import hashlib
    print(hashlib.md5(args.text.encode()).hexdigest())
    return 0


def cmd_case(args: argparse.Namespace) -> int:
    text = Path(args.input).read_text(encoding="utf-8").strip()
    if args.title:
        result = text.title()
    elif args.camel:
        words = re.findall(r"[a-zA-Z]+", text)
        result = words[0].lower() + "".join(w.capitalize() for w in words[1:])
    elif args.snake:
        result = re.sub(r"[\s-]+", "_", text).lower()
    elif args.kebab:
        result = re.sub(r"[\s_]+", "-", text).lower()
    else:
        result = text
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result)
    return 0


def cmd_wordfreq(args: argparse.Namespace) -> int:
    import re
    text = Path(args.input).read_text(encoding="utf-8")
    words = re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: -x[1])[: args.top]
    for w, n in sorted_words:
        bar = "█" * min(n, 40)
        print(f"  {n:>5}  {bar}  {w}")
    return 0


def cmd_table(args: argparse.Namespace) -> int:
    lines = Path(args.input).read_text(encoding="utf-8").splitlines()
    delimiter = args.delimiter
    rows = [line.split(delimiter) for line in lines if line.strip()]
    if not rows:
        print("(空文件)")
        return 0
    col_widths = [max(len(cell) for cell in row) for row in zip(*rows)]
    header = rows[0] if args.header else rows[:1]
    body = rows[1:] if args.header else rows
    def fmt_row(cells: list[str]) -> str:
        return " | ".join(c.ljust(w) for c, w in zip(cells, col_widths))
    print(fmt_row(header))
    if args.header:
        print("|".join("-" * (w + 2) for w in col_widths))
    for row in body:
        padded = row + [""] * (len(col_widths) - len(row))
        print(fmt_row(padded[:len(col_widths)]))
    return 0


def cmd_regex_test(args: argparse.Namespace) -> int:
    flags = 0
    if "i" in (args.flags or ""):
        flags |= re.IGNORECASE
    if "m" in (args.flags or ""):
        flags |= re.MULTILINE
    if "s" in (args.flags or ""):
        flags |= re.DOTALL
    pat = re.compile(args.pattern, flags)
    matches = list(pat.finditer(args.text))
    print(f"正则: {args.pattern}")
    print(f"匹配数: {len(matches)}")
    for m in matches[:20]:
        print(f"  [{m.start()}-{m.end()}] {m.group()!r}")
    if len(matches) > 20:
        print(f"  ... 还有 {len(matches) - 20} 处")
    return 0

def cmd_repeat(args):
    n = getattr(args, 'count', 1)
    text = getattr(args, 'text', '')
    sep = getattr(args, 'separator', chr(10))
    print(sep.join([text] * n))
    return 0

def cmd_transpose(args):
    lines = Path(args.input).read_text(encoding='utf-8').splitlines()
    if not lines:
        return 0
    cols = max(len(l.split()) for l in lines)
    rows = len(lines)
    for c in range(cols):
        row = []
        for r in range(rows):
            parts = lines[r].split()
            row.append(parts[c] if c < len(parts) else '')
        print(' '.join(row))
    return 0

def cmd_word_wrap(args):
    import textwrap
    text = Path(args.input).read_text(encoding='utf-8')
    width = getattr(args, 'width', 80)
    wrapped = textwrap.fill(text, width=width)
    print(wrapped)
    return 0

def cmd_line_numbers(args):
    lines = Path(args.input).read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines, 1):
        print(f'{i:>6}  {line}')
    return 0

def cmd_excerpt(args):
    lines = Path(args.input).read_text(encoding='utf-8').splitlines()
    start = max(0, getattr(args, 'start', 0) - 1)
    end = min(len(lines), getattr(args, 'end', len(lines)))
    ctx = getattr(args, 'context', 0)
    for i in range(max(0, start - ctx), min(len(lines), end + ctx)):
        prefix = '...' if i < start else '   '
        suffix = '...' if i >= end else '   '
        print(f'{prefix}{i+1:>4} {lines[i]}{suffix}')
    return 0


def cmd_line_numbers(args):
    """给文件添加行号。"""
    lines = Path(args.input).read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, 1):
        print(f"{i:>6}  {line}")
    return 0


def cmd_word_wrap(args):
    """文本自动换行到指定宽度。"""
    import textwrap
    text = Path(args.input).read_text(encoding="utf-8")
    width = getattr(args, "width", 80)
    print(textwrap.fill(text, width=width))
    return 0


def cmd_excerpt(args):
    """提取文件指定行范围。"""
    lines = Path(args.input).read_text(encoding="utf-8").splitlines()
    start = max(0, getattr(args, "start", 0) - 1)
    end = min(len(lines), getattr(args, "end", len(lines)))
    for i in range(start, end):
        print(f"{i+1:>6}: {lines[i]}")
    return 0


def cmd_repeat(args):
    """重复文本 N 次。"""
    n = getattr(args, "count", 1)
    text = getattr(args, "text", "")
    sep = getattr(args, "separator", "\n")
    print(sep.join([text] * n))
    return 0


def cmd_transpose(args):
    """转置矩阵（行变列）。"""
    lines = Path(args.input).read_text(encoding="utf-8").splitlines()
    if not lines:
        return 0
    cols = max(len(l.split()) for l in lines)
    rows = len(lines)
    for c in range(cols):
        row = []
        for r in range(rows):
            parts = lines[r].split()
            row.append(parts[c] if c < len(parts) else "")
        print(" ".join(row))
    return 0
