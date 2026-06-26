# 04 Graph Building

> 本文档定义 AStock V2 Knowledge Graph 的构建流程。

---

## 1. Graph Building 目标

图谱构建的目标是将分散信息转化为稳定、可查询、可追溯的产业知识。

输入包括：

```text
YAML 规则库
年报
招股说明书
公告
官网产品目录
互动易
新闻 RSS
LLM 抽取结果
人工维护数据
```

输出包括：

```text
kg_entities
kg_relations
relation_evidence
candidate_entities
candidate_relations
```

---

## 2. 构建流程总览

```text
Raw Source
  ↓
Evidence Collector
  ↓
Extractor
  ↓
Candidate Entity / Relation
  ↓
Normalize / Deduplicate
  ↓
Review / Auto Approval
  ↓
Write Knowledge Graph
  ↓
Validation Feedback
```

---

## 3. YAML Seed 构建

V1 中已有的 YAML 规则作为 V2 图谱初始种子。

YAML 适合保存人工确认过的高价值关系。

示例：

```yaml
entities:
  - name: 六氟化钨
    type: Product
    aliases: [WF6, Tungsten Hexafluoride]

relations:
  - source: 中船特气
    relation: produces
    target: 六氟化钨
    confidence: 0.85
    source_type: yaml_seed
```

加载流程：

```text
YAML
  ↓
Parse
  ↓
Normalize Entity
  ↓
Upsert Entity
  ↓
Upsert Relation
  ↓
Mark source_type = yaml_seed
```

---

## 4. Document-based 构建

文档类来源包括：

- 年报。
- 招股说明书。
- 公告 PDF。
- 产品目录 PDF。

流程：

```text
PDF / HTML
  ↓
Text Extraction
  ↓
Evidence
  ↓
LLM / Rule Extraction
  ↓
Candidate Relations
```

示例抽取关系：

```text
Company -> produces -> Product
Product -> belongs_to -> Material
Product -> used_in -> Industry
```

---

## 5. Website-based 构建

公司官网和产品中心通常包含高价值信息。

流程：

```text
Company Website
  ↓
Product Page Discovery
  ↓
Text / Table Extraction
  ↓
Evidence
  ↓
Candidate Product Relations
```

官网产品目录的可信度通常高于普通新闻，但低于年报和招股书。

---

## 6. News-based 构建

新闻和 RSS 更适合发现新事件和新概念。

新闻不应直接生成高置信关系。

推荐流程：

```text
News
  ↓
Event Extraction
  ↓
Candidate Event Entity
  ↓
Candidate Relation
  ↓
Wait for Confirmation
```

新闻可用于触发图谱补全，但不能单独作为高置信供应链关系来源。

---

## 7. LLM Extraction 构建

LLM 负责从证据中抽取候选实体和候选关系。

LLM 输出必须是结构化 JSON。

输出示例：

```json
{
  "entities": [
    {"name": "六氟化钨", "type": "Product", "aliases": ["WF6"]}
  ],
  "relations": [
    {
      "source": "中船特气",
      "relation": "produces",
      "target": "六氟化钨",
      "evidence_text": "公司主要产品包括六氟化钨...",
      "confidence": 0.86
    }
  ]
}
```

LLM 抽取结果进入 candidate 层。

---

## 8. Entity Normalization

实体归一化用于避免重复节点。

示例：

```text
WF6
Tungsten Hexafluoride
六氟化钨气体
```

统一为：

```text
六氟化钨
```

归一化依据：

- canonical_name。
- aliases。
- 规则词典。
- LLM 建议。
- 人工审核。

---

## 9. Relation Deduplication

相同关系不能重复写入。

唯一键建议：

```text
source_entity_id + relation_type + target_entity_id
```

如果已有关系存在，则追加 evidence 并更新 confidence。

---

## 10. Auto Approval

部分关系可以自动进入正式图谱。

自动通过条件示例：

```text
来源为年报 / 招股书 / 公告
且抽取置信度 >= 0.85
且实体归一化成功
且不存在冲突关系
```

其他关系进入人工审核或候选池。

---

## 11. Conflict Handling

冲突示例：

```text
来源 A：公司生产某产品
来源 B：公司已剥离该产品业务
```

处理方式：

- 保留两条 evidence。
- 关系状态标记为 needs_review。
- 降低 confidence。
- 等待人工或后续公告确认。

---

## 12. Incremental Building

图谱构建必须支持增量。

每次新增证据只处理新内容。

```text
new_evidence
  ↓
extract
  ↓
merge
  ↓
update graph
```

不得每次全量重建图谱。

---

## 13. Graph Building 设计原则

1. 先证据，后关系。
2. LLM 输出只进入候选层。
3. 高质量来源可自动通过。
4. 关系合并优先于重复创建。
5. 冲突关系必须保留审计信息。
6. 图谱构建必须幂等。
7. YAML 是种子，不是长期唯一维护方式。

---

## 14. 结论

Graph Building 是 V2 的知识生产流程。

它将原始材料转化为可推理的产业知识，并通过证据、置信度和审核机制保证图谱质量。