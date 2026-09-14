"""system: 系统工具。"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def register(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("info", help="系统信息")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("disk", help="磁盘空间")
    p.add_argument("--path", nargs="?", default="/")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("mem", help="内存使用")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("cpu", help="CPU 信息")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("process", help="进程管理")
    p.add_argument("--filter", help="过滤进程名")
    p.add_argument("--sort", choices=["cpu", "mem", "pid"], default="pid")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("kill", help="终止进程")
    p.add_argument("pid", type=int)
    p.add_argument("--signal", type=int, default=15)

    p = sub.add_parser("env-show", help="环境变量查看")
    p.add_argument("--key", help="指定键")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("path-show", help="PATH 分析")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("which", help="查找命令路径")
    p.add_argument("command")

    p = sub.add_parser("clipboard", help="剪贴板操作")
    p.add_argument("--copy", help="复制到剪贴板")
    p.add_argument("--paste", action="store_true")

    p = sub.add_parser("sleep", help="延迟执行")
    p.add_argument("--seconds", type=float, default=1)
    p.add_argument("--command", help="延迟后执行的命令")

    p = sub.add_parser("watch", help="持续监控")
    p.add_argument("command")
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--times", type=int, default=0, help="0=无限")

    p = sub.add_parser("benchmark", help="性能基准测试")
    p.add_argument("--code", help="测试代码字符串")
    p.add_argument("--file", help="测试代码文件")
    p.add_argument("--iters", type=int, default=1000)

    p = sub.add_parser("timeit", help="代码计时")
    p.add_argument("--code", required=True)
    p.add_argument("--iters", type=int, default=100)

    p = sub.add_parser("random", help="随机数生成")
    p.add_argument("--min", type=int, default=0)
    p.add_argument("--max", type=int, default=100)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--seed", type=int, default=None)

    p = sub.add_parser("date", help="日期工具")
    p.add_argument("--format", default="%Y-%m-%d %H:%M:%S")
    p.add_argument("--add", help="添加时间如 +1d +2h +30m")
    p.add_argument("--diff", help="计算两个日期差")

    p = sub.add_parser("hash", help="哈希计算")
    p.add_argument("input", help="文件或文本")
    p.add_argument("--algo", choices=["md5", "sha1", "sha256", "sha512"], default="sha256")
    p.add_argument("--text", action="store_true", help="输入是文本而非文件")

    p = sub.add_parser("unicode", help="Unicode 工具")
    p.add_argument("--encode", help="转义为 Unicode 码点")
    p.add_argument("--decode", help="从码点还原")
    p.add_argument("--table", help="显示字符表")

    p = sub.add_parser("terminal", help="终端信息")
    p.add_argument("--width", action="store_true")
    p.add_argument("--height", action="store_true")
    p.add_argument("--clear", action="store_true")
def cmd_info(args: argparse.Namespace) -> int:
    result = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "uptime_seconds": time.time() - os.stat("/proc" if os.path.exists("/proc") else ".").st_mtime if os.path.exists("/proc") else 0,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"🖥️  系统信息")
        print(f"   平台: {result['platform']}")
        print(f"   系统: {result['system']} {result['release']}")
        print(f"   架构: {result['machine']}")
        print(f"   Python: {result['python_version']}")
        print(f"   主机: {result['hostname']}")
    return 0


def cmd_disk(args: argparse.Namespace) -> int:
    import shutil
    total, used, free = shutil.disk_usage(args.path)
    result = {
        "path": args.path,
        "total_gb": round(total / 1073741824, 2),
        "used_gb": round(used / 1073741824, 2),
        "free_gb": round(free / 1073741824, 2),
        "percent_used": round(used / total * 100, 1) if total > 0 else 0,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"💾 磁盘空间: {result['path']}")
        print(f"   总容量: {result['total_gb']} GB")
        print(f"   已用:   {result['used_gb']} GB ({result['percent_used']}%)")
        print(f"   可用:   {result['free_gb']} GB")
    return 0


def cmd_mem(args: argparse.Namespace) -> int:
    try:
        import psutil
    except ImportError:
        psutil = None
    try:
        import psutil
        vm = psutil.virtual_memory()
        result = {
            "total_gb": round(vm.total / 1073741824, 2),
            "available_gb": round(vm.available / 1073741824, 2),
            "used_gb": round(vm.used / 1073741824, 2),
            "percent": vm.percent,
        }
    except ImportError:
        result = {"total_gb": 0, "available_gb": 0, "used_gb": 0, "percent": 0, "note": "psutil not installed"}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"🧠 内存使用")
        print(f"   总内存: {result.get('total_gb', 'N/A')} GB")
        print(f"   可用:   {result.get('available_gb', 'N/A')} GB")
        print(f"   使用率: {result.get('percent', 0)}%")
    return 0


def cmd_cpu(args: argparse.Namespace) -> int:
    result = {
        "cores_physical": os.cpu_count(),
        "cores_logical": len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else os.cpu_count(),
        "load_avg": os.getloadavg()[:3] if hasattr(os, 'getloadavg') else [],
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"🔧 CPU 信息")
        print(f"   物理核: {result['cores_physical']}")
        print(f"   逻辑核: {result['cores_logical']}")
    return 0


def cmd_process(args: argparse.Namespace) -> int:
    import psutil
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "create_time"]):
        try:
            if args.filter and args.filter.lower() not in p.info["name"].lower():
                continue
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    sort_key = {"cpu": lambda x: x.get("cpu_percent", 0), "mem": lambda x: x.get("memory_percent", 0), "pid": lambda x: x.get("pid", 0)}
    procs.sort(key=sort_key.get(args.sort, sort_key["pid"]), reverse=True)
    if args.json:
        print(json.dumps(procs[:50], indent=2, default=str))
    else:
        print(f"📊 进程列表 ({len(procs)} 个)")
        for p in procs[:20]:
            print(f"  PID {p['pid']:>6}  {p['cpu_percent']:>5.1f}% CPU  {p['memory_percent']:>5.1f}% MEM  {p['name']}")
    return 0


def cmd_kill(args: argparse.Namespace) -> int:
    try:
        import signal
        os.kill(args.pid, args.signal)
        print(f"  ✅ 已发送信号 {args.signal} 到 PID {args.pid}")
    except ProcessLookupError:
        print(f"  ❌ 进程 {args.pid} 不存在", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"  ❌ 权限不足", file=sys.stderr)
        return 1
    return 0


def cmd_env_show(args: argparse.Namespace) -> int:
    if args.key:
        print(os.environ.get(args.key, "(未设置)"))
    elif args.json:
        print(json.dumps(dict(os.environ), indent=2, default=str))
    else:
        for k, v in sorted(os.environ.items()):
            if not k.startswith("_"):
                print(f"  {k}={v[:80]}{'...' if len(v) > 80 else ''}")
    return 0


def cmd_path_show(args: argparse.Namespace) -> int:
    paths = os.environ.get("PATH", "").split(os.pathsep)
    if args.json:
        print(json.dumps(paths, indent=2))
    else:
        print(f"📂 PATH ({len(paths)} 项):")
        for p in paths:
            exists = "✓" if Path(p).exists() else "✗"
            print(f"  {exists} {p}")
    return 0


def cmd_which(args: argparse.Namespace) -> int:
    result = shutil.which(args.command)
    if result:
        print(f"  {args.command} → {result}")
    else:
        print(f"  ❌ 未找到: {args.command}", file=sys.stderr)
        return 1
    return 0


def cmd_clipboard(args: argparse.Namespace) -> int:
    import subprocess as sp
    if args.copy:
        sp.run(["powershell", "-Command", "Set-Clipboard -Value", args.copy], check=False)
        print(f"  ✅ 已复制到剪贴板")
    elif args.paste:
        r = sp.run(["powershell", "-Command", "Get-Clipboard"], capture_output=True, text=True)
        print(r.stdout.strip())
    return 0


def cmd_sleep(args: argparse.Namespace) -> int:
    time.sleep(args.seconds)
    if args.command:
        os.system(args.command)
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    import subprocess as sp
    times = args.times
    i = 0
    while times == 0 or i < times:
        r = sp.run(args.command, shell=True, capture_output=True, text=True)
        print(r.stdout)
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        time.sleep(args.interval)
        i += 1
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    import time
    code = args.code or ""
    if args.file:
        code = Path(args.file).read_text(encoding="utf-8")
    start = time.perf_counter()
    for _ in range(args.iters):
        exec(code)
    elapsed = time.perf_counter() - start
    print(f"  ⏱️  {args.iters} 次迭代: {elapsed:.4f}s")
    print(f"     平均: {elapsed/args.iters*1000:.4f}ms/次")
    return 0


def cmd_timeit(args: argparse.Namespace) -> int:
    import time
    start = time.perf_counter()
    for _ in range(args.iters):
        exec(args.code)
    elapsed = time.perf_counter() - start
    print(f"  {elapsed:.4f}s  ({args.iters} 次)")
    return 0


def cmd_random(args: argparse.Namespace) -> int:
    import random
    rng = random.Random(args.seed)
    for _ in range(args.count):
        print(rng.randint(args.min, args.max))
    return 0


def cmd_date(args: argparse.Namespace) -> int:
    now = datetime.now()
    if args.format:
        print(now.strftime(args.format))
    if args.add:
        from datetime import timedelta
        td = timedelta()
        for part in args.add.replace(",", " ").split():
            if part.startswith("+"):
                part = part[1:]
            m = __import__("re").match(r"(\d+)([dhms])", part)
            if m:
                n, unit = int(m.group(1)), m.group(2)
                if unit == "d": td += timedelta(days=n)
                elif unit == "h": td += timedelta(hours=n)
                elif unit == "m": td += timedelta(minutes=n)
                elif unit == "s": td += timedelta(seconds=n)
        print((now + td).strftime(args.format))
    return 0


def cmd_hash(args: argparse.Namespace) -> int:
    import hashlib
    algo = hashlib.new(args.algo)
    if args.text:
        algo.update(args.input.encode())
        print(f"{algo.hexdigest()}  {args.input[:40]}")
    else:
        data = Path(args.input).read_bytes()
        algo.update(data)
        print(f"{algo.hexdigest()}  {args.input}  ({len(data)} bytes)")
    return 0


def cmd_unicode(args: argparse.Namespace) -> int:
    if args.encode:
        print(" ".join(f"U+{ord(c):04X}" for c in args.encode))
    elif args.decode:
        import re
        codepoints = re.findall(r"U\+([0-9A-Fa-f]{4})", args.decode)
        print("".join(chr(int(cp, 16)) for cp in codepoints))
    elif args.table:
        for c in args.table:
            print(f"  '{c}' = U+{ord(c):04X} = {ord(c)}")
    return 0


def cmd_terminal(args: argparse.Namespace) -> int:
    try:
        cols, rows = shutil.get_terminal_size((80, 24))
        if args.width:
            print(cols)
        elif args.height:
            print(rows)
        elif args.clear:
            os.system("cls" if os.name == "nt" else "clear")
        else:
            print(f"  终端: {cols}x{rows}")
    except Exception:
        print("  无法获取终端尺寸")
    return 0
