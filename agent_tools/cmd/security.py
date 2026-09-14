"""security: 安全扫描工具。"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# 安全模式匹配: (名称, 正则, 严重级别)
RULES: list[tuple[str, str, str]] = [
    ("硬编码密码", r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]{4,}", "HIGH"),
    ("硬编码密钥", r"(?i)(api[_-]?key|secret|token|credential)\s*=\s*['\"][^'\"]{8,}", "HIGH"),
    ("AWS 密钥", r"AKIA[0-9A-Z]{16}", "CRITICAL"),
    ("私钥", r"-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----", "CRITICAL"),
    ("GitHub Token", r"gh[pousr]_[A-Za-z0-9_]{20,}", "CRITICAL"),
    ("Slack Token", r"xox[baprs]-[0-9]{10,}", "HIGH"),
    ("JWT Secret", r"(?i)(jwt[_-]?secret|jwt[_-]?key)\s*=\s*['\"][^'\"]{4,}", "HIGH"),
    ("数据库连接串含密码", r"(?i)(mysql|postgres|mongodb|redis)://[^:]+:[^@]+@", "CRITICAL"),
    ("eval/exec", r"\b(eval|exec)\s*\(", "MEDIUM"),
    ("SQL 拼接", r'(?:execute|query)\s*\(.*%"?\s*%', "HIGH"),
    ("子进程 shell=True", r"subprocess\.\w+\(.*shell\s*=\s*True", "HIGH"),
    ("硬编码 IP", r"(?:private_ip|internal_host)\s*=\s*[\"'][0-9]+\.[0-9]+\.[0-9]+\.[0-9]+[\"']", "LOW"),
    ("硬编码端口", r"(?:port|PORT)\s*=\s*[0-9]{4,5}(?![0-9])", "LOW"),
    ("Base64 编码密钥", r"(?i)(key|secret|password)\s*=\s*[A-Za-z0-9+/]{20,}={0,2}", "MEDIUM"),
    ("SSH 私钥文件引用", r"(?i)(id_rsa|id_ed25519|private_key)\s*[:=]", "CRITICAL"),
    ("Hardcoded URL 含 auth", r"https?://[^:]+:[^@]+@[a-zA-Z0-9.-]+", "HIGH"),
    ("临时文件泄露", r"/tmp/[a-zA-Z0-9_]+\.key|\.pem|\.crt", "MEDIUM"),
    ("敏感文件路径", r"(?i)(passwords?|secrets?|credentials?|keys?)\.(txt|env|json|yaml|yml|csv)", "HIGH"),
    ("JWT 解码", r"\.jwt\b", "LOW"),
]

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", ".tox", ".mypy_cache"}
SKIP_EXTENSIONS = {".pyc", ".pyo", ".o", ".so", ".dll", ".exe", ".bin", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".map"}


def register(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scan", help="安全扫描目录")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", help="后缀过滤（逗号分隔）")
    p.add_argument("--severity", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"], default="LOW")
    p.add_argument("--json", action="store_true")
    p.add_argument("--exclude", nargs="*", default=list(EXCLUDE_DIRS))

    p = sub.add_parser("check-token", help="检查 token 泄露")
    p.add_argument("text")

    p = sub.add_parser("mask", help="脱敏文本")
    p.add_argument("text")
    p.add_argument("--type", choices=["password", "key", "email", "phone"], default="password")

    p = sub.add_parser("hash-password", help="生成密码哈希")
    p.add_argument("--password", help="密码（或从 stdin）")
    p.add_argument("--algo", choices=["bcrypt", "pbkdf2", "argon2"], default="pbkdf2")

    p = sub.add_parser("gen-secret", help="生成随机密钥")
    p.add_argument("--length", type=int, default=32)
    p.add_argument("--type", choices=["hex", "base64", "alphanumeric"], default="hex")
    p.add_argument("--count", type=int, default=1)

    p = sub.add_parser("verify-password", help="验证密码哈希")
    p.add_argument("--password", required=True)
    p.add_argument("--hash", required=True)

    p = sub.add_parser("encrypt", help="AES 加密")
    p.add_argument("input")
    p.add_argument("--key", required=True)
    p.add_argument("--output", "-o")

    p = sub.add_parser("decrypt", help="AES 解密")
    p.add_argument("input")
    p.add_argument("--key", required=True)
    p.add_argument("--output", "-o")

    p = sub.add_parser("audit-env", help="审计 .env 文件")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("check-crlf", help="检查 CRLF 注入风险")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py,.js,.ts,.json,.yaml,.yml,.md,.txt,.html,.css,.sh,.bat")

    p = sub.add_parser("check-backticks", help="检查反引号注入")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".py,.js,.ts,.sh,.yaml,.yml,.json,.html,.md,.txt")

    p = sub.add_parser("report", help="生成安全报告")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--output", "-o")
    p.add_argument("--json", action="store_true")


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    min_severity = ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(args.severity)
    ext_filter = tuple(args.ext.split(",")) if args.ext else None
    findings: list[dict] = []

    for f in root.rglob("*"):
        if f.is_file():
            rel = f.relative_to(root)
            rel_str = str(rel)
            skip = False
            for exc in EXCLUDE_DIRS | set(args.exclude or []):
                if exc in rel_str.split("/"):
                    skip = True
                    break
            if skip:
                continue
            if ext_filter and f.suffix.lower() not in ext_filter:
                continue
            if f.suffix.lower() in SKIP_EXTENSIONS:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for name, pattern, severity in RULES:
                if ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(severity) < min_severity:
                    continue
                matches = list(re.finditer(pattern, text))
                for m in matches:
                    line_no = text[:m.start()].count("\n") + 1
                    context = text[m.start():m.end()][:80]
                    findings.append({
                        "file": rel_str,
                        "line": line_no,
                        "rule": name,
                        "severity": severity,
                        "match": context,
                    })

    # 去重
    seen = set()
    unique = []
    for f in findings:
        key = (f["file"], f["line"], f["rule"])
        if key not in seen:
            seen.add(key)
            unique.append(f)

    # 排序: CRITICAL > HIGH > MEDIUM > LOW
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    unique.sort(key=lambda x: (sev_order.get(x["severity"], 9), x["file"], x["line"]))

    if args.json:
        print(json.dumps(unique, ensure_ascii=False, indent=2))
        return 0

    if not unique:
        print("✅ 未发现安全问题")
        return 0

    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in unique:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    print(f"🔒 安全扫描报告")
    print(f"   根目录: {root}")
    print(f"   发现: 🔴 {counts['CRITICAL']}  🟠 {counts['HIGH']}  🟡 {counts['MEDIUM']}  🟢 {counts['LOW']}")
    print()
    for f in unique[:50]:
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(f["severity"], "⚪")
        print(f"  {icon} [{f['severity']}] {f['file']}:{f['line']}  {f['rule']}")
        print(f"     {f['match']}")
    if len(unique) > 50:
        print(f"  ... 还有 {len(unique) - 50} 处")
    return 1 if counts["CRITICAL"] > 0 or counts["HIGH"] > 0 else 0


def cmd_check_token(args: argparse.Namespace) -> int:
    text = args.text
    for name, pattern, severity in RULES:
        if re.search(pattern, text):
            print(f"  {severity}  {name}: {text[:80]}")
            return 1
    print("✅ 未检测到敏感 token")
    return 0


def cmd_mask(args: argparse.Namespace) -> int:
    from ..utils import mask_secret
    text = args.text
    if args.type == "email":
        parts = text.split("@")
        if len(parts) == 2:
            print(f"{mask_secret(parts[0])}@{parts[1]}")
        else:
            print(mask_secret(text))
    elif args.type == "phone":
        print(mask_secret(text) + "***")
    else:
        print(mask_secret(text))
    return 0


def cmd_hash_password(args: argparse.Namespace) -> int:
    import getpass
    password = args.password or getpass.getpass("密码: ")
    import hashlib
    salt = hashlib.sha256(str(hash(password)).encode()).digest()[:16]
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    result = salt.hex() + h.hex()
    print(f"$pbkdf2-sha256${result}")
    return 0


def cmd_gen_secret(args: argparse.Namespace) -> int:
    import secrets
    for _ in range(args.count):
        if args.type == "hex":
            print(secrets.token_hex(args.length))
        elif args.type == "base64":
            print(secrets.token_b64(args.length))
        else:
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            print("".join(secrets.choice(chars) for _ in range(args.length)))
    return 0


def cmd_verify_password(args: argparse.Namespace) -> int:
    import hashlib
    stored = args.hash
    if stored.startswith("$pbkdf2-sha256$"):
        stored = stored[len("$pbkdf2-sha256$"):]
        salt = bytes.fromhex(stored[:32])
        expected = stored[32:]
        h = hashlib.pbkdf2_hmac("sha256", args.password.encode(), salt, 100000)
        if h.hex() == expected:
            print("✅ 密码匹配")
            return 0
    print("❌ 密码不匹配")
    return 1


def cmd_encrypt(args: argparse.Namespace) -> int:
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        print("❌ 需要安装 cryptography: pip install cryptography", file=sys.stderr)
        return 1
    key = args.key.encode()
    if len(key) < 32:
        import hashlib
        key = hashlib.sha256(key).digest()
    f = Fernet(key)
    data = Path(args.input).read_bytes()
    encrypted = f.encrypt(data)
    out = Path(args.output) if args.output else Path(args.input).with_suffix(".enc")
    out.write_bytes(encrypted)
    print(f"已加密到 {out}")
    return 0


def cmd_decrypt(args: argparse.Namespace) -> int:
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        print("❌ 需要安装 cryptography: pip install cryptography", file=sys.stderr)
        return 1
    key = args.key.encode()
    if len(key) < 32:
        import hashlib
        key = hashlib.sha256(key).digest()
    f = Fernet(key)
    data = Path(args.input).read_bytes()
    decrypted = f.decrypt(data)
    out = Path(args.output) if args.output else Path(args.input).with_suffix("")
    out.write_bytes(decrypted)
    print(f"已解密到 {out}")
    return 0


def cmd_audit_env(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    env_files = list(root.rglob(".env*")) + list(root.rglob("*.env"))
    env_files = [f for f in env_files if f.is_file()]
    findings: list[dict] = []
    for f in env_files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                for pattern_name, pattern, severity in RULES:
                    if re.search(pattern, f"{key}={value}"):
                        findings.append({
                            "file": str(f.relative_to(root)),
                            "line": i,
                            "key": key,
                            "rule": pattern_name,
                            "severity": severity,
                        })
    if args.json:
        print(json.dumps(findings, indent=2))
        return 0
    if not findings:
        print("✅ .env 文件安全")
        return 0
    print(f"🔒 发现 {len(findings)} 个安全问题")
    for f in findings:
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(f["severity"], "⚪")
        print(f"  {icon} {f['file']}:{f['line']}  {f['key']} — {f['rule']}")
    return 1


def cmd_check_crlf(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(","))
    count = 0
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                text = f.read_text(encoding="utf-8")
                if "\r\n" in text:
                    count += 1
                    print(f"  ⚠️  {f.relative_to(root)}  (含 CRLF)")
            except OSError:
                pass
    print(f"\n发现 {count} 个含 CRLF 的文件")
    return 0


def cmd_check_backticks(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(","))
    count = 0
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            # 检查 shell 命令中的反引号
            for i, line in enumerate(text.splitlines(), 1):
                if "`" in line and "$(" not in line and "import" not in line and "string" not in line:
                    if re.search(r"`[^`]*\$[^`]*`", line):
                        count += 1
                        print(f"  ⚠️  {f.relative_to(root)}:{i}  {line.strip()[:80]}")
    print(f"\n发现 {count} 处潜在反引号注入风险")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    findings: list[dict] = []
    for f in root.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(root))
            skip = any(exc in rel for exc in EXCLUDE_DIRS)
            if skip:
                continue
            if f.suffix.lower() in SKIP_EXTENSIONS:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for name, pattern, severity in RULES:
                for m in re.finditer(pattern, text):
                    line_no = text[:m.start()].count("\n") + 1
                    findings.append({
                        "file": rel,
                        "line": line_no,
                        "rule": name,
                        "severity": severity,
                        "match": text[m.start():m.end()][:80],
                    })
    # 去重
    seen = set()
    unique = []
    for f in findings:
        key = (f["file"], f["line"], f["rule"])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    unique.sort(key=lambda x: (sev_order.get(x["severity"], 9), x["file"], x["line"]))

    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in unique:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    report = {
        "root": str(root),
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "summary": counts,
        "total_findings": len(unique),
        "findings": unique,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"🔒 安全审计报告")
        print(f"   扫描目录: {root}")
        print(f"   生成时间: {report['generated_at']}")
        print(f"   总计: {len(unique)} 处发现")
        print(f"   🔴 严重: {counts['CRITICAL']}  🟠 高危: {counts['HIGH']}  🟡 中危: {counts['MEDIUM']}  🟢 低危: {counts['LOW']}")
        print()
        for f in unique[:30]:
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(f["severity"], "⚪")
            print(f"  {icon} [{f['severity']}] {f['file']}:{f['line']}  {f['rule']}")
            print(f"     {f['match']}")
        if len(unique) > 30:
            print(f"  ... 还有 {len(unique) - 30} 处")

    if args.output:
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n📄 报告已保存到 {args.output}")

    return 1 if counts["CRITICAL"] > 0 or counts["HIGH"] > 0 else 0