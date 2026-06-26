# 08 Implementation Roadmap

> 本目录定义 AStock V2 的实施路线图。
>
> 目标是把 V2 架构拆解为可执行、可验收、可持续迭代的开发阶段。

---

## 文档范围

```text
08_Implementation_Roadmap/
├── README.md
├── 00_Overview.md
├── 01_Phase_1_KG_Schema.md
├── 02_Phase_2_YAML_Migration.md
├── 03_Phase_3_Reasoning_MVP.md
├── 04_Phase_4_LLM_Extraction.md
├── 05_Phase_5_Validation_Loop.md
├── 06_Phase_6_Web_Explainability.md
└── 07_ADR.md
```

---

## 阶段总览

```text
Phase 1：KG Schema 与基础表
Phase 2：YAML 规则迁移到图谱
Phase 3：Reasoning Engine MVP
Phase 4：LLM 抽取候选关系
Phase 5：Validation Loop 验证闭环
Phase 6：Web Explainability 前端解释层
```

---

## 实施原则

1. 先数据模型，后推理逻辑。
2. 先 YAML seed，后 LLM 自动抽取。
3. 先离线计算，后在线展示。
4. 先保存路径，后优化评分。
5. 先可解释，后复杂算法。
6. 每个阶段必须有可验收产物。

---

## 最小可用目标

V2 MVP 完成后，系统必须支持：

```text
输入一个事件
  ↓
识别影响实体
  ↓
通过图谱找到相关股票
  ↓
展示推理路径
  ↓
展示证据来源
  ↓
记录后续收益验证
```

---

## 非目标

Roadmap 第一阶段不包含：

- 自动交易。
- 高频数据。
- 完整 Neo4j 迁移。
- 多 Agent 自动维护图谱。
- 完全无人审核的 LLM 入库。

---

## 成功标准

每个 Phase 必须满足：

- 有清晰数据库或代码产物。
- 有最小测试样例。
- 有 Web 或 API 可观察结果。
- 能回滚或禁用。
- 不破坏 V1 现有功能。