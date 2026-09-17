# Scalendar V1

Scalendar V1 是一款面向 Windows 桌面端的新一代课表图片转日历工具。它在旧测试版基础上进行了全新重写，并与历史版本保持 Git 隔离：旧版基线保留在 `main` 与 `v0.0.0-test`，而新版本仅在 `rewrite/v1` 分支继续开发。

当前 V1.0.0 的交付范围涵盖 Milestone 0–9，包含 Python / PySide6 / QML 工程骨架、真实 `.scalendar` 项目生命周期、可编辑课程模型、课程列表多选批量操作、学期与节次管理、图片识别、Excel 导入导出、ICS 导出、Windows 打包与 GitHub Actions CI 自动化等能力。

## 功能概览

- 课表图片识别与结构化提取
- 可编辑课程模型与课表数据管理
- 课程列表多选批量编辑、删除与调整
- 支持按星期、节次、课程名称进行排序与筛选
- 以 `.scalendar` 项目文件作为唯一数据源
- 支持 Excel 导入/导出与 ICS 日历导出
- 提供 Windows 桌面应用与便携版发布流程
- 集成自动化测试与 CI 构建检查

## 开发环境

- Python 3.11+
- PySide6 6.8+
- Windows 10 / 11（目标平台）

建议使用项目自带虚拟环境进行开发。程序与测试均不要求最终用户以 PowerShell 作为唯一入口；PowerShell 主要用于开发和构建流程。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
```

## 运行与测试

```powershell
python -m scalendar.main
pytest
```

安装项目后，也可以直接运行：

```powershell
scalendar
```

Windows 便携版构建：

```powershell
.\tools\build_windows.ps1
```

构建产物位于 `build\release\Scalendar\Scalendar.exe`。构建目录不会提交到 Git。Windows 发布流程使用 Qt for Python 官方的 `pyside6-deploy`，配置位于 `pysidedeploy.spec`；构建脚本会校验所需依赖并生成可分发包。

GitHub Actions 会在 Windows runner 上自动执行常规 push / pull request 测试；手动触发 `Windows package` 工作流，或推送版本 Tag 时，会生成短期保留的便携版构建产物。

启动 GUI 后，会打开 Home 页面。用户可创建空白课表、添加/编辑/删除课程、在课表与课程列表之间同步编辑、按星期/节次/名称排序、多选批量修改周次、节次和课程属性，并管理学期设置与课表配置。

## 架构

```text
src/scalendar/
├── main.py                 # Qt 应用入口
├── core/                   # 纯数据模型、校验与课表日期计算
├── storage/                # .scalendar JSON 项目读写
├── recognition/            # 图片识别 provider 与候选结果规范化
├── importers/              # Excel 输入适配器与外部表格兼容层
├── exporters/              # XLSX / ICS 输出适配器
├── bridge/                 # Python 与 QML 的控制器边界
├── ui/                     # Qt Quick / QML 页面、组件与主题
└── tests/                  # 自动化测试
```

项目文件使用 UTF-8 编码的 JSON，并以 `.scalendar` 作为扩展名。它是唯一的数据源；Excel 则是可审阅、可交换的导入/导出格式，而不是内部事实源。更多设计说明请参考 [docs/architecture.md](docs/architecture.md)。

## 用户数据与安全

用户设置和项目文件应写入用户可写目录或用户手动选择的目录。API Key 仅接受当前运行会话内存中的值，不应被持久化到项目目录或系统级目录中。

仓库会忽略用户图片、Excel、ICS、`.scalendar` 文件、虚拟环境、构建产物和秘密文件。发布流程说明见 [docs/release.md](docs/release.md)。

## 阶段状态

| 阶段 | 状态 |
| --- | --- |
| M0 工程环境与最小窗口 | 已实现 |
| M1 数据核心与项目读写 | 已实现 |
| M2 UI 外壳与视觉方向 | 已完成 |
| M3 真实项目数据与手工课表编辑器 | 已完成 |
| M4 课程列表与时间设置增强 | 已完成 |
| M5 图片识别 | 已完成 |
| M6 Excel Import / Export | 已完成 |
| M7 ICS Export | 已完成 |
| M8 Windows EXE / 发布流程 | 已完成 |
| M9 GitHub CI / 构建自动化 | 已完成 |

## 备注

- 这是一个重写后的 V1 版本；旧版历史仍保留在 Git 中，不影响新版本开发。
- 若你希望继续扩展文档，可在后续补充：快速开始示例、截图展示、常见问题、功能路线图和贡献指南。
