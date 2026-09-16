# Scalendar V1 架构说明

## 边界

V1 采用 Python + PySide6 + Qt Quick/QML。Python 负责稳定数据模型、校验、文件读写和后续服务编排；QML 负责页面布局、导航、主题和交互状态。两者通过 `bridge/AppController` 连接，避免把业务逻辑散落到 QML。

核心原则是：正确性 > 可维护性 > 用户体验 > 性能 > 简洁性 > 视觉效果。M2 的视觉组件已经先建立，但识别和导出尚未接入。

## 分层

- `core/`：纯 Python 数据和日期逻辑，可脱离 GUI 测试。
- `storage/`：`.scalendar` JSON 的读取、校验和原子替换保存。
- `recognition/`：M5 的 provider-neutral 识别边界。`RecognitionProvider` 只处理图片和识别服务；`CandidateCourse` / `RecognitionResult` 是独立 DTO，经过 `normalizer` 后才转换为 Core `Course`。OpenAI 适配器使用 Responses API 的图片输入和严格 JSON Schema 输出，不依赖 Qt/QML，也不直接修改项目。
- `importers/`、`exporters/`：为 M6/M7 的 Excel 和 ICS 适配器预留边界。
- `bridge/`：Qt 对象、`QAbstractListModel`、排序 proxy 和 QML 可调用的最小接口。Timetable 与 Course List 共享同一个 `CourseListModel`；Course List 的排序只作用于 `CourseSortProxyModel`，不会改写项目数据顺序。编辑器使用独立的未保存状态对象。
- `ui/`：页面、组件、主题 token；页面不直接读写磁盘。

## 后续演进

项目生命周期由 `AppController` 负责：创建空白项目、加载、保存、debounce autosave、课程增删改、课程列表批量操作、学期设置和节次更新。批量操作先在候选 `ProjectDocument` 上完整校验，成功后才一次性替换，避免半完成数据。节次允许时间重叠，但 `SectionListModel` 会为涉及的节次提供警告；非法的开始/结束时间会被拒绝。缩短学期周数若会使课程越界会被阻止，不自动静默截断。保存前仍由 Core validation 拦截非法数据，`.scalendar` 是唯一真相源。图片识别结果先停留在 `RecognitionCandidateModel` 中；未知数字保持待确认状态，用户确认后才新增课程，且不会替换现有课程。导出器只能消费已校验的项目与展开后的 occurrence，不应反向改变项目数据。位置解析必须是可选增强：即使地理匹配失败，也保留原始 `location_text` 并允许导出。
