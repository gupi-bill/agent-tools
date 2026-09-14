"""meta: 项目元信息生成。"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def register(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("project-info", help="项目信息摘要")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("readme-gen", help="生成 README")
    p.add_argument("--name", required=True)
    p.add_argument("--desc", required=True)
    p.add_argument("--output", "-o", default="README.md")
    p.add_argument("--features", help="功能列表（逗号分隔）")
    p.add_argument("--install", help="安装命令")
    p.add_argument("--usage", help="使用示例")

    p = sub.add_parser("package-json", help="生成 package.json")
    p.add_argument("--name", required=True)
    p.add_argument("--version", default="1.0.0")
    p.add_argument("--output", "-o")

    p = sub.add_parser("pyproject-info", help="解析 pyproject.toml")
    p.add_argument("path", nargs="?", default="pyproject.toml")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("git-info", help="Git 仓库信息")
    p.add_argument("--repo", nargs="?", default=".")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("contributors", help="贡献者统计")
    p.add_argument("--repo", nargs="?", default=".")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("version-bump", help="版本升级")
    p.add_argument("--bump", choices=["major", "minor", "patch"], default="patch")
    p.add_argument("--file", help="版本号文件")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("license-check", help="License 检查")
    p.add_argument("--scan", action="store_true")
    p.add_argument("--report", action="store_true")

    p = sub.add_parser("spdx-check", help="SPDX 许可证验证")
    p.add_argument("--license", required=True)

    p = sub.add_parser("changelog-gen", help="自动 CHANGELOG")
    p.add_argument("--since", help="起始版本")
    p.add_argument("--output", "-o", default="CHANGELOG.md")
def cmd_project_info(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    files = list(root.rglob("*"))
    py_files = [f for f in files if f.suffix == ".py" and f.is_file()]
    result = {
        "path": str(root),
        "total_files": len([f for f in files if f.is_file()]),
        "python_files": len(py_files),
        "directories": len([f for f in files if f.is_dir()]),
        "size_bytes": sum(f.stat().st_size for f in files if f.is_file()),
        "created": datetime.fromtimestamp(root.stat().st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(root.stat().st_mtime).isoformat(),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"📁 项目信息: {result['path']}")
        print(f"   总文件: {result['total_files']:,}")
        print(f"   Python 文件: {result['python_files']:,}")
        print(f"   目录: {result['directories']:,}")
        print(f"   总大小: {result['size_bytes']:,} bytes")
    return 0


def cmd_readme_gen(args: argparse.Namespace) -> int:
    features = [f.strip() for f in (args.features or "").split(",") if f.strip()] if args.features else []
    lines = [
        f"# {args.name}",
        "",
        f"> {args.desc}",
        "",
        "## 安装",
        "",
        f"```bash",
        args.install or "pip install .",
        "```",
        "",
        "## 使用",
        "",
        "```bash",
        args.usage or "at --help",
        "```",
        "",
    ]
    if features:
        lines += ["## 功能", "", ""]
        for f in features:
            lines.append(f"- {f}")
        lines.append("")
    lines += ["## 开发", "", "```bash", "pytest tests/ -v", "```", "", "## License", "", "MIT"]
    output = Path(args.output)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ README 已生成 → {output}")
    return 0


def cmd_package_json(args: argparse.Namespace) -> int:
    pkg = {"name": args.name, "version": args.version, "description": args.name,
           "main": "index.js", "scripts": {"test": "echo Error && exit 1"},
           "license": "MIT"}
    output = Path(args.output) if args.output else Path("package.json")
    output.write_text(json.dumps(pkg, indent=2), encoding="utf-8")
    print(f"✅ package.json 已生成 → {output}")
    return 0


def cmd_pyproject_info(args: argparse.Namespace) -> int:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    data = tomllib.loads(Path(args.path).read_text(encoding="utf-8"))
    proj = data.get("project", {})
    result = {
        "name": proj.get("name"),
        "version": proj.get("version"),
        "description": proj.get("description"),
        "python_requires": proj.get("requires-python"),
        "dependencies": proj.get("dependencies", []),
        "optional_deps": list(proj.get("optional-dependencies", {}).keys()),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"📦 {result['name']} v{result['version']}")
        print(f"   描述: {result['description']}")
        print(f"   Python: {result['python_requires']}")
        print(f"   依赖: {len(result['dependencies'])} 个")
    return 0


def cmd_git_info(args: argparse.Namespace) -> int:
    import subprocess
    repo = args.repo or "."
    def _git(*cmd):
        r = subprocess.run(["git", *cmd], capture_output=True, text=True, cwd=repo)
        return r.stdout.strip()
    result = {
        "remote": _git("remote", "get-url", "origin"),
        "branch": _git("branch", "--show-current"),
        "commits": _git("rev-list", "--all", "--count"),
        "tags": _git("tag", "--sort=-version:refname"),
        "last_commit": _git("log", "-1", "--format=%h %ad %s", "--date=short"),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"📊 Git 仓库信息: {repo}")
        print(f"   分支: {result['branch']}")
        print(f"   提交: {result['commits']} 次")
        print(f"   最新: {result['last_commit']}")
    return 0


def cmd_contributors(args: argparse.Namespace) -> int:
    import subprocess
    repo = args.repo or "."
    output = subprocess.run(["git", "-C", repo, "shortlog", "-sne", f"--all", f"--max-count={args.top}"],
                           capture_output=True, text=True).stdout
    result = []
    for line in output.splitlines():
        parts = line.strip().split("\t", 1)
        if len(parts) == 2:
            result.append({"commits": int(parts[0]), "author": parts[1]})
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"👥 贡献者 Top {args.top}")
        for r in result:
            print(f"  {r['commits']:>6}  {r['author']}")
    return 0


def cmd_version_bump(args: argparse.Namespace) -> int:
    version_file = Path(args.file) if args.file else None
    current = "0.1.0"
    if version_file and version_file.exists():
        current = version_file.read_text(encoding="utf-8").strip()
    parts = current.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if args.bump == "major":
        major += 1; minor = 0; patch = 0
    elif args.bump == "minor":
        minor += 1; patch = 0
    else:
        patch += 1
    new_version = f"{major}.{minor}.{patch}"
    if version_file:
        version_file.write_text(new_version + "\n", encoding="utf-8")
    print(f"  {current} → {new_version}")
    return 0


def cmd_spdx_check(args: argparse.Namespace) -> int:
    valid = {"MIT", "Apache-2.0", "GPL-3.0", "BSD-2-Clause", "BSD-3-Clause", "MPL-2.0", "AGPL-3.0",
             "ISC", "LGPL-2.1", "LGPL-3.0", "EPL-2.0", "Unlicense", "0BSD", "CC0-1.0"}
    if args.license in valid:
        print(f"  ✅ 有效的 SPDX 许可证: {args.license}")
        return 0
    print(f"  ⚠️  未知许可证: {args.license}")
    print(f"  可用: {', '.join(sorted(valid))}")
    return 1
