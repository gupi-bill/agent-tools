"""data: 数据格式转换工具。"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def register(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("json-to-csv", help="JSON 转 CSV")
    p.add_argument("input")
    p.add_argument("--output", "-o")
    p.add_argument("--keys", help="指定字段（逗号分隔）")

    p = sub.add_parser("csv-to-json", help="CSV 转 JSON")
    p.add_argument("input")
    p.add_argument("--output", "-o")
    p.add_argument("--header", action="store_true")

    p = sub.add_parser("json-format", help="格式化 JSON")
    p.add_argument("input")
    p.add_argument("--indent", type=int, default=2)
    p.add_argument("--output", "-o")
    p.add_argument("--minify", action="store_true")

    p = sub.add_parser("json-validate", help="验证 JSON 格式")
    p.add_argument("input")

    p = sub.add_parser("json-schema", help="从示例生成 JSON Schema")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("flatten-json", help="扁平化嵌套 JSON")
    p.add_argument("input")
    p.add_argument("--delimiter", default=".")
    p.add_argument("--output", "-o")

    p = sub.add_parser("unflatten-json", help="恢复嵌套 JSON")
    p.add_argument("input")
    p.add_argument("--delimiter", default=".")
    p.add_argument("--output", "-o")

    p = sub.add_parser("yaml-to-json", help="YAML 转 JSON")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("json-to-yaml", help="JSON 转 YAML")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("csv-summary", help="CSV 统计摘要")
    p.add_argument("input")

    p = sub.add_parser("json-diff", help="JSON diff")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("json-merge", help="合并多个 JSON 文件")
    p.add_argument("inputs", nargs="+")
    p.add_argument("--output", "-o")
    p.add_argument("--strategy", choices=["deep", "shallow", "overwrite"], default="deep")

    p = sub.add_parser("json-select", help="JSONPath 查询")
    p.add_argument("input")
    p.add_argument("--query", required=True, help="路径如 .items[0].name")

    p = sub.add_parser("json-query", help="JSON jq 风格查询")
    p.add_argument("input")
    p.add_argument("--expr", required=True)

    p = sub.add_parser("csv-sort", help="CSV 排序")
    p.add_argument("input")
    p.add_argument("--by", required=True, help="列名")
    p.add_argument("--reverse", action="store_true")
    p.add_argument("--output", "-o")

    p = sub.add_parser("csv-filter", help="CSV 过滤行")
    p.add_argument("input")
    p.add_argument("--where", required=True, help="SQL 风格 WHERE 如 name='foo'")
    p.add_argument("--output", "-o")

    p = sub.add_parser("xlsx-to-csv", help="Excel 转 CSV")
    p.add_argument("input")
    p.add_argument("--sheet", type=int, default=0)
    p.add_argument("--output", "-o")

    p = sub.add_parser("csv-to-xlsx", help="CSV 转 Excel")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("xml-to-json", help="XML 转 JSON")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("json-to-xml", help="JSON 转 XML")
    p.add_argument("input")
    p.add_argument("--root", default="root")
    p.add_argument("--output", "-o")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path | None, data: object) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if path:
        path.write_text(text, encoding="utf-8")
    else:
        print(text)


def cmd_json_to_csv(args: argparse.Namespace) -> int:
    data = _read_json(Path(args.input))
    if isinstance(data, dict):
        data = [data]
    if not data:
        print("空数据")
        return 0
    keys = args.keys.split(",") if args.keys else list(data[0].keys())
    out = args.output and Path(args.output) or Path(args.input).with_suffix(".csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in data:
            writer.writerow({k: row.get(k, "") for k in keys})
    print(f"已导出到 {out}")
    return 0


def cmd_csv_to_json(args: argparse.Namespace) -> int:
    rows = []
    with open(args.input, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    _write_json(args.output and Path(args.output) or None, rows)
    return 0


def cmd_json_format(args: argparse.Namespace) -> int:
    data = _read_json(Path(args.input))
    if args.minify:
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    else:
        text = json.dumps(data, ensure_ascii=False, indent=args.indent)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def cmd_json_validate(args: argparse.Namespace) -> int:
    try:
        _read_json(Path(args.input))
        print("✅ JSON 格式正确")
        return 0
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}")
        return 1


def cmd_json_schema(args: argparse.Namespace) -> int:
    data = _read_json(Path(args.input))
    def _schema(obj: object) -> dict:
        if isinstance(obj, dict):
            return {"type": "object", "properties": {k: _schema(v) for k, v in obj.items()}}
        elif isinstance(obj, list):
            return {"type": "array", "items": _schema(obj[0]) if obj else {}}
        elif isinstance(obj, bool):
            return {"type": "boolean"}
        elif isinstance(obj, int):
            return {"type": "integer"}
        elif isinstance(obj, float):
            return {"type": "number"}
        elif isinstance(obj, str):
            return {"type": "string"}
        elif obj is None:
            return {"type": "null"}
        return {}
    schema = _schema(data)
    out = Path(args.output) if args.output else Path(args.input).with_suffix(".schema.json")
    out.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Schema 已生成: {out}")
    return 0


def cmd_flatten_json(args: argparse.Namespace) -> int:
    data = _read_json(Path(args.input))
    result: dict[str, str] = {}

    def _flatten(obj: object, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{prefix}{args.delimiter}{k}" if prefix else k
                _flatten(v, new_key)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _flatten(v, f"{prefix}{args.delimiter}[{i}]")
        else:
            result[prefix] = str(obj) if obj is not None else ""

    _flatten(data)
    out = Path(args.output) if args.output else Path(args.input).with_suffix(".flat.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已扁平化: {len(result)} 个键")
    return 0


def cmd_unflatten_json(args: argparse.Namespace) -> int:
    data = _read_json(Path(args.input))
    result: dict = {}
    for key, value in data.items():
        parts = key.split(args.delimiter)
        current = result
        for part in parts[:-1]:
            if part.startswith("[") and part.endswith("]"):
                idx = int(part[1:-1])
                current = current[idx] if isinstance(current, list) else current.setdefault(part, [])
            else:
                current = current.setdefault(part, {})
        last = parts[-1]
        if last.startswith("[") and last.endswith("]"):
            idx = int(last[1:-1])
            while len(current) <= idx:
                current.append({})
            current[idx] = value
        else:
            current[last] = value
    out = Path(args.output) if args.output else Path(args.input).with_suffix(".unflat.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已恢复嵌套结构")
    return 0


def cmd_yaml_to_json(args: argparse.Namespace) -> int:
    import yaml
    data = yaml.safe_load(Path(args.input).read_text(encoding="utf-8"))
    _write_json(args.output and Path(args.output) or None, data)
    return 0


def cmd_json_to_yaml(args: argparse.Namespace) -> int:
    import yaml
    data = _read_json(Path(args.input))
    text = yaml.dump(data, allow_unicode=True, sort_keys=False)
    out = Path(args.output) if args.output else Path(args.input).with_suffix(".yaml")
    out.write_text(text, encoding="utf-8")
    print(f"已导出到 {out}")
    return 0


def cmd_csv_summary(args: argparse.Namespace) -> int:
    rows: list[dict] = []
    with open(args.input, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        for row in reader:
            rows.append(row)
    if not rows:
        print("空文件")
        return 0
    print(f"📊 {args.input}")
    print(f"   行数: {len(rows)} | 列数: {len(headers)}")
    print()
    for h in headers:
        values = [r.get(h, "") for r in rows]
        nums = []
        for v in values:
            try:
                nums.append(float(v))
            except (ValueError, TypeError):
                pass
        unique = len(set(values))
        missing = sum(1 for v in values if not v)
        print(f"  📌 {h:<20}  唯一值: {unique:>5}  缺失: {missing:>4}")
        if nums:
            print(f"       数值范围: {min(nums):.2f} ~ {max(nums):.2f}  均值: {sum(nums)/len(nums):.2f}")
    return 0


def cmd_json_diff(args: argparse.Namespace) -> int:
    a = _read_json(Path(args.a))
    b = _read_json(Path(args.b))
    import difflib
    ja = json.dumps(a, sort_keys=True, ensure_ascii=False)
    jb = json.dumps(b, sort_keys=True, ensure_ascii=False)
    diffs = list(difflib.unified_diff(ja.splitlines(), jb.splitlines(), fromfile=args.a, tofile=args.b))
    if args.json:
        print(json.dumps(diffs, indent=2))
    else:
        for line in diffs:
            color = ""
            if line.startswith("+"):
                color = "\033[32m"
            elif line.startswith("-"):
                color = "\033[31m"
            print(f"{color}{line}\033[0m", end="")
    return 0


def cmd_json_merge(args: argparse.Namespace) -> int:
    parts = [_read_json(Path(p)) for p in args.inputs]
    if args.strategy == "deep":
        def deep_merge(base: dict, overlay: dict) -> dict:
            result = base.copy()
            for k, v in overlay.items():
                if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                    result[k] = deep_merge(result[k], v)
                else:
                    result[k] = v
            return result
        result = parts[0]
        for p in parts[1:]:
            result = deep_merge(result, p)
    else:
        result = {}
        for p in parts:
            if isinstance(p, dict):
                result.update(p)
    _write_json(args.output and Path(args.output) or None, result)
    return 0


def cmd_json_select(args: argparse.Namespace) -> int:
    data = _read_json(Path(args.input))
    parts = args.query.strip(".").split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError):
                current = None
        else:
            current = None
        if current is None:
            break
    if isinstance(current, (dict, list)):
        print(json.dumps(current, ensure_ascii=False, indent=2))
    else:
        print(current)
    return 0


def cmd_json_query(args: argparse.Namespace) -> int:
    data = _read_json(Path(args.input))
    expr = args.expr
    try:
        result = eval(expr, {"__builtins__": {}}, {"data": data})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"❌ 查询错误: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_csv_sort(args: argparse.Namespace) -> int:
    rows: list[dict] = []
    with open(args.input, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            rows.append(row)
    def sort_key(row: dict):
        try:
            return float(row.get(args.by, 0))
        except (ValueError, TypeError):
            return row.get(args.by, "")
    rows.sort(key=sort_key, reverse=args.reverse)
    out = Path(args.output) if args.output else Path(args.input)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"已排序并保存到 {out}")
    return 0


def cmd_csv_filter(args: argparse.Namespace) -> int:
    rows: list[dict] = []
    with open(args.input, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            try:
                if eval(args.where, {"__builtins__": {}}, dict(row)):
                    rows.append(row)
            except Exception:
                pass
    out = Path(args.output) if args.output else Path(args.input)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"过滤后: {len(rows)} 行")
    return 0