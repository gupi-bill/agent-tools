# Contributing to agent-tools

## 开发环境

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## 添加新命令

1. 在 `agent_tools/cmd/<category>.py` 中添加函数 `cmd_<name>(args)`，返回 `int` 退出码
2. 在 `register(parent)` 中注册：`p = sub.add_parser("name", help="...")`
3. 在 `tests/test_all.py` 中添加测试
4. 运行 `pytest` 确认通过

## 代码规范

- 纯标准库优先，可选依赖用 try/except ImportError
- Windows GBK 兼容：不使用 emoji，使用 ASCII 输出
- 所有命令接受 `args` 命名空间，返回 `int` 退出码
- 错误时返回非零退出码，正常返回 0

## 提交

```bash
git add -A
git commit -m "feat: add cmd_xxx"
git push
```