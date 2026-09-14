# Changelog

## [1.0.1] - 2024-01-15

### Fixed
- CLI 命令分发：改为动态 import 模式，支持所有 200 个命令正常运行
- Windows GBK 编码：移除所有 emoji，确保跨平台兼容
- 连字符命令名：`url-parse` 等自动映射为 `cmd_url_parse`

### Added
- 新增 5 个文本命令：repeat / transpose / word_wrap / line_numbers / excerpt
- 新增 2 个安全命令：path_traversal / check_open
- 新增 2 个文件命令：glob_search / file_info
- 新增 13 个测试用例（共 32 个）

### Changed
- README 大幅美化，含安装/用法/命令总览表/示例
- 添加 LICENSE (MIT)
- 添加 CONTRIBUTING.md

## [1.0.0] - 2024-01-14

### Added
- 200+ CLI 命令，11 大分类
- argparse 子命令架构
- pytest 测试框架