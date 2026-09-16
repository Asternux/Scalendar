# Scalendar V1 架构说明

## 边界

V1 采用 Python + PySide6 + Qt Quick/QML。Python 负责稳定数据模型、校验、文件读写和后续服务编排；QML 负责页面布局、导航、主题和交互状态。两者通过 `bridge/AppController` 连接，避免把业务逻辑散落到 QML。

核心原则是：正确性 > 可维护性 > 用户体验 > 性能 > 简洁性 > 视觉效果。M2 的视觉组件已经先建立，但识别和导出尚未接入。

## 分层

- `core/`：纯 Python 数据和日期逻辑，可脱离 GUI 测试。
- `storage/`：`.scalendar` JSON 的读取、校验和原子替换保存。
- `recognition/`、`importers/`、`exporters/`：为 M3+ 预留适配器边界。
- `bridge/`：Qt 对象和 QML 可调用的最小接口。
- `ui/`：页面、组件、主题 token；页面不直接读写磁盘。

## 后续演进

识别结果应先落到项目模型的草稿对象，用户确认后再成为课程。导出器只能消费已校验的项目与展开后的 occurrence，不应反向改变项目数据。位置解析必须是可选增强：即使地理匹配失败，也保留原始 `location_text` 并允许导出。
