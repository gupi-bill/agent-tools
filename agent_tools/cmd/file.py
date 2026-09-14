"""file: 文件与代码操作工具。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def register(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="cmd", required=True)

    # Count
    p = sub.add_parser("count", help="统计文件/目录")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--json", action="store_true")

    # Grep
    p = sub.add_parser("grep", help="递归搜索文本")
    p.add_argument("pattern")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", help="文件后缀过滤")
    p.add_argument("--count", action="store_true")

    # Find
    p = sub.add_parser("find", help="查找文件")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--name", help="文件名模式")
    p.add_argument("--ext", help="后缀")
    p.add_argument("--size-min", help="最小字节")
    p.add_argument("--size-max", help="最大字节")
    p.add_argument("--empty", action="store_true")
    p.add_argument("--json", action="store_true")

    # Size
    p = sub.add_parser("size", help="目录大小统计")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--json", action="store_true")

    # Duplicates
    p = sub.add_parser("dupes", help="找重复文件")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    # Replace
    p = sub.add_parser("replace", help="批量替换文本")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--from", dest="fr", required=True, help="原字符串")
    p.add_argument("--to", dest="to", required=True, help="新字符串")
    p.add_argument("--ext", default=".py,.js,.ts,.json,.yaml,.yml,.md,.toml,.txt,.sh,.bat")
    p.add_argument("--dry-run", action="store_true")

    # Count lines
    p = sub.add_parser("lines", help="统计代码行数")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", help="后缀列表（逗号分隔）")
    p.add_argument("--json", action="store_true")
    p.add_argument("--by-file", action="store_true")

    # Sort by size
    p = sub.add_parser("sort-size", help="按大小排序文件")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--reverse", action="store_true", help="大到小")

    # Walk
    p = sub.add_parser("walk", help="遍历目录树")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--max-depth", type=int, default=5)
    p.add_argument("--json", action="store_true")

    # Tree
    p = sub.add_parser("tree", help="目录树")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--max-depth", type=int, default=3)
    p.add_argument("--dirs", action="store_true")

    # Hash
    p = sub.add_parser("hash", help="文件哈希")
    p.add_argument("path")
    p.add_argument("--algo", choices=["md5", "sha1", "sha256"], default="sha256")

    # Diff
    p = sub.add_parser("diff", help="文件 diff")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--json", action="store_true")

    # Merge
    p = sub.add_parser("merge", help="合并文本文件")
    p.add_argument("paths", nargs="+")
    p.add_argument("--output", "-o", required=True)
    p.add_argument("--separator", default="\n---\n")

    # Split
    p = sub.add_parser("split", help="分割大文件")
    p.add_argument("input")
    p.add_argument("--lines", type=int, default=1000)
    p.add_argument("--output-dir", default=".")

    # Rename
    p = sub.add_parser("rename", help="批量重命名")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--pattern", required=True, help="正则")
    p.add_argument("--replace", required=True, help="替换字符串")
    p.add_argument("--ext", help="只匹配后缀")
    p.add_argument("--dry-run", action="store_true")

    # Touch
    p = sub.add_parser("touch", help="创建/更新时间戳")
    p.add_argument("paths", nargs="+")

    # Symlink
    p = sub.add_parser("symlink", help="创建符号链接")
    p.add_argument("target")
    p.add_argument("link")

    # Copy tree
    p = sub.add_parser("cpytree", help="复制目录树（含过滤）")
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--exclude", nargs="*", default=["__pycache__", ".git", "node_modules"])

    # Delete empty dirs
    p = sub.add_parser("rmdir-empty", help="删除空目录")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--dry-run", action="store_true")

    # Fix CRLF
    p = sub.add_parser("fix-crlf", help="统一换行符为 LF")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py,.js,.ts,.json,.yaml,.yml,.md,.toml,.sh,.bat,.txt")
    p.add_argument("--dry-run", action="store_true")

    # Add shebang
    p = sub.add_parser("shebang", help="给脚本加 shebang")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--interpreter", default="/usr/bin/env python3")
    p.add_argument("--ext", default=".py")
    p.add_argument("--dry-run", action="store_true")

    # Normalize imports
    p = sub.add_parser("norm-imports", help="规范化 import 顺序")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py")
    p.add_argument("--dry-run", action="store_true")

    # Trailing whitespace
    p = sub.add_parser("trim-ws", help="移除行尾空白")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py,.js,.ts,.json,.yaml,.yml,.md,.toml,.sh,.bat,.txt")
    p.add_argument("--dry-run", action="store_true")

    # File info
    p = sub.add_parser("info", help="文件详细信息")
    p.add_argument("path")
    p.add_argument("--json", action="store_true")

    # Chmod (Unix)
    p = sub.add_parser("chmod", help="设置文件权限")
    p.add_argument("mode", help="八进制权限如 755")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py,.sh")

    # Mv
    p = sub.add_parser("mv", help="批量移动文件")
    p.add_argument("--from-ext", dest="fr_ext", required=True)
    p.add_argument("--to-ext", dest="to_ext", required=True)
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--dry-run", action="store_true")

    # Ext count
    p = sub.add_parser("ext-count", help="统计后缀分布")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--top", type=int, default=20)

    # Recent
    p = sub.add_parser("recent", help="最近修改的文件")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--json", action="store_true")

    # Age
    p = sub.add_parser("age", help="文件年龄分析")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--json", action="store_true")

    # Symlinks check
    p = sub.add_parser("check-symlinks", help="检查符号链接")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--broken", action="store_true")

    # Empty files
    p = sub.add_parser("empty-files", help="找空文件")
    p.add_argument("path", nargs="?", default=".")

    # Hidden files
    p = sub.add_parser("hidden", help="找隐藏文件")
    p.add_argument("path", nargs="?", default=".")


def cmd_count(args: argparse.Namespace) -> int:
    from ..utils import count_lines, find_files
    root = Path(args.path).resolve()
    files = find_files(root)
    dirs = [d for d in root.rglob("*") if d.is_dir()]
    total_size = sum(f.stat().st_size for f in files if f.stat().st_size is not None)
    result = {
        "root": str(root),
        "files": len(files),
        "directories": len(dirs),
        "total_size_bytes": total_size,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{root}")
        print(f"   文件: {result['files']} 个")
        print(f"   目录: {result['directories']} 个")
        print(f"   总大小: {result['total_size_bytes']:,} bytes")
    return 0


def cmd_grep(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    pattern = re.compile(args.pattern, re.IGNORECASE)
    ext_filter = tuple(args.ext.split(",")) if args.ext else None
    hits: list[dict] = []
    for f in root.rglob("*"):
        if f.is_file():
            if ext_filter and f.suffix.lower() not in ext_filter:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    if args.count:
                        hits.append({"file": str(f.relative_to(root)), "count": text.count(args.pattern)})
                        break
                    else:
                        hits.append({"file": str(f.relative_to(root)), "line": i, "text": line.strip()[:200]})
    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return 0
    print(f"找到 {len(hits)} 处匹配")
    for h in hits[:50]:
        print(f"  {h['file']}:{h.get('line', '')} {h.get('text', '')}")
    if len(hits) > 50:
        print(f"  ... 还有 {len(hits) - 50} 处")
    return 0


def cmd_find(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    results = []
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(root)
        if args.name and not re.search(args.name, f.name, re.IGNORECASE):
            continue
        if args.ext and f.suffix.lower() != f".{args.ext.lstrip('.')}" :
            continue
        stat = f.stat()
        if args.size_min and stat.st_size < int(args.size_min):
            continue
        if args.size_max and stat.st_size > int(args.size_max):
            continue
        if args.empty and stat.st_size != 0:
            continue
        results.append(str(rel))
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(f"  {r}")
        print(f"\n共 {len(results)} 个文件")
    return 0


def cmd_size(args: argparse.Namespace) -> int:
    from ..utils import human_size
    root = Path(args.path).resolve()
    dirs_sizes: dict[str, int] = {}
    for d in root.rglob("*"):
        if d.is_dir():
            total = 0
            for f in d.rglob("*"):
                if f.is_file():
                    try:
                        total += f.stat().st_size
                    except OSError:
                        pass
            dirs_sizes[str(d.relative_to(root))] = total
    sorted_dirs = sorted(dirs_sizes.items(), key=lambda x: -x[1])[: args.top]
    if args.json:
        print(json.dumps([{"path": p, "size": s, "human": human_size(s)} for p, s in sorted_dirs], indent=2))
        return 0
    print(f"📊 {root} 目录大小 Top {args.top}")
    for i, (p, s) in enumerate(sorted_dirs, 1):
        print(f"  {i:2d}. {human_size(s):>10}  {p}")
    return 0


def cmd_dupes(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    hash_map: dict[str, list[str]] = {}
    for f in root.rglob("*"):
        if f.is_file() and f.stat().st_size > 0:
            try:
                data = f.read_bytes()
                h = hashlib.sha256(data).hexdigest()
                hash_map.setdefault(h, []).append(str(f.relative_to(root)))
            except OSError:
                pass
    dupes = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    if args.json:
        print(json.dumps(dupes, indent=2))
        return 0
    if not dupes:
        print("✅ 未发现重复文件")
        return 0
    print(f"发现 {len(dupes)} 组重复文件")
    total_waste = 0
    for h, paths in dupes.items():
        size = Path(paths[0]).stat().st_size * (len(paths) - 1)
        total_waste += size
        print(f"  [{h[:8]}] ×{len(paths)}  ({size} bytes)")
        for p in paths:
            print(f"    - {p}")
    print(f"\n💾 可释放空间: {total_waste:,} bytes")
    return 0


def cmd_replace(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(","))
    count = 0
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if args.fr not in text:
                continue
            new_text = text.replace(args.fr, args.to)
            if args.dry_run:
                print(f"  [DRY] {f.relative_to(root)}")
                count += text.count(args.fr)
            else:
                f.write_text(new_text, encoding="utf-8")
                print(f"  ✓ {f.relative_to(root)}")
                count += text.count(args.fr)
    print(f"\n替换了 {count} 处")
    return 0


def cmd_lines(args: argparse.Namespace) -> int:
    from ..utils import count_lines
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(",")) if args.ext else None
    totals: dict[str, int] = {"lines": 0, "files": 0, "chars": 0, "words": 0}
    per_file: dict[str, dict] = {}
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in (exts or {".py"}):
            stats = count_lines(f)
            totals["lines"] += stats["lines"]
            totals["chars"] += stats["chars"]
            totals["words"] += stats["words"]
            totals["files"] += 1
            per_file[str(f.relative_to(root))] = stats
    if args.json:
        print(json.dumps({"totals": totals, "by_file": per_file}, indent=2))
        return 0
    print(f"📝 代码行数统计: {root}")
    print(f"   总行数: {totals['lines']:,} | 文件: {totals['files']} | 字符: {totals['chars']:,} | 单词: {totals['words']:,}")
    if args.by_file:
        for p, s in sorted(per_file.items(), key=lambda x: -x[1]["lines"])[:20]:
            print(f"   {s['lines']:>6}  {p}")
    return 0


def cmd_sort_size(args: argparse.Namespace) -> int:
    from ..utils import human_size
    root = Path(args.path).resolve()
    files = [(f, f.stat().st_size) for f in root.rglob("*") if f.is_file()]
    files.sort(key=lambda x: x[1], reverse=args.reverse)
    for f, sz in files[: args.top]:
        print(f"  {human_size(sz):>10}  {f.relative_to(root)}")
    return 0


def cmd_walk(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    results = []
    def _walk(p: Path, depth: int) -> None:
        if depth > args.max_depth:
            return
        rel = p.relative_to(root)
        results.append({"path": str(rel), "type": "dir" if p.is_dir() else "file", "depth": depth})
        if p.is_dir():
            for child in sorted(p.iterdir()):
                _walk(child, depth + 1)
    _walk(root, 0)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results[:100]:
            indent = "  " * r["depth"]
            icon = "📁" if r["type"] == "dir" else "📄"
            print(f"  {indent}{icon} {r['path']}")
        if len(results) > 100:
            print(f"  ... 还有 {len(results) - 100} 项")
    return 0


def cmd_tree(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    def _tree(p: Path, prefix: str, is_last: bool) -> None:
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{p.name}")
        if p.is_dir() and args.max_depth > 0:
            children = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            extension = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(children):
                _tree(child, extension, i == len(children) - 1)
    print(root.name)
    _tree(root, "", True)
    return 0


def cmd_hash(args: argparse.Namespace) -> int:
    p = Path(args.path)
    algo = hashlib.new(args.algo)
    data = p.read_bytes()
    algo.update(data)
    h = algo.hexdigest()
    print(f"{h}  {p}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    import difflib
    a = Path(args.a).read_text(encoding="utf-8", errors="ignore")
    b = Path(args.b).read_text(encoding="utf-8", errors="ignore")
    diffs = list(difflib.unified_diff(a.splitlines(), b.splitlines(), fromfile=args.a, tofile=args.b))
    if args.json:
        print(json.dumps(diffs, indent=2))
    else:
        for line in diffs:
            color = ""
            if line.startswith("+"):
                color = "\033[32m"
            elif line.startswith("-"):
                color = "\033[31m"
            elif line.startswith("@"):
                color = "\033[36m"
            print(f"{color}{line}\033[0m", end="")
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    out = Path(args.output)
    parts = []
    for p in args.paths:
        parts.append(Path(p).read_text(encoding="utf-8", errors="ignore"))
    out.write_text(args.separator.join(parts), encoding="utf-8")
    print(f"已合并 {len(args.paths)} 个文件到 {out}")
    return 0


def cmd_split(args: argparse.Namespace) -> int:
    inp = Path(args.input)
    out_dir = Path(args.output_dir)
    ensure_dir(out_dir)
    text = inp.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    chunk = args.lines
    for i in range(0, len(lines), chunk):
        part = lines[i:i + chunk]
        idx = i // chunk + 1
        out = out_dir / f"{inp.stem}_part{idx}{inp.suffix}"
        out.write_text("\n".join(part) + "\n", encoding="utf-8")
        print(f"  {out}")
    print(f"\n已拆分为 {(len(lines) + chunk - 1) // chunk} 个文件")
    return 0


def cmd_rename(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    pat = re.compile(args.pattern, re.IGNORECASE)
    changed = 0
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if args.ext and f.suffix.lower() != f".{args.ext.lstrip('.')}":
            continue
        m = pat.search(f.name)
        if not m:
            continue
        new_name = pat.sub(args.replace, f.name)
        new_path = f.parent / new_name
        if args.dry_run:
            print(f"  [DRY] {f.name} → {new_name}")
        else:
            f.rename(new_path)
            print(f"  ✓ {f.name} → {new_name}")
        changed += 1
    print(f"\n重命名了 {changed} 个文件")
    return 0


def cmd_touch(args: argparse.Namespace) -> int:
    now = datetime.now().timestamp()
    for p in args.paths:
        Path(p).touch(atime=now, mtime=now)
        print(f"  touched {p}")
    return 0


def cmd_symlink(args: argparse.Namespace) -> int:
    src = Path(args.target).resolve()
    dst = Path(args.link)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    dst.symlink_to(src)
    print(f"  symlink {dst} → {src}")
    return 0


def cmd_cpytree(args: argparse.Namespace) -> int:
    src = Path(args.src).resolve()
    dst = Path(args.dst)
    excludes = set(args.exclude)
    count = 0
    for f in src.rglob("*"):
        rel = f.relative_to(src)
        parts = rel.parts
        if any(p in excludes for p in parts):
            continue
        dest = dst / rel
        if f.is_file():
            ensure_dir(dest.parent)
            shutil.copy2(f, dest)
            count += 1
    print(f"复制了 {count} 个文件到 {dst}")
    return 0


def cmd_rmdir_empty(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    removed = 0
    for f in sorted(root.rglob("*"), key=lambda x: -len(x.parts)):
        if f.is_dir() and not any(f.iterdir()):
            if args.dry_run:
                print(f"  [DRY] {f.relative_to(root)}")
            else:
                f.rmdir()
                print(f"  ✓ {f.relative_to(root)}")
            removed += 1
    print(f"\n删除了 {removed} 个空目录")
    return 0


def cmd_fix_crlf(args: argparse.Namespace) -> int:
    exts = tuple(args.ext.split(","))
    changed = 0
    for f in Path(args.path).resolve().rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "\r\n" not in text:
                continue
            fixed = text.replace("\r\n", "\n")
            if args.dry_run:
                print(f"  [DRY] {f.relative_to(Path(args.path))}")
            else:
                f.write_text(fixed, encoding="utf-8")
                print(f"  ✓ {f.relative_to(Path(args.path))}")
            changed += 1
    print(f"\n处理了 {changed} 个文件")
    return 0


def cmd_shebang(args: argparse.Namespace) -> int:
    exts = tuple(args.ext.split(","))
    shebang = f"#!{args.interpreter}\n"
    for f in Path(args.path).resolve().rglob(f"*{exts[-1]}"):
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        if text.startswith("#!"):
            continue
        if args.dry_run:
            print(f"  [DRY] 添加 shebang 到 {f.name}")
        else:
            f.write_text(shebang + text, encoding="utf-8")
            print(f"  ✓ {f.name}")
    return 0


def cmd_trim_ws(args: argparse.Namespace) -> int:
    exts = tuple(args.ext.split(","))
    changed = 0
    for f in Path(args.path).resolve().rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            fixed = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
            if fixed != text:
                if args.dry_run:
                    print(f"  [DRY] {f.relative_to(Path(args.path))}")
                else:
                    f.write_text(fixed, encoding="utf-8")
                    print(f"  ✓ {f.relative_to(Path(args.path))}")
                changed += 1
    print(f"\n清理了 {changed} 个文件")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    p = Path(args.path)
    s = p.stat()
    result = {
        "path": str(p),
        "name": p.name,
        "size": s.st_size,
        "created": s.st_ctime,
        "modified": s.st_mtime,
        "is_file": p.is_file(),
        "is_dir": p.is_dir(),
        "is_symlink": p.is_symlink(),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"📄 {p.name}")
        print(f"   路径: {p}")
        print(f"   大小: {s.st_size:,} bytes")
        print(f"   类型: {'文件' if p.is_file() else '目录' if p.is_dir() else '其他'}")
    return 0


def cmd_chmod(args: argparse.Namespace) -> int:
    mode = int(args.mode, 8)
    exts = tuple(args.ext.split(","))
    root = Path(args.path).resolve()
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            os.chmod(f, mode)
            print(f"  chmod {args.mode} {f.relative_to(root)}")
    return 0


def cmd_mv(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    changed = 0
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() == f".{args.fr_ext.lstrip('.')}":
            new_name = f.with_suffix(f".{args.to_ext.lstrip('.')}")
            if args.dry_run:
                print(f"  [DRY] {f.name} → {new_name.name}")
            else:
                f.rename(new_name)
                print(f"  ✓ {f.name} → {new_name.name}")
            changed += 1
    print(f"\n重命名了 {changed} 个文件")
    return 0


def cmd_ext_count(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    counts: dict[str, int] = {}
    for f in root.rglob("*"):
        if f.is_file():
            ext = f.suffix.lower() or "(no ext)"
            counts[ext] = counts.get(ext, 0) + 1
    sorted_counts = sorted(counts.items(), key=lambda x: -x[1])[: args.top]
    for ext, n in sorted_counts:
        print(f"  {n:>6}  {ext}")
    return 0


def cmd_recent(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    now = datetime.now().timestamp()
    cutoff = now - args.days * 86400
    results = []
    for f in root.rglob("*"):
        if f.is_file():
            try:
                mtime = f.stat().st_mtime
                if mtime >= cutoff:
                    results.append({"file": str(f.relative_to(root)), "mtime": mtime, "age_days": (now - mtime) / 86400})
            except OSError:
                pass
    results.sort(key=lambda x: -x["mtime"])
    if args.json:
        print(json.dumps(results[: args.top], indent=2))
    else:
        for r in results[: args.top]:
            print(f"  {r['file']:<40}  {r['age_days']:.1f} days ago")
    return 0


def cmd_age(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    now = datetime.now().timestamp()
    ages: list[float] = []
    for f in root.rglob("*"):
        if f.is_file():
            try:
                age = (now - f.stat().st_mtime) / 86400
                ages.append(age)
            except OSError:
                pass
    if not ages:
        print("无文件")
        return 0
    ages.sort()
    result = {
        "min": ages[0],
        "max": ages[-1],
        "median": ages[len(ages) // 2],
        "mean": sum(ages) / len(ages),
        "count": len(ages),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"📊 文件年龄分析")
        print(f"   最少: {result['min']:.1f} 天")
        print(f"   最多: {result['max']:.1f} 天")
        print(f"   中位数: {result['median']:.1f} 天")
        print(f"   平均: {result['mean']:.1f} 天")
        print(f"   文件数: {result['count']}")
    return 0


def cmd_check_symlinks(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    broken = []
    all_links = []
    for f in root.rglob("*"):
        if f.is_symlink():
            all_links.append(str(f.relative_to(root)))
            if not f.exists():
                broken.append(str(f.relative_to(root)))
    if args.broken:
        if broken:
            print(f"🔴 发现 {len(broken)} 个断裂符号链接:")
            for b in broken:
                print(f"  - {b}")
        else:
            print("✅ 无断裂符号链接")
    else:
        print(f"共 {len(all_links)} 个符号链接，{len(broken)} 个断裂")
        for l in all_links:
            status = "✓" if Path(root / l).exists() or not (root / l).is_symlink() else "✗"
            print(f"  {status} {l}")
    return 0


def cmd_empty_files(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    for f in sorted(root.rglob("*")):
        if f.is_file() and f.stat().st_size == 0:
            print(f"  📄 {f.relative_to(root)}")
    return 0


def cmd_hidden(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    for f in sorted(root.rglob("*")):
        if f.name.startswith("."):
            print(f"  {f.relative_to(root)}")
    return 0


def cmd_glob_search(args):
    root = Path(args.path).resolve()
    pattern = args.pattern
    results = list(root.glob(pattern))
    print(f'Found {len(results)} files matching pattern')
    for r in results[:20]:
        print(f'  {r.relative_to(root)}')
    return 0
