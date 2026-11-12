---
name: uestc-thesis-writer
description: 电子科技大学（UESTC）专业硕士学位论文全流程写作、防 AI 检测润色、导师偏好对齐与校规自检技能。当用户提供实验结果、仿真代码、参考文献并要求撰写、改写、去 AI 痕、审校或编译基于 DissertationUESTC 的硕士论文时使用。
---

# 电子科技大学专业硕士学位论文写作技能（UESTC Thesis Writer）

本技能专为电子科技大学专业硕士学位论文撰写设计，深度融合**课题组导师学术偏好（最高权重）**、**师兄论文行文范式**、**防 AIGC 检测策略**与**学校官方撰写规范**，并与 `thesis-template/` LaTeX 工程无缝联动。

## 一、不可逾越的写作红线（Hard Guardrails）

1. **真实性红线（严禁编造）**：任何实验指标、仿真参数、对比基线数据、公式编号或文献 DOI/页码必须严格源自用户提供的代码、日志、实验图或 `.bib` 文件。未提供的数值一律标注 `% [待补充实验数据: <说明>]`，严禁估算或捏造。
2. **导师偏好最高权重**：撰写与修改前必须先遵守 `knowledge_base/mentor_style_profile.md`（逻辑显式承接、物理机制精确对应、禁用夸张词与绝对化结论、严禁出现“我们”）。
3. **LaTeX 语义无损**：润色与去 AI 改写时，必须原样保留所有 `\cite{}`、`\ref{}`、`\eqref{}`、`\label{}`、数学公式环境与模板宏命令。
4. **先做后写、由内向外**：优先完成核心方法与仿真实验章（第 3~4 章），再补充理论基础（第 2 章），最后统一收束第 1 章绪论、最后一章结论与中英文摘要。

## 二、自动任务路由表

根据用户请求自动匹配对应模式，并按需读取指定文件（**不要一次性全量加载无关文件**）：

| 模式 | 触发场景示例 | 必读参考文件 | 联动脚本 |
| :--- | :--- | :--- | :--- |
| **1. 资产建档与大纲规划** | “根据我的代码和实验结果规划论文大纲” | `references/workflow_order.md`、`knowledge_base/senior_style_guide.md` | 更新 `thesis-template/manifest.yaml` |
| **2. 章节撰写 / 结构仿写** | “根据实验日志写第三章”“按师兄风格写绪论” | `knowledge_base/mentor_style_profile.md`、`knowledge_base/senior_style_guide.md`、对应 `references/section_guides/*.md` | `scripts/check_uestc_tex.py` |
| **3. 防 AI 检测润色（De-AIGC）** | “这段 AI 味太重，帮我降 AIGC”“润色第四章语言” | `references/de_aigc_guide.md`、`knowledge_base/mentor_style_profile.md` | `scripts/deai_scanner.py` |
| **4. 导师视角审校与校规终检** | “按导师标准审一下第 3 章”“检查是否符合校规” | `references/audit_checklist.md`、`knowledge_base/uestc_spec_rules.md`、`knowledge_base/error_log.md` | `scripts/check_uestc_tex.py` |
| **5. 编译与报错诊断** | “帮我编译论文”“Overleaf/XeLaTeX 报错排查” | `knowledge_base/uestc_spec_rules.md` | `scripts/compile_thesis.py` |

## 三、标准 6 步执行工作流

1. **读取上下文与资产清单**：检查 `thesis-template/manifest.yaml` 及用户提供的代码、实验结果、参考论文，明确“已有事实”与“缺失项”。
2. **加载约束知识库**：读取 `knowledge_base/mentor_style_profile.md` 与 `knowledge_base/error_log.md`，并按路由表加载对应章节指南。
3. **信息来源四分类标注（内部校验）**：草拟前区分`[原始数据/代码]`、`[用户确认]`、`[合理机制推断]`、`[建议扩展]`，确保推断部分不越界为虚假实验结论。
4. **生成/改写 LaTeX 正文**：直接编辑对应 `chapters/*.tex`（或按用户要求输出完整 `.tex` 片段），遵循电子科大符号、图表引导与“本章小结”规范。
5. **自动化双检（校规 + 去 AI）**：
   - 运行 `python3 skills/uestc-thesis-writer/scripts/check_uestc_tex.py --root thesis-template`
   - 运行 `python3 skills/uestc-thesis-writer/scripts/deai_scanner.py --target <章节.tex>`
6. **问题闭环与沉淀**：修复脚本检出的硬性违规项；若用户反馈了新的导师修改意见，主动将其记录至 `knowledge_base/error_log.md`。
