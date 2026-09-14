"""agent-tools 入口 - 带命令分发逻辑。"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


VERSION = "1.0.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="at",
        description="Agent 超级工具集 — 两三百个实用 CLI 命令，一个入口",
        epilog=f"version {VERSION} · 输入 'at <category> <command> --help' 查看帮助",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"agent-tools {VERSION}")

    sub = parser.add_subparsers(dest="category", required=True)

    # ── 1. file: 文件与代码操作 ──────────────────────────────
    p_file = sub.add_parser("file", help="文件与代码操作 (30+ 命令)")
    _add_file_cmds(p_file)

    # ── 2. text: 文本处理 ────────────────────────────────────
    p_text = sub.add_parser("text", help="文本处理 (25+ 命令)")
    _add_text_cmds(p_text)

    # ── 3. data: 数据格式转换 ────────────────────────────────
    p_data = sub.add_parser("data", help="数据格式转换 (18+ 命令)")
    _add_data_cmds(p_data)

    # ── 4. git: Git 增强工具 ────────────────────────────────
    p_git = sub.add_parser("git", help="Git 增强工具 (15+ 命令)")
    _add_git_cmds(p_git)

    # ── 5. security: 安全扫描 ───────────────────────────────
    p_sec = sub.add_parser("security", help="安全扫描 (14+ 命令)")
    _add_security_cmds(p_sec)

    # ── 6. dev: 开发辅助 ────────────────────────────────────
    p_dev = sub.add_parser("dev", help="开发辅助 (25+ 命令)")
    _add_dev_cmds(p_dev)

    # ── 7. ai: AI / Agent 工具 ─────────────────────────────
    p_ai = sub.add_parser("ai", help="AI / Agent 工具 (12+ 命令)")
    _add_ai_cmds(p_ai)

    # ── 8. infra: 基础设施 ──────────────────────────────────
    p_infra = sub.add_parser("infra", help="基础设施 (16+ 命令)")
    _add_infra_cmds(p_infra)

    # ── 9. meta: 项目元信息 ─────────────────────────────────
    p_meta = sub.add_parser("meta", help="项目元信息 (8+ 命令)")
    _add_meta_cmds(p_meta)

    # ── 10. system: 系统工具 ────────────────────────────────
    p_sys = sub.add_parser("system", help="系统工具 (18+ 命令)")
    _add_system_cmds(p_sys)

    # ── 11. web: Web 工具 ───────────────────────────────────
    p_web = sub.add_parser("web", help="Web 工具 (14+ 命令)")
    _add_web_cmds(p_web)

    args = parser.parse_args()
    if not hasattr(args, "cmd"):
        parser.print_help()
        return 0

    # 动态查找并调用命令函数
    cmd_name = args.cmd
    category = args.category
    func_name = "cmd_" + cmd_name.replace("-", "_")

    try:
        mod = importlib.import_module(f"agent_tools.cmd.{category}")
        func = getattr(mod, func_name)
    except (ImportError, AttributeError):
        print(f"Error: unknown command '{category} {cmd_name}'", file=sys.stderr)
        return 2

    return func(args)


# ─── 各分类子命令注册 ───────────────────────────────────────────────────
def _add_file_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.file import register
    register(parent)

def _add_text_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.text import register
    register(parent)

def _add_data_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.data import register
    register(parent)

def _add_git_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.git import register
    register(parent)

def _add_security_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.security import register
    register(parent)

def _add_dev_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.dev import register
    register(parent)

def _add_ai_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.ai import register
    register(parent)

def _add_infra_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.infra import register
    register(parent)

def _add_meta_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.meta import register
    register(parent)

def _add_system_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.system import register
    register(parent)

def _add_web_cmds(parent: argparse.ArgumentParser) -> None:
    from agent_tools.cmd.web import register
    register(parent)


if __name__ == "__main__":
    sys.exit(main())
