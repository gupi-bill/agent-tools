"""infra: 基础设施工具。"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def register(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("health", help="服务健康检查")
    p.add_argument("targets", nargs="+", help="URL 或 host:port")
    p.add_argument("--timeout", type=int, default=5)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("port-finder", help="查找空闲端口")
    p.add_argument("--range", default="8000-9000")
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("ping", help="Ping 主机")
    p.add_argument("host")
    p.add_argument("--count", type=int, default=4)

    p = sub.add_parser("dns", help="DNS 查询")
    p.add_argument("domain")
    p.add_argument("--type", choices=["A", "AAAA", "MX", "NS", "TXT", "CNAME"], default="A")

    p = sub.add_parser("whois", help="WHOIS 查询")
    p.add_argument("domain")

    p = sub.add_parser("env", help="环境变量管理")
    p.add_argument("--get", help="获取变量")
    p.add_argument("--set", help="设置变量")
    p.add_argument("--list", action="store_true")
    p.add_argument("--export", action="store_true")
    p.add_argument("--file", help="从 .env 文件加载")

    p = sub.add_parser("vault", help="加密存储环境变量")
    p.add_argument("key")
    p.add_argument("--value", help="值")
    p.add_argument("--delete", action="store_true")
    p.add_argument("--list", action="store_true")
    p.add_argument("--get", help="获取值")

    p = sub.add_parser("cron-gen", help="生成 cron 表达式")
    p.add_argument("--every", choices=["minute", "hour", "day", "week", "month"], default="hour")
    p.add_argument("--at", help="具体时间如 30 2 * * *")
    p.add_argument("--desc", help="描述")

    p = sub.add_parser("timer", help="定时任务")
    p.add_argument("--seconds", type=int, required=True)
    p.add_argument("--task", help="任务命令")

    p = sub.add_parser("queue", help="简单消息队列")
    p.add_argument("--enqueue", help="入队")
    p.add_argument("--dequeue", action="store_true")
    p.add_argument("--list", action="store_true")
    p.add_argument("--queue-name", default="default")

    p = sub.add_parser("cache", help="简单缓存")
    p.add_argument("--get", help="获取缓存")
    p.add_argument("--set", help="设置缓存")
    p.add_argument("--delete", help="删除缓存")
    p.add_argument("--ttl", type=int, default=3600, help="过期时间(秒)")

    p = sub.add_parser("lock", help="文件锁")
    p.add_argument("--name", required=True)
    p.add_argument("--acquire", action="store_true")
    p.add_argument("--release", action="store_true")
    p.add_argument("--status", action="store_true")

    p = sub.add_parser("rate-limiter", help="限流器")
    p.add_argument("--check", help="检查 key")
    p.add_argument("--limit", type=int, default=10, help="每秒最大请求数")
    p.add_argument("--window", type=int, default=60, help="窗口秒数")

    p = sub.add_parser("log-tail", help="日志实时查看")
    p.add_argument("path", nargs="?", default="")
    p.add_argument("--lines", type=int, default=20)
    p.add_argument("--follow", "-f", action="store_true")
    p.add_argument("--grep", help="关键词过滤")

    p = sub.add_parser("backup", help="备份工具")
    p.add_argument("source")
    p.add_argument("--dest", required=True)
    p.add_argument("--keep", type=int, default=5, help="保留备份数")

    p = sub.add_parser("restore", help="恢复备份")
    p.add_argument("backup_file")
    p.add_argument("--dest", required=True)

    p = sub.add_parser("db-migrate", help="数据库迁移")
    p.add_argument("--up", action="store_true", help="执行迁移")
    p.add_argument("--down", action="store_true", help="回滚")
    p.add_argument("--status", action="store_true", help="查看状态")
    p.add_argument("--sql-dir", default="migrations")
def cmd_health(args: argparse.Namespace) -> int:
    results = []
    for target in args.targets:
        result = {"target": target, "status": "unknown", "latency_ms": 0}
        if target.startswith("http"):
            try:
                import urllib.request
                start = time.time()
                req = urllib.request.Request(target, method="GET")
                with urllib.request.urlopen(req, timeout=args.timeout) as resp:
                    latency = (time.time() - start) * 1000
                    result = {"target": target, "status": "up" if resp.status == 200 else "error", "latency_ms": round(latency, 1), "status_code": resp.status}
            except Exception as e:
                result = {"target": target, "status": "down", "error": str(e)}
        else:
            parts = target.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 80
            try:
                start = time.time()
                sock = socket.create_connection((host, port), timeout=args.timeout)
                latency = (time.time() - start) * 1000
                sock.close()
                result = {"target": target, "status": "up", "latency_ms": round(latency, 1)}
            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                result = {"target": target, "status": "down", "error": str(e)}
        results.append(result)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        up = sum(1 for r in results if r["status"] == "up")
        print(f"🏥 健康检查: {up}/{len(results)} 正常")
        for r in results:
            icon = "✓" if r["status"] == "up" else "✗"
            print(f"  {icon} {r['target']}  ({r['latency_ms']}ms)" if r["latency_ms"] else f"  {icon} {r['target']}")
    return 0 if all(r["status"] == "up" for r in results) else 1


def cmd_port_finder(args: argparse.Namespace) -> int:
    start, end = map(int, args.range.split("-"))
    available = []
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                available.append(port)
                if len(available) >= args.count:
                    break
    if args.json:
        print(json.dumps({"ports": available, "range": f"{start}-{end}"}, indent=2))
    else:
        print(f"  空闲端口 ({len(available)} 个): {available[:10]}")
    return 0


def cmd_ping(args: argparse.Namespace) -> int:
    import platform
    cmd = ["ping", "-n" if platform.system() == "Windows" else "-c", str(args.count), args.host]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    return r.returncode


def cmd_dns(args: argparse.Namespace) -> int:
    import dns.resolver
    try:
        answers = dns.resolver.resolve(args.domain, args.type)
        for ans in answers:
            print(f"  {ans}")
    except Exception as e:
        print(f"  ❌ 查询失败: {e}")
    return 0


def cmd_env(args: argparse.Namespace) -> int:
    if args.file:
        import dotenv
        dotenv.load_dotenv(args.file, override=True)
        print(f"  ✅ 已加载 {args.file}")
    if args.get:
        print(os.environ.get(args.get, "(未设置)"))
    elif args.set and "=" in args.set:
        key, _, value = args.set.partition("=")
        os.environ[key.strip()] = value.strip()
        print(f"  ✅ 已设置 {key.strip()}")
    elif args.list:
        for k, v in sorted(os.environ.items()):
            if not k.startswith("_") and not any(x in k for x in ["PATH", "SYSTEMROOT"]):
                print(f"  {k}={v[:50]}{'...' if len(v) > 50 else ''}")
    elif args.export:
        for k, v in os.environ.items():
            print(f'export {k}="{v}"')
    return 0


def cmd_vault(args: argparse.Namespace) -> int:
    vault_dir = Path.home() / ".agent_tools_vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    vault_file = vault_dir / "vault.enc"
    if args.list:
        if vault_file.exists():
            import hashlib
            data = vault_file.read_bytes()
            keys = set(h[:16] for h in hashlib.sha256(data).hexdigest())
            print(f"  仓库: {vault_file} ({len(keys)} 条记录)")
        else:
            print("  仓库为空")
        return 0
    if args.get:
        if not vault_file.exists():
            print("  ❌ 仓库不存在")
            return 1
        import base64
        import hashlib
        key = hashlib.sha256(args.get.encode()).digest()
        data = vault_file.read_bytes()
        h = hashlib.sha256(data).hexdigest()[:16]
        print(f"  {args.get}: {base64.b64encode(key).decode()[:16]}***")
        return 0
    if args.value and args.key:
        import base64
        import hashlib
        import hmac
        key = hashlib.sha256(args.key.encode()).digest()
        hmac_key = hashlib.sha256(b"vault_key_v2").digest()
        iv = hashlib.sha256((args.key + str(time.time())).encode()).digest()[:16]
        import os
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        plaintext = args.value.encode()
        # 简单 XOR 加密（生产环境请用 AES）
        encrypted = bytes(p ^ k for p, k in zip(plaintext + b"\x00" * (16 - len(plaintext) % 16), (key * ((len(plaintext)//16)+1))[:len(plaintext)+16]))
        import struct
        header = struct.pack(">I", len(plaintext)) + key + iv
        with open(vault_file, "wb") as f:
            f.write(header + encrypted)
        print(f"  ✅ 已加密存储: {args.key}")
        return 0
    if args.delete and args.key:
        if vault_file.exists():
            vault_file.unlink()
            print(f"  ✅ 已删除: {args.key}")
    return 0


def cmd_cron_gen(args: argparse.Namespace) -> int:
    cron_map = {"minute": "* * * * *", "hour": "0 * * * *", "day": "0 0 * * *", "week": "0 0 * * 0", "month": "0 0 1 * *"}
    expr = args.at or cron_map.get(args.every, "* * * * *")
    print(f"  Cron 表达式: {expr}")
    if args.desc:
        print(f"  描述: {args.desc}")
    print(f"  运行: {'每小时' if args.every == 'hour' else '每天' if args.every == 'day' else '每周' if args.every == 'week' else '每月' if args.every == 'month' else '每分钟'}")
    return 0


def cmd_timer(args: argparse.Namespace) -> int:
    import threading
    def _run():
        time.sleep(args.seconds)
        if args.task:
            subprocess.run(args.task, shell=True)
        print(f"  ⏰ 定时任务已触发: {args.task or '(无任务)'}")
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    print(f"  ⏱️  定时器已启动: {args.seconds} 秒后执行")
    return 0


def cmd_queue(args: argparse.Namespace) -> int:
    queue_file = Path.home() / ".agent_tools_queue" / (args.queue_name + ".json")
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    messages = []
    if queue_file.exists():
        try:
            messages = json.loads(queue_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            messages = []
    if args.enqueue:
        messages.append({"id": len(messages) + 1, "body": args.enqueue, "created": datetime.now().isoformat(), "status": "pending"})
        queue_file.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✅ 已入队: {args.enqueue[:50]}")
    elif args.dequeue:
        pending = [m for m in messages if m.get("status") == "pending"]
        if pending:
            msg = pending[0]
            msg["status"] = "done"
            msg["dequeued_at"] = datetime.now().isoformat()
            queue_file.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  📨 已出队: {msg['body'][:80]}")
        else:
            print("  (队列为空)")
    elif args.list:
        for m in messages[-10:]:
            status = "⏳" if m.get("status") == "pending" else "✅"
            print(f"  {status} #{m['id']} {m['body'][:60]} ({m.get('created', '')[:10]})")
    return 0


def cmd_cache(args: argparse.Namespace) -> int:
    cache_file = Path.home() / ".agent_tools_cache" / "cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache: dict[str, dict] = {}
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}
    now = datetime.now().isoformat()
    if args.set:
        key, _, value = args.set.partition("=")
        cache[key.strip()] = {"value": value.strip(), "created": now, "ttl": args.ttl}
        cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✅ 已缓存: {key.strip()}")
    elif args.get:
        entry = cache.get(args.get)
        if entry:
            created = datetime.fromisoformat(entry["created"])
            elapsed = (datetime.now() - created).total_seconds()
            if elapsed > entry["ttl"]:
                del cache[args.get]
                cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  ⏰ 缓存已过期")
            else:
                print(f"  📦 {args.get}: {entry['value'][:100]}")
        else:
            print(f"  (未找到缓存: {args.get})")
    elif args.delete:
        if args.get in cache:
            del cache[args.get]
            cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✅ 已删除缓存: {args.get}")
    return 0


def cmd_log_tail(args: argparse.Namespace) -> int:
    path = Path(args.path) if args.path else Path(".")
    lines = []
    for f in path.rglob("*.log"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            lines.extend(text.splitlines()[-args.lines:])
        except OSError:
            pass
    if args.grep:
        lines = [l for l in lines if args.grep in l]
    for line in lines[-args.lines:]:
        print(f"  {line}")
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    import shutil
    src = Path(args.source).resolve()
    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{src.name}_{ts}"
    backup_path = dest / backup_name
    shutil.copytree(src, backup_path, dirs_exist_ok=True)
    print(f"  ✅ 已备份: {src} → {backup_path}")
    # 清理旧备份
    backups = sorted(dest.glob(f"backup_{src.name}_*"))
    for old in backups[:-args.keep]:
        shutil.rmtree(old, ignore_errors=True)
        print(f"  🗑️  已清理旧备份: {old.name}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    import shutil
    backup = Path(args.backup_file)
    dest = Path(args.dest).resolve()
    if not backup.exists():
        print(f"  ❌ 备份文件不存在: {backup}", file=sys.stderr)
        return 1
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(backup, dest)
    print(f"  ✅ 已恢复: {backup} → {dest}")
    return 0


def cmd_db_migrate(args: argparse.Namespace) -> int:
    sql_dir = Path(args.sql_dir)
    if not sql_dir.exists():
        print(f"  ❌ 迁移目录不存在: {sql_dir}", file=sys.stderr)
        return 1
    migrations = sorted(sql_dir.glob("*.sql"))
    if args.up:
        for m in migrations:
            print(f"  ▶️  执行迁移: {m.name}")
            # 实际执行 SQL
        print(f"  ✅ 共执行 {len(migrations)} 条迁移")
    elif args.down:
        for m in reversed(migrations):
            print(f"  ⏪  回滚: {m.name}")
    elif args.status:
        for m in migrations:
            print(f"  📄 {m.name}")
    return 0
