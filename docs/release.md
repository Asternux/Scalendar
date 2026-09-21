# 构建与发布

V1.0.0 使用 Qt for Python 官方 `pyside6-deploy`（Nuitka standalone 模式）生成 Windows 便携版；部署配置为 [pysidedeploy.spec](../pysidedeploy.spec)，构建脚本为 [tools/build_windows.ps1](../tools/build_windows.ps1)，产物写入 `build\release\Scalendar`，不进入 Git。构建脚本会校验 EXE、shiboken6、Qt plugins 和 QML 资源，并启动便携版做冒烟测试。M5 的 OpenAI Vision 请求需要用户在运行会话中提供 API Key；该 Key 不属于发布包或项目文件。M6 的 XLSX 读写和 M7 的 ICS 写入使用 Python 标准库边界，不要求安装 Excel 或 Apple 软件。

GitHub Actions 配置位于 `.github/workflows/`：`ci.yml` 负责 Windows 测试与编译检查；`windows-package.yml` 在手动触发或推送版本 Tag 时构建便携版并上传临时 artifact。仓库默认分支为 `rewrite/v1`，旧版 `main` 与 `v0.0.0-test` 继续作为历史基线保留。

建议发布检查：

1. `pytest` 全部通过，并运行 `python -m compileall -q src tests`。
2. 从用户可写目录启动，验证不向 `Program Files` 写入项目、设置或导出文件。
3. 检查 Qt/QML 资源、最小窗口尺寸、滚动区域和高 DPI 显示。
4. 用不含秘密、用户图片、Excel、ICS 和临时文件的干净工作区构建。
5. 运行 `tools\build_windows.ps1`，确认 `build\release\Scalendar\Scalendar.exe` 存在并能启动。
6. 在无开发环境的 Windows 机器上验证启动、项目保存、XLSX/ICS 导出和用户可写目录行为。
7. 在 GitHub Actions 通过后创建 `v1.0.0` tag；`Windows package` 工作流会生成便携版 artifact。

EXE、安装包、签名证书和发布日志均不应提交 Git；它们应作为 GitHub Release 构建产物上传。当前版本不包含安装器、自动更新、邮件推送或云服务。

部署说明：`pyside6-deploy` 会收集 PySide6、shiboken6、Qt plugins 和 QML 模块，不能只复制单个 EXE。Windows Nuitka 依赖扫描对非 ASCII 的 Python/Qt 安装路径不稳定，因此构建脚本会在用户临时目录建立 ASCII staging environment，并复制当前项目虚拟环境中的已锁定依赖；这不会改变运行时数据目录，也不会把构建虚拟环境提交到仓库。若系统临时目录本身含非 ASCII 路径，应在 ASCII 路径下构建或使用 GitHub Actions。
