# `.scalendar` 数据格式（V1 schema 1）

项目文件是 UTF-8 JSON，顶层包括：

```json
{
  "schema_version": 1,
  "project": { "name": "我的课表", "created_at": "...", "updated_at": "..." },
  "semester": {
    "name": "2026 秋季学期",
    "first_week_monday": "2026-09-07",
    "total_weeks": 20,
    "timezone": "Asia/Shanghai"
  },
  "sections": [],
  "courses": []
}
```

课程使用稳定 UUID `id`。课程定义记录星期、起止节次、起止周、全周/单双周/自定义周次、教师、建筑、教室、原始地点文本、颜色、备注和识别状态。一个课程可以展开为多个 occurrence；后续 ICS UID 应基于课程 ID 与 occurrence 身份，而不是表格行号。

V1 先不加入临时调课、停课和临时换教室模型，避免把正式课表核心与例外情况混在一起。新增字段时必须增加 `schema_version` 迁移策略和 round-trip 测试。
