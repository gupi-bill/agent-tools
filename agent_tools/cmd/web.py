"""web: Web 工具。"""
from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path

def register(parent):
    sub = parent.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("serve", help="简易 HTTP 服务器")
    p.add_argument("--dir", default=".")
    p.add_argument("--port", type=int, default=8080)
    p = sub.add_parser("headers", help="HTTP Header 解析")
    p.add_argument("header_string")
    p = sub.add_parser("url-parse", help="URL 解析")
    p.add_argument("url")
    p = sub.add_parser("html-minify", help="HTML 压缩")
    p.add_argument("input")
    p.add_argument("--output", "-o")
    p = sub.add_parser("css-minify", help="CSS 压缩")
    p.add_argument("input")
    p.add_argument("--output", "-o")
    p = sub.add_parser("js-minify", help="JS 压缩")
    p.add_argument("input")
    p.add_argument("--output", "-o")
    p = sub.add_parser("cors-check", help="CORS 头检查")
    p.add_argument("url")
    p.add_argument("--method", default="GET")
    p = sub.add_parser("http-status", help="HTTP 状态码说明")
    p.add_argument("--code", type=int, required=True)
    p = sub.add_parser("mime-type", help="MIME 类型查询")
    p.add_argument("extension")
    p = sub.add_parser("screenshot-url", help="生成截图 URL")
    p.add_argument("url")
    p = sub.add_parser("robots-txt", help="生成 robots.txt")
    p.add_argument("--disallow", nargs="*", default=["/admin", "/private"])
    p.add_argument("--output", "-o", default="robots.txt")
    p = sub.add_parser("sitemap-gen", help="生成 sitemap.xml")
    p.add_argument("--base-url", required=True)
    p.add_argument("--paths", nargs="*", default=["/"])
    p.add_argument("--output", "-o", default="sitemap.xml")
    p = sub.add_parser("htaccess-gen", help="生成 .htaccess")
    p.add_argument("--rewrite", action="store_true")
    p.add_argument("--cache", action="store_true")
    p.add_argument("--output", "-o", default=".htaccess")
    p = sub.add_parser("gzip-test", help="Gzip 压缩测试")
    p.add_argument("input")
    p.add_argument("--threshold", type=int, default=1024)


def cmd_serve(args):
    import http.server, socketserver
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", args.port), handler) as httpd:
        print(f"Serving at http://localhost:{args.port}")
        httpd.serve_forever()
    return 0

def cmd_headers(args):
    parsed = {}
    for line in args.header_string.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            parsed[k.strip()] = v.strip()
    print(json.dumps(parsed, indent=2))
    return 0

def cmd_url_parse(args):
    from urllib.parse import urlparse
    u = urlparse(args.url)
    result = {"scheme": u.scheme, "netloc": u.netloc, "path": u.path,
              "query": u.query, "fragment": u.fragment}
    print(json.dumps(result, indent=2))
    return 0

def cmd_html_minify(args):
    text = Path(args.input).read_text(encoding="utf-8")
    text = re.sub(r">\s+<", "><", text)
    text = re.sub(r"\s{2,}", " ", text)
    out = Path(args.output) if args.output else Path(args.input)
    out.write_text(text, encoding="utf-8")
    print(f"已压缩: {len(text)} bytes")
    return 0

def cmd_css_minify(args):
    text = Path(args.input).read_text(encoding="utf-8")
    text = re.sub(r"\s*{\s*", "{", text)
    text = re.sub(r"\s*}\s*", "}", text)
    text = re.sub(r"\s*;\s*", ";", text)
    text = re.sub(r"\s{2,}", " ", text)
    out = Path(args.output) if args.output else Path(args.input)
    out.write_text(text, encoding="utf-8")
    print(f"已压缩: {len(text)} bytes")
    return 0

def cmd_js_minify(args):
    text = Path(args.input).read_text(encoding="utf-8")
    # 简单压缩（不安全，生产环境请用 terser）
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{}();,=<>+\-*/])\s*", r"\1", text)
    out = Path(args.output) if args.output else Path(args.input)
    out.write_text(text, encoding="utf-8")
    print(f"已压缩: {len(text)} bytes")
    return 0

def cmd_http_status(args):
    statuses = {
        200: "OK", 201: "Created", 204: "No Content",
        301: "Moved Permanently", 302: "Found", 304: "Not Modified",
        400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
        404: "Not Found", 405: "Method Not Allowed",
        500: "Internal Server Error", 502: "Bad Gateway", 503: "Service Unavailable",
    }
    desc = statuses.get(args.code, "Unknown")
    print(f"  {args.code}  {desc}")
    return 0

def cmd_mime_type(args):
    from mimetypes import guess_type
    mt = guess_type("file" + args.extension)[0] or "application/octet-stream"
    print(f"  {args.extension}  {mt}")
    return 0

def cmd_screenshot_url(args):
    print(f"https://api.screenshotone.com/take?url={args.url}")
    return 0

def cmd_robots_txt(args):
    lines = ["User-agent: *", ""]
    for path in args.disallow:
        lines.append(f"Disallow: {path}")
    lines.append("")
    lines.append("Sitemap: {base}/sitemap.xml".format(base=args.base_url))
    out = Path(args.output) if hasattr(args, 'output') and args.output else Path("robots.txt")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已生成 → {out}")
    return 0

def cmd_sitemap_gen(args):
    from datetime import datetime
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in args.paths:
        lines.append(f'  <url><loc>{args.base_url}{p}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>')
    lines.append("</urlset>")
    out = Path(args.output) if hasattr(args, 'output') and args.output else Path("sitemap.xml")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已生成 → {out}")
    return 0

def cmd_htaccess_gen(args):
    lines = ["# Auto-generated .htaccess", ""]
    if args.rewrite:
        lines += ["RewriteEngine On", "RewriteBase /", ""]
    if args.cache:
        lines += ["# Cache static assets for 1 year",
                  "<IfModule mod_expires.c>",
                  "  ExpiresActive On",
                  '  ExpiresByType image/jpeg "access plus 1 year"',
                  '  ExpiresByType image/png "access plus 1 year"',
                  '  ExpiresByType text/css "access plus 1 month"',
                  "</IfModule>"]
    out = Path(args.output) if hasattr(args, 'output') and args.output else Path(".htaccess")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已生成 → {out}")
    return 0

def cmd_gzip_test(args):
    import gzip
    data = Path(args.input).read_bytes()
    compressed = gzip.compress(data)
    ratio = len(compressed) / len(data) * 100 if data else 0
    print(f"  原始: {len(data):,} bytes")
    print(f"  压缩: {len(compressed):,} bytes ({ratio:.1f}%)")
    if ratio < float(getattr(args, 'threshold', 1024)):
        print(f"  ✅ 压缩率高，建议启用 gzip")
    return 0