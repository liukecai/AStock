# 06 DTO Error Design

> 本文档定义 AStock V2 API 的统一 DTO 与错误响应规范。

---

## 1. 设计目标

DTO 和错误结构用于保证前后端契约稳定。

目标：

- 响应结构统一。
- 错误格式统一。
- 分页格式统一。
- 前端处理简单。
- API 可版本化演进。

---

## 2. 成功响应

统一结构：

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {}
}
```

---

## 3. 失败响应

统一结构：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Entity not found",
    "details": {}
  },
  "meta": {}
}
```

---

## 4. 分页响应

meta 中包含分页信息：

```json
{
  "page": 1,
  "page_size": 20,
  "total": 100,
  "has_next": true
}
```

---

## 5. 错误码分类

常见错误码：

```text
BAD_REQUEST
VALIDATION_ERROR
ENTITY_NOT_FOUND
EVENT_NOT_FOUND
STOCK_NOT_FOUND
RELATION_NOT_FOUND
JOB_NOT_FOUND
INTERNAL_ERROR
SERVICE_UNAVAILABLE
```

---

## 6. DTO 命名

DTO 命名建议：

```text
EntityDTO
RelationDTO
EvidenceDTO
EventDTO
ReasonPathDTO
StockExposureDTO
StockScoreDTO
ValidationResultDTO
JobRunDTO
```

---

## 7. 时间格式

所有时间字段使用 ISO 8601 字符串。

示例：

```text
2026-06-27T10:30:00+08:00
```

---

## 8. 分数字段

分数字段应明确范围：

```text
confidence: 0.0 - 1.0
exposure_score: 0.0 - 1.0
final_score: 0 - 100
```

---

## 9. 空值处理

缺失数据使用 null。

不要使用空字符串表达缺失。

对于列表字段，缺失时返回空数组。

---

## 10. 设计原则

1. API 不直接返回 ORM 对象。
2. 所有响应结构统一。
3. 所有错误结构统一。
4. 分数字段必须明确范围。
5. 时间字段必须统一格式。
6. 缺失数据使用 null 或空数组。

---

## 11. 结论

DTO 和错误响应规范是 API 可维护性的基础。

统一结构能降低前端复杂度，也便于后续 API 版本演进。