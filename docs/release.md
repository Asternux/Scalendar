# 构建与发布（草案）

当前 M0–M5 只提供源码运行方式，尚未生成正式 Windows EXE。发布前需要在干净的 Windows 构建环境中安装项目依赖，运行测试，再使用 PyInstaller 或等价方案打包 PySide6/QML 资源。M5 的 OpenAI Vision 请求需要用户在运行会话中提供 API Key；该 Key 不属于发布包或项目文件。

建议发布检查：

1. `pytest` 全部通过。
2. 从用户可写目录启动，验证不向 `Program Files` 写入项目、设置或导出文件。
3. 检查 Qt/QML 资源、最小窗口尺寸、滚动区域和高 DPI 显示。
4. 用不含秘密、用户图片、Excel、ICS 和临时文件的干净工作区构建。
5. 生成安装包或便携包后，在无开发环境的 Windows 机器上验证启动。

EXE、安装包、签名证书和发布日志均不应提交 Git；它们应作为 Release 构建产物上传。
