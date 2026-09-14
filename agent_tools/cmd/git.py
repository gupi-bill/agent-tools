"""git: Git 增强工具。"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def register(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("log", help="Git log")
    p.add_argument("--max-count", type=int, default=20)
    p.add_argument("--author", help="作者过滤")
    p.add_argument("--since", help="起始日期 YYYY-MM-DD")
    p.add_argument("--until", help="截止日期")
    p.add_argument("--oneline", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("diff", help="查看 diff")
    p.add_argument("--base", required=True, help="基准 commit/branch")
    p.add_argument("--head", required=True, help="目标 commit/branch")
    p.add_argument("--stat", action="store_true")
    p.add_argument("--files-only", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("stats", help="仓库统计")
    p.add_argument("--repo", nargs="?", default=".")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("branches", help="列出分支")
    p.add_argument("--merged", action="store_true", help="只显示已合并")
    p.add_argument("--unmerged", action="store_true", help="只显示未合并")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("tags", help="列出标签")
    p.add_argument("--sort", choices=["date", "version", "name"], default="date")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("blame", help="行级 blame")
    p.add_argument("file")
    p.add_argument("--line-range", help="如 10-20")
    p.add_argument("--by-author", action="store_true")

    p = sub.add_parser("first-last", help="首末 commit")
    p.add_argument("--file", help="指定文件")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("recent-changes", help="最近变更文件")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("author-stats", help="作者贡献统计")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("show", help="查看 commit 详情")
    p.add_argument("commit", nargs="?", default="HEAD")
    p.add_argument("--stat", action="store_true")
    p.add_argument("--patch", action="store_true")

    p = sub.add_parser("status-summary", help="状态摘要")
    p.add_argument("--short", action="store_true")

    p = sub.add_parser("merged-branches", help="已合并分支")
    p.add_argument("--exclude-main", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("stale-branches", help="过时分支（30天无活动）")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("conflict-files", help="找冲突文件")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("cleanup", help="清理过期分支")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--dry-run", action="store_true")


def _git(*args: str) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return r.stdout.strip()


def cmd_log(args: argparse.Namespace) -> int:
    cmd = ["log", f"--max-count={args.max_count}"]
    if args.author:
        cmd += ["--author=" + args.author]
    if args.since:
        cmd += ["--since=" + args.since]
    if args.until:
        cmd += ["--until=" + args.until]
    if args.oneline:
        cmd += ["--oneline"]
    else:
        cmd += ["--format=%H%n%an%n%ad%n%s", "--date=short"]
    output = _git(*cmd)
    if args.json:
        entries = []
        lines = output.split("\n")
        i = 0
        while i < len(lines):
            if len(lines) - i >= 4 and not lines[i].startswith("commit"):
                entries.append({
                    "hash": lines[i],
                    "author": lines[i+1],
                    "date": lines[i+2],
                    "message": lines[i+3],
                })
                i += 4
            else:
                i += 1
        print(json.dumps(entries, indent=2))
    else:
        print(output)
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    if args.stat:
        output = _git("diff", f"--stat={args.base}..{args.head}")
        print(output)
    elif args.files_only:
        output = _git("diff", "--name-only", f"{args.base}..{args.head}")
        print(output)
    else:
        output = _git("diff", f"{args.base}..{args.head}")
        print(output)
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    repo = args.repo or "."
    total_commits = _git("-C", repo, "rev-list", "--all", "--count")
    branches = _git("-C", repo, "branch", "--list").splitlines()
    tags = _git("-C", repo, "tag", "--list").splitlines()
    files = sum(1 for _ in Path(repo).rglob("*") if _.is_file())
    result = {
        "repo": repo,
        "total_commits": int(total_commits) if total_commits else 0,
        "branches": len([b for b in branches if b.strip()]),
        "tags": len(tags),
        "files": files,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"📊 {repo}")
        print(f"   提交: {result['total_commits']:,}")
        print(f"   分支: {result['branches']}")
        print(f"   标签: {result['tags']}")
        print(f"   文件: {result['files']:,}")
    return 0


def cmd_branches(args: argparse.Namespace) -> int:
    current = _git("branch", "--show-current").strip()
    all_branches = _git("branch").splitlines()
    result = []
    for b in all_branches:
        b = b.strip()
        if not b:
            continue
        marker = " *" if b.startswith("* ") else ""
        result.append({"name": b.lstrip(" *"), "current": b.startswith("*")})
    if args.merged:
        merged = _git("branch", "--merged").splitlines()
        result = [r for r in result if r["name"] in [m.strip().lstrip("* ") for m in merged]]
    if args.unmerged:
        unmerged = _git("branch", "--no-merged", "main", "--no-merged", "master").splitlines()
        result = [r for r in result if r["name"] in [m.strip().lstrip("* ") for m in unmerged]]
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for r in result:
            icon = "→ " if r["current"] else "  "
            print(f"  {icon}{r['name']}")
    return 0


def cmd_tags(args: argparse.Namespace) -> int:
    tags = _git("tag", "--sort=" + args.sort).splitlines()
    if args.json:
        print(json.dumps(tags, indent=2))
    else:
        for t in tags:
            print(f"  {t}")
    return 0


def cmd_blame(args: argparse.Namespace) -> int:
    file_arg = args.file
    cmd = ["blame", "--line-porcelain", file_arg]
    if args.line_range:
        start, end = args.line_range.split("-")
        cmd += [f"{start}-{end}"]
    output = _git(*cmd)
    if args.by_author:
        authors: dict[str, int] = {}
        for line in output.split("\n"):
            if line.startswith("author "):
                a = line[7:]
                authors[a] = authors.get(a, 0) + 1
        for a, n in sorted(authors.items(), key=lambda x: -x[1]):
            print(f"  {n:>6}  {a}")
    else:
        # 简化输出
        lines = _git("blame", "--line-buffer", file_arg).split("\n")
        for line in lines[:50]:
            if line.strip():
                print(f"  {line}")
    return 0


def cmd_first_last(args: argparse.Namespace) -> int:
    if args.file:
        first = _git("log", "--reverse", "--format=%H %ad", "--diff-filter=A", "--", args.file)
        last = _git("log", "-1", "--format=%H %ad %s", "--", args.file)
    else:
        first = _git("log", "--reverse", "--format=%H %ad", "-1")
        last = _git("log", "-1", "--format=%H %ad %s")
    result: dict = {}
    if first:
        parts = first.split()
        result["first_commit"] = parts[0] if parts else ""
        result["first_date"] = parts[1] if len(parts) > 1 else ""
    if last:
        parts = last.split()
        result["last_commit"] = parts[0] if parts else ""
        result["last_date"] = parts[1] if len(parts) > 1 else ""
        result["last_message"] = " ".join(parts[2:]) if len(parts) > 2 else ""
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for k, v in result.items():
            print(f"  {k}: {v}")
    return 0


def cmd_recent_changes(args: argparse.Namespace) -> int:
    since = f"--since={args.days} days ago"
    output = _git("diff", "--name-status", f"HEAD @{since}", "..HEAD")
    result: dict[str, int] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            status = parts[0]
            fname = parts[1]
            result.setdefault(fname, 0)
            result[fname] += 1
    sorted_files = sorted(result.items(), key=lambda x: -x[1])[: args.top]
    if args.json:
        print(json.dumps(sorted_files, indent=2))
    else:
        for f, n in sorted_files:
            print(f"  {n:>4}  {f}")
    return 0


def cmd_author_stats(args: argparse.Namespace) -> int:
    output = _git("shortlog", "-sne", f"--all", f"--max-count={args.top}")
    result: list[dict] = []
    for line in output.splitlines():
        parts = line.strip().split("\t", 1)
        if len(parts) == 2:
            count = int(parts[0].strip())
            author = parts[1].strip()
            result.append({"author": author, "commits": count})
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for r in result:
            print(f"  {r['commits']:>6}  {r['author']}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    commit = args.commit or "HEAD"
    if args.stat:
        output = _git("show", "--stat", commit)
        print(output)
    elif args.patch:
        output = _git("show", "--patch", commit)
        print(output)
    else:
        output = _git("show", "--format=%H%n%an <%ae>%n%ad%n%s%n%n%b", "--date=short", commit)
        print(output)
    return 0


def cmd_status_summary(args: argparse.Namespace) -> int:
    modified = _git("status", "--short").splitlines()
    staged = _git("diff", "--cached", "--name-only").splitlines()
    untracked = _git("ls-files", "--others", "--exclude-standard").splitlines()
    result = {
        "modified": len([m for m in modified if m and not m.startswith("??")]),
        "staged": len(staged),
        "untracked": len(untracked),
        "branch": _git("branch", "--show-current").strip(),
    }
    if args.short:
        print(f"{result['branch']} | modified:{result['modified']} staged:{result['staged']} untracked:{result['untracked']}")
    else:
        print(f"📍 分支: {result['branch']}")
        print(f"   已修改: {result['modified']} 个文件")
        print(f"   已暂存: {result['staged']} 个文件")
        print(f"   未跟踪: {result['untracked']} 个文件")
        if modified:
            print("\n修改的文件:")
            for m in modified[:20]:
                print(f"  {m}")
    return 0


def cmd_merged_branches(args: argparse.Namespace) -> int:
    current = _git("branch", "--show-current").strip()
    merged = _git("branch", "--merged").splitlines()
    result = []
    for b in merged:
        b = b.strip().lstrip("* ")
        if b and b != current:
            if args.exclude_main and b in ("main", "master"):
                continue
            result.append(b)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for b in result:
            print(f"  ✓ {b}")
    return 0


def cmd_stale_branches(args: argparse.Namespace) -> int:
    current = _git("branch", "--show-current").strip()
    output = _git("for-each-ref", "--sort=-committerdate", "refs/heads/",
                   "--format=%(refname:short) %(committerdate:relative) %(committerdate:short)")
    result: list[dict] = []
    cutoff = datetime.now() - __import__("datetime").timedelta(days=args.days)
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        name = parts[0]
        if name == current:
            continue
        date_str = " ".join(parts[1:3])
        try:
            # 简单检查: 包含 "ago" 且天数 < args.days
            if "ago" in line:
                import re
                m = re.search(r"(\d+)\s*(day|week|month)s?\s*ago", line)
                if m:
                    num = int(m.group(1))
                    unit = m.group(2)
                    days = num * (365 if unit == "month" else 30 if unit == "week" else 1)
                    if days > args.days:
                        result.append({"name": name, "days_ago": days})
        except Exception:
            pass
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for r in result:
            print(f"  ⏰ {r['name']}  ({r['days_ago']} 天前)")
    return 0


def cmd_conflict_files(args: argparse.Namespace) -> int:
    conflicts = _git("diff", "--name-only", "--diff-filter=U").splitlines()
    if args.json:
        print(json.dumps(conflicts, indent=2))
    else:
        if conflicts:
            print("🔴 发现冲突文件:")
            for c in conflicts:
                print(f"  ✗ {c}")
        else:
            print("✅ 无冲突文件")
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    import re
    from datetime import datetime, timedelta
    current = _git("branch", "--show-current").strip()
    all_branches = _git("branch").splitlines()
    removed = 0
    for b in all_branches:
        b = b.strip().lstrip("* ")
        if not b or b == current:
            continue
        last_commit = _git("log", "-1", "--format=%ct", b)
        if not last_commit:
            continue
        try:
            commit_time = datetime.fromtimestamp(int(last_commit))
            if datetime.now() - commit_time > timedelta(days=args.days):
                if args.dry_run:
                    print(f"  [DRY] 删除: {b}")
                else:
                    _git("branch", "-d", b)
                    print(f"  ✓ 删除: {b}")
                removed += 1
        except (ValueError, OSError):
            pass
    print(f"\n清理了 {removed} 个过时分支")
    return 0