"""tests for agent-tools unified CLI."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


def test_cli_help(capsys):
    """CLI 帮助正常显示。"""
    from agent_tools.cli import main
    import sys
    old_argv = sys.argv
    try:
        sys.argv = ["at", "--help"]
        main()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
    captured = capsys.readouterr()
    assert "file" in captured.out
    assert "security" in captured.out
    assert "dev" in captured.out


def test_file_count(tmp_path):
    """文件统计。"""
    (tmp_path / "test.py").write_text("import os\nprint('hi')\n", encoding="utf-8")
    from agent_tools.cmd.file import cmd_count
    import argparse
    args = argparse.Namespace(path=str(tmp_path), json=False)
    rc = cmd_count(args)
    assert rc == 0


def test_file_grep(tmp_path):
    """grep 搜索。"""
    (tmp_path / "a.py").write_text("hello world\nfoo bar\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("hello there\n", encoding="utf-8")
    from agent_tools.cmd.file import cmd_grep
    import argparse
    args = argparse.Namespace(pattern="hello", path=str(tmp_path), ext=None, count=False, json=False)
    rc = cmd_grep(args)
    assert rc == 0


def test_text_sort():
    """文本排序。"""
    from agent_tools.cmd.text import cmd_sort
    import argparse
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("banana\napple\ncherry\n")
        f.flush()
        args = argparse.Namespace(input=f.name, output=None, reverse=False, unique=False)
        cmd_sort(args)
        result = Path(f.name).read_text(encoding="utf-8")
        assert "apple" in result
        assert "banana" in result


def test_text_dedup():
    """去重。"""
    from agent_tools.cmd.text import cmd_dedup
    import argparse
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("a\na\nb\na\nc\n")
        f.flush()
        args = argparse.Namespace(input=f.name, output=None, keep="first")
        cmd_dedup(args)
        result = Path(f.name).read_text(encoding="utf-8")
        lines = [l for l in result.strip().split("\n") if l]
        assert len(lines) == 3


def test_security_scan(tmp_path):
    """安全扫描。"""
    (tmp_path / "secret.py").write_text('password = "supersecret123"\napi_key = "sk-abc123"\n', encoding="utf-8")
    from agent_tools.cmd.security import cmd_scan
    import argparse
    args = argparse.Namespace(
        path=str(tmp_path), ext=None, severity="LOW", json=False, exclude=None
    )
    rc = cmd_scan(args)
    assert rc == 1  # 发现安全问题


def test_security_clean(tmp_path):
    """干净代码无发现。"""
    (tmp_path / "safe.py").write_text('def hello():\n    return "world"\n', encoding="utf-8")
    from agent_tools.cmd.security import cmd_scan
    import argparse
    args = argparse.Namespace(
        path=str(tmp_path), ext=None, severity="LOW", json=False, exclude=None
    )
    rc = cmd_scan(args)
    assert rc == 0


def test_dev_deps(tmp_path):
    """依赖分析。"""
    (tmp_path / "requirements.txt").write_text("fastapi>=0.133\nrequests\nnonexistent-pkg-xyz\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("import fastapi\nfrom pydantic import BaseModel\n", encoding="utf-8")
    from agent_tools.cmd.dev import cmd_deps
    import argparse
    args = argparse.Namespace(path=str(tmp_path), fix=False, json=False)
    rc = cmd_deps(args)
    assert rc == 1  # 有缺失依赖


def test_data_json_format():
    """JSON 格式化。"""
    import json as _json
    from agent_tools.cmd.data import cmd_json_format
    import argparse
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write('{"b":2,"a":1}')
        f.flush()
        args = argparse.Namespace(input=f.name, indent=2, output=None, minify=False)
        cmd_json_format(args)


def test_data_json_validate():
    """JSON 验证。"""
    from agent_tools.cmd.data import cmd_json_validate
    import argparse
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write('{"a":1,"b":[1,2,3]}')
        f.flush()
        args = argparse.Namespace(input=f.name)
        rc = cmd_json_validate(args)
        assert rc == 0


def test_dev_todo(tmp_path):
    """TODO 扫描。"""
    (tmp_path / "code.py").write_text('# TODO: fix this\n# FIXME: bug here\nprint("hello")\n', encoding="utf-8")
    from agent_tools.cmd.dev import cmd_todo
    import argparse
    args = argparse.Namespace(path=str(tmp_path), ext=None, json=False)
    rc = cmd_todo(args)
    assert rc == 0


def test_system_hash():
    """哈希计算。"""
    from agent_tools.cmd.system import cmd_hash
    import argparse
    args = argparse.Namespace(input="hello world", algo="sha256", text=True)
    rc = cmd_hash(args)
    assert rc == 0


def test_ai_token_count():
    """Token 估算。"""
    from agent_tools.cmd.ai import cmd_token_count
    import argparse
    args = argparse.Namespace(text="Hello world this is a test", file=None, model="gpt-4", json=False)
    rc = cmd_token_count(args)
    assert rc == 0



def test_infra_port_finder():
    """端口查找。"""
    from agent_tools.cmd.infra import cmd_port_finder
    import argparse
    args = argparse.Namespace(range="30000-30010", count=1, json=False)
    rc = cmd_port_finder(args)
    assert rc == 0


def test_data_yaml_to_json(tmp_path):
    """YAML 转 JSON。"""
    (tmp_path / "test.yaml").write_text("name: test\nvalue: 42\n", encoding="utf-8")
    from agent_tools.cmd.data import cmd_yaml_to_json
    import argparse
    out = tmp_path / "out.json"
    args = argparse.Namespace(input=str(tmp_path / "test.yaml"), output=str(out))
    rc = cmd_yaml_to_json(args)
    assert out.exists()


def test_main_module():
    """python -m agent_tools 入口正常工作。"""
    import subprocess, sys
    r = subprocess.run([sys.executable, '-m', 'agent_tools', '--version'],
                       capture_output=True, text=True, timeout=5)
    assert r.returncode == 0
    assert 'agent-tools' in r.stdout


def test_at_file_count(tmp_path, capsys):
    """file count 命令。"""
    (tmp_path / 'a.txt').write_text('hello\n', encoding='utf-8')
    (tmp_path / 'b.txt').write_text('world\n', encoding='utf-8')
    from agent_tools.cmd.file import cmd_count
    import argparse
    args = argparse.Namespace(path=str(tmp_path), json=False)
    rc = cmd_count(args)
    assert rc == 0


def test_text_sort_lines(tmp_path):
    """text sort 命令。"""
    (tmp_path / 'input.txt').write_text('banana\napple\ncherry\n', encoding='utf-8')
    from agent_tools.cmd.text import cmd_sort
    import argparse
    out = tmp_path / 'out.txt'
    args = argparse.Namespace(input=str(tmp_path / 'input.txt'), output=str(out), reverse=False, unique=False)
    cmd_sort(args)
    result = out.read_text(encoding='utf-8')
    lines = [l for l in result.strip().split('\n') if l]
    assert lines == sorted(lines)


def test_security_mask(capsys):
    """security mask 命令。"""
    from agent_tools.cmd.security import cmd_mask
    import argparse
    args = argparse.Namespace(text='password: abc123, key: sk-xyz', type='mask-all')
    rc = cmd_mask(args)
    assert rc == 0

def test_file_grep_pattern(tmp_path):
    """grep search."""
    (tmp_path / "a.py").write_text("hello world\nfoo bar\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("hello there\n", encoding="utf-8")
    from agent_tools.cmd.file import cmd_grep
    import argparse
    args = argparse.Namespace(pattern="hello", path=str(tmp_path), ext=None, count=False, json=False)
    rc = cmd_grep(args)
    assert rc == 0


def test_data_json_to_csv(tmp_path):
    """JSON to CSV."""
    import json
    data = [{"name": "Alice", "age": "30"}]
    (tmp_path / "data.json").write_text(json.dumps(data), encoding="utf-8")
    out = tmp_path / "out.csv"
    from agent_tools.cmd.data import cmd_json_to_csv
    import argparse
    args = argparse.Namespace(input=str(tmp_path / "data.json"), output=str(out), keys=None, sep=",")
    rc = cmd_json_to_csv(args)
    assert out.exists()


def test_system_disk():
    """Disk info."""
    from agent_tools.cmd.system import cmd_disk
    import argparse
    args = argparse.Namespace(path="/", json=False)
    rc = cmd_disk(args)
    assert rc == 0


def test_system_env_show():
    """Env show."""
    from agent_tools.cmd.system import cmd_env_show
    import argparse
    args = argparse.Namespace(key=None, json=False)
    rc = cmd_env_show(args)
    assert rc == 0


def test_meta_project_info(tmp_path):
    import pytest
    pytest.skip("requires tomli")

def test_web_headers():
    """HTTP headers."""
    from agent_tools.cmd.web import cmd_headers
    import argparse
    args = argparse.Namespace(header_string="Content-Type: text/html\nAuthorization: Bearer tok")
    rc = cmd_headers(args)
    assert rc == 0


def test_web_url_parse():
    """URL parse."""
    from agent_tools.cmd.web import cmd_url_parse
    import argparse
    args = argparse.Namespace(url="https://example.com/path?q=1")
    rc = cmd_url_parse(args)
    assert rc == 0


def test_git_branches():
    """Git branches listing."""
    import pytest
    pytest.skip("requires git repo")

def test_security_gen_secret():
    """Generate random secret."""
    import pytest
    pytest.skip("complex setup")

def test_ai_similarity():
    """Text similarity."""
    from agent_tools.cmd.ai import cmd_similarity
    import argparse
    args = argparse.Namespace(a="hello world", b="hi there", method="jaccard")
    rc = cmd_similarity(args)
    assert rc == 0


def test_text_reverse(tmp_path):
    """Text reverse."""
    (tmp_path / "in.txt").write_text("hello\nworld\n", encoding="utf-8")
    from agent_tools.cmd.text import cmd_reverse
    import argparse
    args = argparse.Namespace(input=str(tmp_path / "in.txt"), output=None)
    rc = cmd_reverse(args)
    assert rc == 0


def test_file_find_empty(tmp_path):
    """Find empty files."""
    import os
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")
    (tmp_path / "notempty.txt").write_text("x", encoding="utf-8")
    from agent_tools.cmd.file import cmd_find
    import argparse
    args = argparse.Namespace(
        path=str(tmp_path), name=None, ext=None, empty=True,
        size_min=None, size_max=None, json=False
    )
    rc = cmd_find(args)
    assert rc == 0


def test_dev_changelog():
    """Changelog generation."""
    import pytest
    pytest.skip("requires git repo with history")
