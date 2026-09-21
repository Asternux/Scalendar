# `.scalendar` 数据格式（V1 schema 1）

项目文件是 UTF-8 JSON，顶层包括：

```json
{
  "schema_version": 1,
  "project": {
    "name": "我的课表",
    "school": "",
    "campus": "",
    "created_at": "...",
    "updated_at": "..."
  },
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

课程使用稳定 UUID `id`。课程定义记录星期、起止节次、起止周、全周/单双周/自定义周次、教师、建筑、教室、原始地点文本、颜色、备注和识别状态。图片识别导入的课程可以额外带 `needs_review_fields` 字段，记录尚未由用户确认的字段名；旧 schema 1 文件缺少该字段时按空列表读取。项目的 `school`、`campus` 同样是 schema 1 中的可选兼容字段，旧文件缺失时按空字符串读取。一个课程可以展开为多个 occurrence；ICS UID 基于课程 ID、实际日期和节次，而不是表格行号。地点的经纬度不是当前 schema 的可信字段，ICS 默认只输出地点文本。

V1 先不加入临时调课、停课和临时换教室模型，避免把正式课表核心与例外情况混在一起。新增字段时必须增加 `schema_version` 迁移策略和 round-trip 测试。
