"""dev: 开发辅助工具。"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def register(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("deps", help="依赖分析")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("import-graph", help="导入关系图")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py")
    p = sub.add_parser("todo", help="扫描 TODO/FIXME/HACK")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", help="后缀过滤")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("test-gen", help="生成测试模板")
    p.add_argument("module", nargs="?", help="模块路径")
    p.add_argument("--output", "-o")
    p.add_argument("--framework", choices=["pytest", "unittest"], default="pytest")

    p = sub.add_parser("changelog", help="根据 commit 生成 CHANGELOG")
    p.add_argument("--since", help="起始 tag/commit")
    p.add_argument("--output", "-o", default="CHANGELOG.md")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("schema-gen", help="从代码生成 JSON Schema")
    p.add_argument("path", help="Python 文件路径")
    p.add_argument("--output", "-o")

    p = sub.add_parser("doc-gen", help="生成文档注释")
    p.add_argument("path", help="Python 文件路径")
    p.add_argument("--output", "-o")

    p = sub.add_parser("config-gen", help="生成配置文件模板")
    p.add_argument("--name", required=True, help="配置名")
    p.add_argument("--format", choices=["json", "yaml", "toml", "env"], default="json")
    p.add_argument("--output", "-o")

    p = sub.add_parser("makefile-gen", help="生成 Makefile")
    p.add_argument("--name", required=True, help="项目名称")
    p.add_argument("--lang", choices=["python", "node", "go", "rust"], default="python")
    p.add_argument("--output", "-o", default="Makefile")

    p = sub.add_parser("docker-gen", help="生成 Dockerfile")
    p.add_argument("--lang", choices=["python", "node", "go", "rust"], default="python")
    p.add_argument("--output", "-o", default="Dockerfile")
    p.add_argument("--base", help="基础镜像")
    p.add_argument("--port", type=int, default=8080)

    p = sub.add_parser("ci-gen", help="生成 GitHub Actions CI")
    p.add_argument("--lang", choices=["python", "node", "go", "rust"], default="python")
    p.add_argument("--output", "-o", default=".github/workflows/ci.yml")
    p.add_argument("--tests", action="store_true")

    p = sub.add_parser("package-gen", help="生成 package.json / pyproject.toml")
    p.add_argument("--name", required=True)
    p.add_argument("--type", choices=["python", "node", "go", "rust"], default="python")
    p.add_argument("--output", "-o")

    p = sub.add_parser("init-project", help="初始化项目结构")
    p.add_argument("--name", required=True)
    p.add_argument("--lang", choices=["python", "node", "go", "rust"], default="python")
    p.add_argument("--output", "-o", default=".")
    p.add_argument("--with-tests", action="store_true")
    p.add_argument("--with-ci", action="store_true")

    p = sub.add_parser("license", help="生成 License 文件")
    p.add_argument("--type", choices=["mit", "apache2", "gpl3", "bsd2", "bsd3", "mpl2", "agpl3"], default="mit")
    p.add_argument("--author", help="作者名")
    p.add_argument("--year", help="年份")
    p.add_argument("--output", "-o", default="LICENSE")

    p = sub.add_parser("hook-gen", help="生成 git hook")
    p.add_argument("--name", required=True, help="hook 名如 pre-commit")
    p.add_argument("--output", "-o", default=".git/hooks/pre-commit")

    p = sub.add_parser("error-check", help="检查未处理的异常")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("unused-imports", help="查找未使用的 import")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("type-hints", help="添加类型注解")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("flake8-report", help="Flake8 风格报告")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("cyclomatic", help="圈复杂度分析")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py")
    p.add_argument("--max", type=int, default=10)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("ast-dump", help="AST 树输出")
    p.add_argument("path")

    p = sub.add_parser("function-count", help="统计函数/方法数")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("complexity", help="整体复杂度报告")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("code-style", help="代码风格检查汇总")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py")
    p.add_argument("--fix", action="store_true")

    p = sub.add_parser("dependency-tree", help="依赖树可视化")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--depth", type=int, default=3)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("env-example", help="生成 .env.example")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--output", "-o")
_STDLIB = {
    "os", "sys", "re", "json", "pathlib", "typing", "collections", "itertools",
    "functools", "abc", "asyncio", "dataclasses", "datetime", "decimal", "enum",
    "errno", "string", "textwrap", "unittest", "logging", "argparse",
    "subprocess", "threading", "socket", "http", "urllib", "html", "csv",
    "copy", "math", "random", "hashlib", "hmac", "secrets", "tempfile", "glob",
    "shutil", "zipfile", "tarfile", "configparser", "tomllib", "traceback",
    "warnings", "contextlib", "inspect", "dis", "pickle", "pprint", "struct",
    "codecs", "unicodedata", "importlib", "pkgutil", "platform", "signal",
    "time", "statistics", "numbers", "operator", "concurrent", "multiprocessing",
    "ctypes", "select", "mmap", "fcntl", "posixpath", "ntpath", "genericpath",
    "fnmatch", "stat", "fileinput", "filecmp", "linecache", "tokenize",
    "token", "keyword", "ast", "symtable", "compileall", "py_compile",
    "zipimport", "pkg_resources", "site", "getopt", "optparse", "readline",
    "rlcompleter", "code", "codeop", "pdb", "profile", "cProfile", "timeit",
    "trace", "distutils", "setuptools", "venv", " Ensurepip", "wheel",
    "builtins", "_thread", "io", "weakref", "types", "gc", "resource",
    "nis", "syslog", "array", "bisect", "heapq", "queue", "selectors",
    "signal", "mimetypes", "webbrowser", "cgi", "cgitb", "wsgiref",
    "xml", "xmlrpc", "ipaddress", "uuid", "ftplib", "poplib", "imaplib",
    "smtplib", "telnetlib", "dircache", "commands", "crypt", "termios",
    "tty", "pty", "fcntl", "posix", "spwd", "grp", "pwd", "resource",
    "nis", "syslog", "ossaudiodev", "aifc", "sunau", "wave", "chunk",
    "colorsys", "imghdr", "sndhdr", "turtle", "turtledemo", "cmd",
}


def cmd_deps(args: argparse.Namespace) -> int:
    from ..utils import detect_framework
    root = Path(args.path).resolve()
    framework = detect_framework(root)
    req_file = root / "requirements.txt"
    deps: dict[str, str] = {}
    if req_file.exists():
        for line in req_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                m = re.match(r"^([a-zA-Z0-9_-]+)", line)
                if m:
                    deps[m.group(1).lower()] = line
    imported: set[str] = set()
    for f in root.rglob("*.py"):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0].lower())
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                if node.module:
                    imported.add(node.module.split(".")[0].lower())
    missing = [d for d in deps if d not in imported and d not in _STDLIB]
    unused = [d for d in deps if d in imported or any(d in i for i in imported)]
    result = {"framework": framework, "total_deps": len(deps), "missing": missing, "potentially_unused": unused}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"📦 框架: {framework}")
        print(f"   总依赖: {len(deps)} 个")
        if missing:
            print(f"   🔍 缺失: {len(missing)} 个")
            for d in missing[:10]:
                print(f"      - {d}")
        if unused:
            print(f"   ⚠️  可能未使用: {len(unused)} 个")
            for d in unused[:10]:
                print(f"      - {d}")
    return 0 if not missing else 1


def cmd_import_graph(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(","))
    imports: dict[str, set[str]] = {}
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            rel = f.relative_to(root).with_suffix("").as_posix().replace("/", ".")
            imports.setdefault(rel, set())
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            except (SyntaxError, OSError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports[rel].add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    if node.module:
                        imports[rel].add(node.module.split(".")[0])
    if args.json:
        print(json.dumps(imports, indent=2))
    else:
        for mod, deps in sorted(imports.items()):
            print(f"  {mod}")
            for d in sorted(deps):
                print(f"    └── {d}")
    return 0


def cmd_todo(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    patterns = [(r"\bTODO\b", "TODO"), (r"\bFIXME\b", "FIXME"), (r"\bHACK\b", "HACK"),
                (r"\bXXX\b", "XXX"), (r"\bWORKAROUND\b", "WORKAROUND"), (r"\bTEMP\b", "TEMP"), (r"\bNOTE\b", "NOTE")]
    results: list[dict] = []
    for f in root.rglob("*"):
        if f.is_file():
            if args.ext and f.suffix.lower() not in tuple(args.ext.split(",")):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                for pat, label in patterns:
                    if re.search(pat, line, re.IGNORECASE):
                        results.append({"file": str(f.relative_to(root)), "line": i, "type": label, "text": line.strip()[:120]})
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        counts: dict[str, int] = {}
        for r in results:
            counts[r["type"]] = counts.get(r["type"], 0) + 1
        print(f"📋 标记汇总: {sum(counts.values())} 条")
        for t, n in sorted(counts.items()):
            print(f"   {t}: {n}")
        for r in results[:30]:
            print(f"  📌 {r['file']}:{r['line']}  [{r['type']}]  {r['text']}")
    return 0

def cmd_test_gen(args: argparse.Namespace) -> int:
    if args.module:
        import importlib
        try:
            mod = importlib.import_module(args.module)
            source_file = Path(getattr(mod, "__file__", ".")).resolve()
        except ImportError:
            source_file = (Path.cwd() / args.module.replace(".", "/").with_suffix(".py")).resolve()
    else:
        source_file = Path.cwd()
    if not source_file.exists():
        print(f"❌ 文件不存在: {source_file}", file=sys.stderr)
        return 1
    try:
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}", file=sys.stderr)
        return 1
    tests: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.decorator_list == []:
            params = [a.arg for a in node.args.args if a.arg != "self"]
            func_name = node.name
            arg_str = ", ".join(params)
            tests.append(f"def test_{func_name}({arg_str}):\n    pass  # TODO\n\n")
    output = Path(args.output) if args.output else (source_file.parent / f"test_{source_file.stem}.py")
    header = f'"""自动生成的测试文件。来源: {source_file.name}"""\nfrom __future__ import annotations\n\n'
    content = header + "\n".join(tests)
    output.write_text(content, encoding="utf-8")
    print(f"✅ 已生成 {len(tests)} 个测试模板 → {output}")
    return 0


def cmd_changelog(args: argparse.Namespace) -> int:
    since = args.since or ""
    cmd = ["log", "--pretty=format:%H|%an|%ad|%s", "--date=short"]
    if since:
        cmd += [f"{since}..HEAD"]
    else:
        cmd += ["--max-count=50"]
    output = subprocess.run(["git", *cmd], capture_output=True, text=True).stdout
    entries = []
    for line in output.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            h, author, date, msg = parts
            entries.append({"hash": h[:8], "author": author, "date": date, "message": msg})
    types = {"feat": [], "fix": [], "docs": [], "refactor": [], "chore": [], "other": []}
    for e in entries:
        msg = e["message"]
        if msg.startswith("feat"): types["feat"].append(e)
        elif msg.startswith("fix"): types["fix"].append(e)
        elif msg.startswith("docs"): types["docs"].append(e)
        elif msg.startswith("refactor"): types["refactor"].append(e)
        elif msg.startswith("chore"): types["chore"].append(e)
        else: types["other"].append(e)
    result = {"entries": entries, "by_type": {k: len(v) for k, v in types.items()}}
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    lines = ["# CHANGELOG", "", f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    labels = {"feat": "✨ 新功能", "fix": "🐛 修复", "docs": "📝 文档", "refactor": "♻️ 重构", "chore": "🔧 维护", "other": "📦 其他"}
    for t, label in labels.items():
        if types[t]:
            lines.append(f"\n## {label}")
            for e in types[t]:
                lines.append(f"- {e['message']} ({e['date']})")
    changelog = "\n".join(lines) + "\n"
    if args.output:
        Path(args.output).write_text(changelog, encoding="utf-8")
        print(f"✅ 已写入 {args.output}")
    else:
        print(changelog)
    return 0


def cmd_schema_gen(args: argparse.Namespace) -> int:
    source = Path(args.path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    schemas: dict[str, dict] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            props: dict[str, dict] = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    ann = item.annotation
                    type_str = "string"
                    if isinstance(ann, ast.Name):
                        type_map = {"str": "string", "int": "integer", "float": "number", "bool": "boolean", "list": "array", "dict": "object"}
                        type_str = type_map.get(ann.id, "string")
                    elif isinstance(ann, ast.Subscript):
                        type_str = "array"
                    props[item.target.id] = {"type": type_str}
            schemas[node.name] = {"type": "object", "properties": props}
    output = Path(args.output) if args.output else (Path(args.path).parent / f"{Path(args.path).stem}.schema.json")
    output.write_text(json.dumps(schemas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Schema 已生成 → {output}")
    return 0


def cmd_doc_gen(args: argparse.Namespace) -> int:
    source = Path(args.path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.decorator_list:
            docstring = ast.get_docstring(node)
            if not docstring:
                params = ", ".join(a.arg for a in node.args.args if a.arg != "self")
                ret = "None"
                if node.returns and isinstance(node.returns, ast.Name):
                    ret = node.returns.id
                new_doc = f'    """{node.name}({params}) -> {ret}"""'
                insert_pos = node.body[0].lineno if node.body else node.end_lineno or node.lineno
                lines.insert(insert_pos - 1, new_doc)
    output = Path(args.output) if args.output else Path(args.path)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 文档注释已添加到 {output}")
    return 0


def cmd_config_gen(args: argparse.Namespace) -> int:
    name = args.name
    config: dict[str, Any] = {"app": {"name": name, "version": "0.1.0", "debug": False},
        "database": {"host": "localhost", "port": 5432, "name": f"{name}_db"},
        "logging": {"level": "INFO", "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        "features": {"enabled": [], "disabled": []}}
    if args.format == "json": content = json.dumps(config, ensure_ascii=False, indent=2)
    elif args.format == "yaml":
        try:
            import yaml
            content = yaml.dump(config, allow_unicode=True, sort_keys=False)
        except ImportError:
            content = json.dumps(config, ensure_ascii=False, indent=2)
    elif args.format == "toml":
        content = f'[app]\nname = "{name}"\nversion = "0.1.0"\ndebug = false\n\n[database]\nhost = "localhost"\nport = 5432\nname = "{name}_db"\n'
    elif args.format == "env":
        content = f'APP_NAME={name}\nAPP_VERSION=0.1.0\nDEBUG=false\nDB_HOST=localhost\nDB_PORT=5432\nDB_NAME={name}_db\n'
    else: content = json.dumps(config, ensure_ascii=False, indent=2)
    output = Path(args.output) if args.output else Path(f"config.{args.format}")
    output.write_text(content, encoding="utf-8")
    print(f"✅ 配置已生成 → {output}")
    return 0


def cmd_makefile_gen(args: argparse.Namespace) -> int:
    name = args.name
    templates = {
        "python": f'# Makefile for {name}\n.PHONY: all install test lint format clean help\n\nall: test\n\ninstall:\n\tpip install -e ".[dev]"\n\ntest:\n\tpytest tests/ -v --tb=short\n\nlint:\n\truff check .\n\tmypy .\n\nformat:\n\truff format .\n\nclean:\n\trm -rf .pytest_cache .ruff_cache __pycache__ *.egg-info dist build\n\nhelp:\n\t@echo "Targets: all install test lint format clean help"\n',
        "node": f'# Makefile for {name}\n.PHONY: all install test lint format clean help\n\nall: test\n\ninstall:\n\tnpm install\n\ntest:\n\tnpm test\n\nlint:\n\tnpx eslint .\n\nformat:\n\tnpx prettier --write .\n\nclean:\n\trm -rf node_modules dist build\n\nhelp:\n\t@echo "Targets: all install test lint format clean help"\n',
    }
    content = templates.get(args.lang, templates["python"])
    output = Path(args.output)
    output.write_text(content, encoding="utf-8")
    print(f"✅ Makefile 已生成 → {output}")
    return 0

def cmd_docker_gen(args: argparse.Namespace) -> int:
    base = args.base or {"python": "python:3.11-slim", "node": "node:22-slim", "go": "golang:1.22-slim", "rust": "rust:1.75-slim"}.get(args.lang, "python:3.11-slim")
    dockerfile = f'''# Auto-generated Dockerfile
FROM {base}
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {args.port}
CMD ["python", "-m", "app"]
'''
    output = Path(args.output)
    output.write_text(dockerfile, encoding="utf-8")
    print(f"✅ Dockerfile 已生成 → {output}")
    return 0


def cmd_ci_gen(args: argparse.Namespace) -> int:
    ci_content = '''# Auto-generated GitHub Actions CI
name: CI
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v5
      with:
        python-version: ${{{{ matrix.python-version }}}}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    - name: Lint
      run: ruff check .
    - name: Test
      run: pytest tests/ -v --tb=short
'''
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(ci_content, encoding="utf-8")
    print(f"✅ CI 配置已生成 → {output}")
    return 0


def cmd_package_gen(args: argparse.Namespace) -> int:
    name = args.name
    if args.type == "python":
        content = f'''[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "Project {name}"
readme = "README.md"
license = {{text = "MIT"}}
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.4.0"]

[tool.setuptools.packages.find]
include = ["{name.replace("-", "_")}*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
'''
    else:
        content = f'{{\n  "name": "{name}",\n  "version": "0.1.0",\n  "description": "Project {name}",\n  "main": "index.js",\n  "scripts": {{"test": "echo \\"Error: no test specified\\" && exit 1"}},\n  "license": "MIT"\n}}\n'
    output = Path(args.output) if args.output else (Path("pyproject.toml") if args.type == "python" else Path("package.json"))
    output.write_text(content, encoding="utf-8")
    print(f"✅ 包配置已生成 → {output}")
    return 0


def cmd_init_project(args: argparse.Namespace) -> int:
    name = args.name
    output = Path(args.output).resolve()
    pkg_name = name.replace("-", "_")
    (output / pkg_name).mkdir(parents=True, exist_ok=True)
    (output / "tests").mkdir(parents=True, exist_ok=True)
    (output / pkg_name / "__init__.py").write_text(f'"""{name} package."""\n', encoding="utf-8")
    (output / pkg_name / "__main__.py").write_text(f'"""{name} entry point."""\nfrom .main import main\n\nif __name__ == "__main__":\n    main()\n', encoding="utf-8")
    (output / pkg_name / "main.py").write_text(f'"""{name} main module."""\nfrom __future__ import annotations\nimport argparse\n\ndef main() -> int:\n    parser = argparse.ArgumentParser(prog="{name}")\n    parser.add_argument("--version", action="version", version=f"{{name}} 0.1.0")\n    return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n', encoding="utf-8")
    (output / "tests" / "test_main.py").write_text(f'"""Tests for {name}."""\nfrom {pkg_name}.main import main\n\ndef test_main():\n    assert main() == 0\n', encoding="utf-8")
    (output / "README.md").write_text(f'# {name}\n\nProject {name}\n', encoding="utf-8")
    (output / ".gitignore").write_text("__pycache__/\n*.py[cod]\n.venv/\n*.egg-info/\n.pytest_cache/\n", encoding="utf-8")
    if args.with_tests:
        (output / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n", encoding="utf-8")
    if args.with_ci:
        ci_dir = output / ".github" / "workflows"
        ci_dir.mkdir(parents=True, exist_ok=True)
        (ci_dir / "ci.yml").write_text("name: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n      - run: pip install -e '.[dev]'\n      - run: pytest tests/ -v\n", encoding="utf-8")
    print(f"✅ 项目已初始化 → {output}")
    return 0


def cmd_license(args: argparse.Namespace) -> int:
    year = args.year or str(datetime.now().year)
    author = args.author or "Unnamed"
    templates = {
        "mit": f'MIT License\n\nCopyright (c) {year} {author}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction...\n',
        "apache2": f'Apache License\nVersion 2.0, January 2004\n\nCopyright {year} {author}\n\nLicensed under the Apache License, Version 2.0...\n',
    }
    content = templates.get(args.type, templates["mit"])
    output = Path(args.output)
    output.write_text(content, encoding="utf-8")
    print(f"✅ License 已生成 → {output}")
    return 0


def cmd_hook_gen(args: argparse.Namespace) -> int:
    hooks = {
        "pre-commit": "#!/bin/sh\necho 'Running pre-commit checks...'\nexit 0\n",
        "commit-msg": '#!/bin/sh\nCOMMIT_MSG=$(cat "$1")\nif ! echo "$COMMIT_MSG" | grep -qE "^(feat|fix|docs|refactor|chore)(\\(.+\\))?: .+" ; then\n    echo "⚠️  Use Conventional Commits"\nfi\n',
    }
    content = hooks.get(args.name, f"#!/bin/sh\n# {args.name} hook\n")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    output.chmod(0o755)
    print(f"✅ Hook 已生成 → {output}")
    return 0


def cmd_error_check(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(","))
    results: list[dict] = []
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None:
                        results.append({"file": str(f.relative_to(root)), "line": node.lineno, "issue": "bare except", "severity": "HIGH"})
                    elif isinstance(node.type, ast.Tuple) and any(isinstance(e, ast.Name) and e.id == "Exception" for e in node.type.elts):
                        results.append({"file": str(f.relative_to(root)), "line": node.lineno, "issue": "broad exception", "severity": "MEDIUM"})
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if not results:
            print("✅ 未发现未处理异常")
            return 0
        print(f"🔍 发现 {len(results)} 处异常处理问题")
        for r in results:
            print(f"  ⚠️  {r['file']}:{r['line']}  [{r['severity']}]  {r['issue']}")
    return 1 if results else 0


def cmd_unused_imports(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(","))
    results: list[dict] = []
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            except SyntaxError:
                continue
            imports: dict[str, int] = {}
            names_in_code: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports[alias.asname or alias.name.split(".")[0]] = node.lineno
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    if node.module:
                        for alias in node.names:
                            imports[alias.asname or alias.name] = node.lineno
                elif isinstance(node, ast.Name):
                    names_in_code.add(node.id)
            for name, lineno in imports.items():
                if name not in names_in_code and name != "self":
                    results.append({"file": str(f.relative_to(root)), "line": lineno, "import": name})
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if not results:
            print("✅ 无未使用 import")
            return 0
        print(f"🔍 发现 {len(results)} 处未使用 import")
        for r in results:
            print(f"  ⚠️  {r['file']}:{r['line']}  {r['import']}")
    return 0

def _cyclomatic_complexity(func_node) -> int:
    complexity = 1
    for node in ast.walk(func_node):
        if isinstance(node, (ast.If, ast.While, ast.For)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, ast.ExceptHandler):
            complexity += 1
        elif isinstance(node, ast.Assert):
            complexity += 1
    return complexity


def cmd_ast_dump(args: argparse.Namespace) -> int:
    import ast as _ast
    tree = _ast.parse(Path(args.path).read_text(encoding="utf-8"))
    print(_ast.dump(tree, indent=2))
    return 0


def cmd_function_count(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(","))
    total = 0
    per_file: dict[str, int] = {}
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            count = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
            if count > 0:
                per_file[str(f.relative_to(root))] = count
                total += count
    if args.json:
        print(json.dumps({"total": total, "by_file": per_file}, indent=2))
    else:
        print(f"📊 函数统计: {total} 个函数")
        for f, n in sorted(per_file.items(), key=lambda x: -x[1])[:20]:
            print(f"   {n:>4}  {f}")
    return 0


def cmd_complexity(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(","))
    results: list[dict] = []
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    c = _cyclomatic_complexity(node)
                    if c > 1:
                        results.append({"file": str(f.relative_to(root)), "function": node.name, "line": node.lineno, "complexity": c})
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        high = [r for r in results if r["complexity"] > args.max]
        if high:
            print(f"⚠️  {len(high)} 个函数圈复杂度 > {args.max}")
            for r in sorted(high, key=lambda x: -x["complexity"])[:10]:
                print(f"   {r['complexity']:>3}  {r['file']}:{r['line']}  {r['function']}")
        else:
            print(f"✅ 所有函数复杂度 ≤ {args.max}")
    return 1 if high else 0


def cmd_code_style(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(","))
    issues: list[dict] = []
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                text = f.read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if len(line) > 100:
                    issues.append({"file": str(f.relative_to(root)), "line": i, "issue": "line too long", "severity": "LOW"})
                if line.rstrip() != line:
                    issues.append({"file": str(f.relative_to(root)), "line": i, "issue": "trailing whitespace", "severity": "LOW"})
    if args.fix:
        for f in root.rglob("*"):
            if f.is_file() and f.suffix.lower() in exts:
                try:
                    text = f.read_text(encoding="utf-8")
                except OSError:
                    continue
                fixed = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
                if fixed != text:
                    f.write_text(fixed, encoding="utf-8")
    if args.json:
        print(json.dumps(issues, indent=2))
    else:
        print(f"📋 代码风格: {len(issues)} 处问题")
        for iss in issues[:20]:
            print(f"  ⚠️  {iss['file']}:{iss['line']}  {iss['issue']}")
    return 0 if not issues else 1


def cmd_dependency_tree(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    deps: dict[str, list[str]] = {}
    for f in root.rglob("*.py"):
        rel = f.relative_to(root).with_suffix("").as_posix().replace("/", ".")
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                if node.module:
                    imports.add(node.module.split(".")[0])
        deps[rel] = sorted(imports)
    def _print_tree(node: str, depth: int = 0, visited: set[str] | None = None) -> None:
        if visited is None:
            visited = set()
        if node in visited or depth > args.depth:
            return
        visited.add(node)
        indent = "  " * depth
        prefix = "└── " if depth > 0 else ""
        print(f"{indent}{prefix}{node}")
        for dep in deps.get(node, [])[:5]:
            _print_tree(dep, depth + 1, visited.copy())
    _print_tree(list(deps.keys())[0] if deps else "root")
    return 0


def cmd_env_example(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    patterns = [(r"(?i)(PASSWORD|PASSWD|PWD)\s*=\s*(.+)", "password"), (r"(?i)(API_KEY|SECRET|TOKEN)\s*=\s*(.+)", "secret"),
                (r"(?i)(DATABASE_URL|DB_URL)\s*=\s*(.+)", "url"), (r"(?i)(HOST|PORT|URL)\s*=\s*(.+)", "host"),
                (r"(?i)(DEBUG|VERBOSE)\s*=\s*(.+)", "flag")]
    found: dict[str, str] = {}
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".env", ".env.example", ".env.local"):
            try:
                text = f.read_text(encoding="utf-8")
            except OSError:
                continue
            for pat, category in patterns:
                for m in re.finditer(pat, text):
                    key = m.group(1).strip()
                    val = m.group(2).strip()
                    if key not in found:
                        found[key] = val
    output = Path(args.output) if args.output else root / ".env.example"
    lines = ["# Environment variables for this project", "", ""]
    for key, val in sorted(found.items()):
        lines.append(f"# {key} — {val}")
        lines.append(f"{key}=")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ .env.example 已生成 → {output}")
    return 0
