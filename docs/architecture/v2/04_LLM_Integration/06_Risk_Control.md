# 06 Risk Control

> 本文档定义 AStock V2 中 LLM 接入的风险控制设计。

---

## 1. 风险控制目标

LLM 可以提高信息抽取效率，但也会带来风险。

主要风险包括：

- 幻觉。
- 过度推断。
- 实体误匹配。
- 关系方向错误。
- 来源质量过低。
- 输出格式不稳定。
- 将传闻当事实。
- 将计划当现有业务。

Risk Control 的目标是确保 LLM 不污染正式图谱。

---

## 2. 风险边界

LLM 不允许直接：

- 写入正式图谱。
- 修改关系权重。
- 修改验证结果。
- 生成最终股票推荐。
- 覆盖人工确认关系。

LLM 只允许写入候选层。

---

## 3. 输出格式风险

LLM 可能输出非法 JSON。

控制措施：

- 强制 JSON Schema 校验。
- 必填字段校验。
- 枚举值校验。
- confidence 范围校验。
- evidence_text 非空校验。

不合法输出不得入库。

---

## 4. 幻觉风险

幻觉表现：

- 编造产品。
- 编造客户。
- 编造供应商。
- 编造产业链关系。
- 编造事件影响方向。

控制措施：

- 每条关系必须包含 evidence_text。
- evidence_text 必须来自原文。
- 无 evidence_text 的结果直接拒绝。
- 高风险来源必须人工审核。

---

## 5. 过度推断风险

示例：

原文：

```text
公司产品可用于半导体行业。
```

错误推断：

```text
公司是 HBM 供应商。
```

控制措施：

- 区分直接关系和间接关系。
- 使用 support_type。
- 间接关系降低 confidence。
- 热点概念关系必须审核。

---

## 6. 实体误匹配风险

同名实体可能导致误匹配。

控制措施：

- 使用 entity_type。
- 使用 aliases。
- 使用股票代码或公司名称辅助。
- 无法确认时进入 candidate entity。

---

## 7. 关系方向风险

关系方向错误会严重影响推理。

示例错误：

```text
六氟化钨 produces 中船特气
```

正确关系：

```text
中船特气 produces 六氟化钨
```

控制措施：

- predicate 与 subject_type / object_type 校验。
- 关系方向规则校验。
- 不合法关系直接拒绝。

---

## 8. 来源质量风险

不同来源可信度不同。

控制措施：

- 来源基础可信度分级。
- 低质量来源不能单独生成 active relation。
- 新闻和社交讨论默认 candidate。
- 年报和招股书可自动通过高置信关系。

---

## 9. 传闻风险

市场传闻可能有价值，但不能当作事实。

处理方式：

```text
传闻 -> Event Candidate
传闻 -> 不生成高置信公司产品关系
传闻 -> 需要行情或多源验证
```

---

## 10. 计划与现有业务混淆风险

原文可能描述：

- 计划建设。
- 拟投资。
- 正在研发。
- 已量产。

这些状态必须区分。

关系状态建议：

```text
planned
under_construction
in_rnd
in_production
terminated
```

不能把 planned 当作 in_production。

---

## 11. 成本风险

LLM 调用成本可能随文档数量增加。

控制措施：

- 文档分块。
- 增量抽取。
- 缓存抽取结果。
- 相同 content_hash 不重复调用。
- 优先处理高价值文档。

---

## 12. 审计要求

每次 LLM 调用应记录：

```text
prompt_name
prompt_version
model_name
input_hash
output_hash
source_evidence_id
created_at
status
```

便于问题复盘。

---

## 13. 风险控制原则

1. LLM 只进候选层。
2. 没有 evidence_text 不入库。
3. 低质量来源不自动通过。
4. 热点概念必须谨慎。
5. 计划和现有业务必须区分。
6. 所有抽取任务必须可审计。
7. 输出不合法直接拒绝。

---

## 14. 结论

LLM 风险控制的核心不是不用 LLM，而是把 LLM 限定在可审计、可回滚、可审核的候选层中。

这样既能利用 LLM 的抽取能力，又能保护 Knowledge Graph 的可信度。