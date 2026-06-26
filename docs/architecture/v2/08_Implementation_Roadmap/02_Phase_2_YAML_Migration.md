# 02 Phase 2 YAML Migration

> Phase 2 目标：将 V1 YAML 规则迁移为 V2 Knowledge Graph 的种子数据。

---

## 1. 阶段目标

V1 已有规则不是废弃资产，而是 V2 图谱的初始知识来源。

Phase 2 目标是实现：

```text
YAML Rules
  ↓
yaml_to_kg_loader
  ↓
kg_entities / kg_relations / relation_evidence
```

---

## 2. 开发任务

新增脚本：

```text
scripts/yaml_to_kg_loader.py
```

新增配置：

```text
config/kg_seed.yaml
config/entity_aliases.yaml
config/relation_types.yaml
```

新增服务能力：

```text
upsert_entity
upsert_relation
resolve_alias
append_evidence
```

---

## 3. YAML Seed 格式

示例：

```yaml
entities:
  - name: 产品A
    type: Product
    aliases: [AliasA]

relations:
  - source: 公司A
    source_type: Company
    relation: produces
    target: 产品A
    target_type: Product
    confidence: 0.85
    weight: 0.80
    source_type_label: yaml_seed
```

---

## 4. 迁移规则

迁移时必须：

1. 先创建实体。
2. 再创建关系。
3. aliases 写入实体别名。
4. source_type 标记为 yaml_seed。
5. 重复关系执行 upsert。
6. 不重复插入同一关系。

---

## 5. 验收用例

导入一组供应链 seed：

```text
公司A -> produces -> 产品A
产品A -> belongs_to -> 材料A
材料A -> belongs_to -> 行业A
```

然后查询：

```text
产品A 的邻居
公司A 的产品
行业A 相关公司
```

---

## 6. 验收标准

1. YAML 能被成功解析。
2. 实体能自动 upsert。
3. 关系能自动 upsert。
4. 重复执行 loader 不产生重复数据。
5. API 能查询迁移后的实体和关系。
6. 每条关系包含 confidence、weight、source_type。

---

## 7. 风险控制

主要风险：

- YAML 字段不统一。
- 实体别名重复。
- 旧规则语义不清。

控制方式：

- 先支持最小 YAML schema。
- 对无法识别字段直接报错。
- 对冲突实体写入候选层。

---

## 8. 结论

Phase 2 让 V1 规则资产进入 V2 图谱体系，是从规则驱动转向知识驱动的第一步。