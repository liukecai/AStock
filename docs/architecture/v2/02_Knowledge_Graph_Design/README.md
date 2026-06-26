# 02 Knowledge Graph Design

> 本目录定义 AStock V2 的产业知识图谱设计。
>
> 目标是让系统能够回答：一只股票为什么涉及某个供应链内容？某个事件如何沿产业链传播到相关公司？每条关系的证据和置信度是什么？

---

## 文档范围

```text
02_Knowledge_Graph_Design/
├── README.md
├── 00_Overview.md
├── 01_Entity_Model.md
├── 02_Relation_Model.md
├── 03_Evidence_Model.md
├── 04_Graph_Building.md
├── 05_Graph_Query.md
├── 06_Graph_Update.md
└── 07_ADR.md
```

---

## 阅读顺序

1. `00_Overview.md`：理解为什么 V2 需要 Knowledge Graph。
2. `01_Entity_Model.md`：理解图谱中的实体类型。
3. `02_Relation_Model.md`：理解图谱中的关系类型。
4. `03_Evidence_Model.md`：理解证据、来源、置信度如何建模。
5. `04_Graph_Building.md`：理解图谱如何从 YAML、公告、年报、LLM 抽取结果构建。
6. `05_Graph_Query.md`：理解图谱如何支持事件推理和个股解释。
7. `06_Graph_Update.md`：理解图谱如何增量更新、合并和校准。
8. `07_ADR.md`：理解图谱设计中的关键决策。

---

## 图谱核心目标

Knowledge Graph 的目标不是替代所有规则，而是把规则升级为可查询、可追溯、可验证的长期知识。

V1 中可能存在这样的规则：

```text
六氟化钨紧缺 -> 中船特气 / 中钨高新
```

V2 中应拆解为：

```text
六氟化钨
  ↓ belongs_to
电子特气
  ↓ belongs_to
半导体材料

中船特气
  ↓ produces
六氟化钨

中钨高新
  ↓ exposed_to
钨材料
```

这样系统不再只记住某个事件对应哪些股票，而是记住事件、商品、材料、行业、公司之间的真实关系。

---

## 图谱核心能力

V2 Knowledge Graph 必须支持：

1. 实体归一化。
2. 多来源证据绑定。
3. 关系置信度。
4. 关系权重。
5. 多跳路径查询。
6. 股票暴露度计算。
7. 事件影响路径解释。
8. 历史验证结果回写。

---

## 基础图谱路径

典型路径：

```text
Event
  ↓ impacts
Commodity / Material
  ↓ belongs_to
Industry
  ↓ related_to
Company
  ↓ maps_to
Stock
```

公司画像路径：

```text
Company
  ↓ produces
Product
  ↓ uses
Material
  ↓ belongs_to
Commodity
  ↓ used_in
Industry
```

---

## 图谱设计原则

### 1. Evidence First

没有证据的关系只能作为候选关系，不能直接进入高置信正式图谱。

### 2. Relation over Label

不要只给股票打标签，而要记录实体之间的关系。

错误方式：

```text
中船特气 tags = [电子特气, 半导体]
```

推荐方式：

```text
中船特气 produces 六氟化钨
六氟化钨 belongs_to 电子特气
电子特气 used_in 半导体制造
```

### 3. Confidence is Required

每条关系必须有置信度。

### 4. Source is Required

每条关系必须尽可能追溯到证据来源。

### 5. Graph is Mutable

图谱不是一次性写死的，而是持续被年报、公告、官网、LLM 抽取、市场验证更新。

---

## 与 Reasoning Engine 的关系

Knowledge Graph 负责存储关系。

Reasoning Engine 负责使用关系。

```text
Knowledge Graph：知道中船特气生产六氟化钨
Reasoning Engine：当六氟化钨紧缺时，推理中船特气可能受益
```

两者必须解耦。