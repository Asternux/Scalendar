# 构建与发布（草案）

M7 已完成并建立 checkpoint。M8 使用 PyInstaller 生成 Windows 便携版；构建脚本为 [tools/build_windows.ps1](../tools/build_windows.ps1)，产物写入 `build\dist\Scalendar`，不进入 Git。M5 的 OpenAI Vision 请求需要用户在运行会话中提供 API Key；该 Key 不属于发布包或项目文件。M6 的 XLSX 读写和 M7 的 ICS 写入使用 Python 标准库边界，不要求安装 Excel 或 Apple 软件。

建议发布检查：

1. `pytest` 全部通过。
2. 从用户可写目录启动，验证不向 `Program Files` 写入项目、设置或导出文件。
3. 检查 Qt/QML 资源、最小窗口尺寸、滚动区域和高 DPI 显示。
4. 用不含秘密、用户图片、Excel、ICS 和临时文件的干净工作区构建。
5. 运行 `tools\build_windows.ps1`，确认 `build\dist\Scalendar\Scalendar.exe` 存在。
6. 在无开发环境的 Windows 机器上验证启动、项目保存、XLSX/ICS 导出和用户可写目录行为。

EXE、安装包、签名证书和发布日志均不应提交 Git；它们应作为 Release 构建产物上传。
