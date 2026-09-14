<div align="center">

# 🧰 agent-tools

**Agent 超级工具集 — 200+ CLI 命令，一个入口 `at`**

文件、文本、数据、Git、安全、开发、AI、基建……
Agent 和开发者日常要用的命令行工具，一次装齐，随取随用。

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Commands](https://img.shields.io/badge/commands-200%2B-orange)](#命令总览)
[![pytest](https://img.shields.io/badge/tests-15%20passed-green)](./tests)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

</div>

---

## 目录

- [🚀 快速开始](#-快速开始)
- [📋 命令总览](#-命令总览)
- [💡 常用示例](#-常用示例)
- [🖥️ 跨平台支持](#️-跨平台支持)
- [🛠️ 开发](#️-开发)
- [📄 License](#-license)

---

## 🚀 快速开始

```bash
# 安装（开发模式）
pip install -e .

# 查看所有分类
at --help

# 查看某分类下的命令
at file --help
at security --help
```

---

## 📋 命令总览

11 大分类，200+ 命令：

| 分类 | 命令数 | 核心功能 |
|------|:------:|---------|
| 📁 `file` | 32 | 搜索 / 统计 / diff / 批量重命名 / 哈希 / 复制 |
| 📝 `text` | 36 | 排序 / 去重 / Base64 / 正则 / 分词 / 转置矩阵 |
| 🔄 `data` | 16 | JSON ↔ CSV / YAML ↔ JSON / XML 转换 / Schema 验证 |
| 🌿 `git` | 15 | log / diff / stats / blame / 分支管理 / 冲突检测 |
| 🛡️ `security` | 12 | 密钥扫描 / AES 加密 / 密码哈希 / 安全审计 |
| 🔧 `dev` | 23 | 依赖分析 / TODO 扫描 / CHANGELOG 生成 / CI 模板 |
| 🤖 `ai` | 12 | Token 估算 / RAG 索引 / 情感分析 / 关键词提取 |
| 🏗️ `infra` | 14 | 健康检查 / 端口查找 / Cron 生成 / 备份恢复 |
| 🏷️ `meta` | 8 | README 生成 / License 选择 / 版本管理 |
| 💻 `system` | 19 | 进程管理 / 磁盘内存 / 哈希 / 终端工具 |
| 🌐 `web` | 13 | HTTP 服务器 / HTML 压缩 / robots.txt / sitemap |

---

## 💡 常用示例

**文件搜索**

```bash
at file grep "TODO" /path/to/code
at file find "*.py" --size +1MB
```

**安全扫描**

```bash
at security scan ./src --severity HIGH
at security hash-password "mypassword"
```

**数据转换**

```bash
at data json-to-csv input.json output.csv
at data yaml-to-json config.yaml
```

**代码分析**

```bash
at dev deps --fix ./requirements.txt
at dev todo ./src
at git stats
```

---

## 🖥️ 跨平台支持

Windows / macOS / Linux 全平台可用，纯标准库实现 + 可选依赖增强。

| 可选依赖 | 解锁能力 |
|---|---|
| `cryptography` | 加解密命令 |
| `PyYAML` | YAML 转换命令 |
| `psutil` | 系统信息命令 |

---

## 🛠️ 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 类型检查
python -m py_compile agent_tools/*.py agent_tools/cmd/*.py
```

---

## 📄 License

[MIT](./LICENSE)
