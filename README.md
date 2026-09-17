# Scalendar V1

Scalendar V1 是课表图片到日历的全新 Windows 桌面重写。它与旧测试版保持 Git 历史隔离：旧版基线仍在 `main` 与 `v0.0.0-test`，新版本只在 `rewrite/v1` 开发。

当前 V1.0.0 交付范围是 Milestone 0–9：完成 Python/PySide6/QML 工程骨架、真实 `.scalendar` 项目生命周期、可编辑课程模型、课程列表多选批量操作、学期与节次设置、图片导入与 OpenAI Vision 结构化识别候选、标准 XLSX 导入/导出、面向 Apple 日历的 ICS 导出，以及可复现的 Windows 便携版 EXE 构建和 GitHub Actions 自动化。推送和真实地图位置解析暂未实现，这是有意保留的后续阶段。

## 开发环境

- Python 3.11+
- PySide6 6.8+
- Windows 10/11（目标平台）

建议使用项目自己的虚拟环境。程序和测试均不要求 PowerShell 作为最终用户入口；PowerShell 命令只用于开发。

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

也可以在安装项目后运行：

```powershell
scalendar
```

Windows 便携版构建使用：

```powershell
.\tools\build_windows.ps1
```

产物位于 `build\release\Scalendar\Scalendar.exe`，构建目录不会提交 Git。Windows 发布使用 Qt for Python 官方 `pyside6-deploy`，配置见 `pysidedeploy.spec`；构建脚本会验证 shiboken6、Qt plugins、QML 资源并启动 EXE 做冒烟测试。

GitHub Actions：普通 push / pull request 会在 Windows runner 上运行测试；手动触发 `Windows package` 或推送版本 Tag 时，会生成短期保留的便携版构建产物。Actions 不会自动创建 Release，也不会替代用户确认后的发布流程。

当前 GUI 启动后会打开 Home 页面。可以创建空白课表、添加/编辑/删除课程、在课表和课程列表间同步编辑、按星期/节次/名称排序、多选批量修改周次或地点、修改学期设置和节次时间、保存并重新打开 `.scalendar`。导入页支持 PNG/JPG/JPEG/WEBP 图片以及 XLSX 文件选择或拖拽；图片识别请求不会自动发起，Excel 和视觉识别结果都会先进入候选确认，再以新增课程方式导入。导出页支持标准 XLSX 和 ICS；ICS 会按实际课程日期生成事件。格式说明见 [docs/excel.md](docs/excel.md) 和 [docs/ics.md](docs/ics.md)。

## 架构

```text
src/scalendar/
├── main.py                 # Qt 应用入口
├── core/                   # 纯数据模型、校验、课表日期计算
├── storage/                # .scalendar JSON 项目读写
├── recognition/            # 图片识别 provider 与候选结果规范化
├── importers/              # Excel 输入适配器与外部表格兼容层
├── exporters/              # XLSX / ICS 输出适配器
├── bridge/                 # Python 与 QML 的控制器边界
└── ui/                    # Qt Quick/QML 页面、组件和主题
```

项目文件是 UTF-8 JSON，扩展名为 `.scalendar`。它是唯一数据源，Excel 是可审阅、可交换的导入/导出格式，不是内部真相源。详见 [docs/architecture.md](docs/architecture.md)、[docs/data-format.md](docs/data-format.md) 和 [docs/excel.md](docs/excel.md)。

## 用户数据与安全

用户设置和项目文件应写入用户可写目录（例如 `%LOCALAPPDATA%\Scalendar`）或用户选择的目录，不写入 `Program Files`。API Key 只接受当前运行会话内存中的值，不能写入项目、日志或 Git；关闭程序后需要重新设置。

仓库忽略用户图片、Excel、ICS、`.scalendar`、虚拟环境、构建产物和秘密文件。发布流程见 [docs/release.md](docs/release.md)。

## 阶段状态

| 阶段 | 状态 |
| --- | --- |
| M0 工程环境与最小窗口 | 已实现 |
| M1 数据核心与项目读写 | 已实现 |
| M2 UI 壳层与视觉方向 | 已完成，checkpoint `7d4a5b0036cc` |
| M3 真实项目数据与手工课表编辑器 | 已完成，checkpoint `ee72e9343c13` |
| M4 课程列表与时间设置增强 | 已完成，checkpoint `25abd66d180f` |
| M5 图片识别 | 已完成，checkpoint `35c2a64` |
| M6 Excel Import / Export | 已完成，checkpoint `bb3bcc080d48` |
| M7 ICS Export | 已完成，checkpoint `132f0b7f0497` |
| M8 Windows EXE / 发布流程 | 已完成，checkpoint `87b9ec36757c` |
| M9 GitHub CI / 构建自动化 | 已完成，checkpoint `6a270d3eb788` |
