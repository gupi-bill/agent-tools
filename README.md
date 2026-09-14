# agent-tools

Agent 超级工具集 — **200+ CLI 命令，一个入口** `at`。

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)
[![pytest](https://img.shields.io/badge/tests-15_passed-green)](./tests)

---

## 快速开始

```bash
# 安装（开发模式）
pip install -e .

# 查看所有分类
at --help

# 查看某分类命令
at file --help
at security --help
```

## 命令总览

| 分类 | 命令数 | 核心功能 |
|------|--------|---------|
| `file` | 32 | 搜索 / 统计 / diff / 批量重命名 / 哈希 / 复制 |
| `text` | 36 | 排序 / 去重 / Base64 / 正则 / 分词 / 转置矩阵 |
| `data` | 16 | JSON ↔ CSV / YAML ↔ JSON / XML 转换 / Schema 验证 |
| `git` | 15 | log / diff / stats / blame / 分支管理 / 冲突检测 |
| `security` | 12 | 密钥扫描 / AES 加密 / 密码哈希 / 安全审计 |
| `dev` | 23 | 依赖分析 / TODO 扫描 / CHANGELOG 生成 / CI 模板 |
| `ai` | 12 | Token 估算 / RAG 索引 / 情感分析 / 关键词提取 |
| `infra` | 14 | 健康检查 / 端口查找 / Cron 生成 / 备份恢复 |
| `meta` | 8 | README 生成 / License 选择 / 版本管理 |
| `system` | 19 | 进程管理 / 磁盘内存 / 哈希 / 终端工具 |
| `web` | 13 | HTTP 服务器 / HTML 压缩 / robots.txt / sitemap |

## 常用示例

```bash
# 文件搜索
at file grep "TODO" /path/to/code
at file find "*.py" --size +1MB

# 安全扫描
at security scan ./src --severity HIGH
at security hash-password "mypassword"

# 数据转换
at data json-to-csv input.json output.csv
at data yaml-to-json config.yaml

# 代码分析
at dev deps --fix ./requirements.txt
at dev todo ./src
at git stats
```

## 跨平台支持

Windows / macOS / Linux，纯标准库 + 可选依赖。

**可选依赖：**
- `cryptography` — 加解密命令
- `PyYAML` — YAML 转换命令
- `psutil` — 系统信息命令

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 类型检查
python -m py_compile agent_tools/*.py agent_tools/cmd/*.py
```

## License

MIT
