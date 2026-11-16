---
name: uestc-thesis-writer
description: 为电子科技大学专业硕士中文学位论文整理研究材料、规划主线、撰写和修改 LaTeX 章节、自然化润色及导师视角审校。适用于代码和实验转写、已有章节修改、学校规范检查及编译；英文仅限必要摘要和扉页，不处理英文期刊投稿。
---
# 电子科技大学中文专业硕士论文写作

## 目标与边界
以作者真实研究为基础，用中文专业硕士论文语体表达。正文维护在 LaTeX 中，Word 交给独立的 uestc-tex2docx。先确定用户请求的局部范围，不为改一段要求重建全文计划。

研究事实优先于表达偏好。学校明确条款约束格式及规定用语；导师偏好指导论证与措辞；师兄样本只提供风格参考。规则来源见 [导师档案](references/mentor-profile.md) 与 [学校映射](references/school-profile/source-map.md)。不得声称风格规则来自导师本人，除非有可定位的原始意见。

## 必须保持的约束
- 不编造实验数值、模型条件、代码运行结果、文献细节或创新点。未解决项记录在项目 issues 中，正式定稿必须清理。
- 代码能说明实现逻辑，不能单独证明某次实验确已运行；曲线估读不能冒充精确日志。
- 润色前后核对数值、条件、术语、公式、引用键及标签；纯语言修改不更改数学对象和主张强度。
- 中文正文使用本文、本章、具体技术对象等合适主语，按校规避免“我们”。英文摘要以学校学位论文要求为准，不套用 WCL 的 We propose 规则。
- “去 AI 味”指消除空话和机械表达，不能输出检测概率、保证检测通过、故意加错字或降低学术质量。
- 收到“审核”只给诊断；收到“修改”在已授权范围直接改。已有用户确认不重复索取。未明确的研究意图只阻塞依赖它的段落，其余可继续。

## 任务路由
| 当前任务 | 读取资料 | 产物 |
| --- | --- | --- |
| 代码、数据和文献盘点 | [输入与证据](references/intake-and-evidence.md) | 事实表、证据台账、缺口 |
| 大纲与研究主线 | [主线规划](references/outline-and-mainline.md)、[师兄风格](references/senior-style.md) | 问题—方法—证据—章节映射 |
| 章节写作 | [导师档案](references/mentor-profile.md)、相应 [章节指南](references/sections/index.md) | 可编译 LaTeX、缺证项 |
| 文献与综述 | [引用指南](references/literature-and-citations.md) | 文献比较、已验证引用 |
| 自然化或局部润色 | [自然表达](references/natural-academic-prose.md) | 保真改稿、变更说明 |
| 审校与导师反馈 | [审校](references/review-and-revision.md) | 定位问题、修改及状态 |
| 编译、盲审和定稿 | [交付](references/compile-and-delivery.md)、学校映射 | PDF、检查报告 |

只加载当前任务需要的参考；不要一次读取所有章指南或旧错误记录。

## 工作过程
读取现有项目状态与相关源材料，区分事实、作者确认、推断、建议。先确定本段或本章的论证目的，再起草；材料不足时只写可支持的部分。一般先方法与实验，再完善基础、绪论、结论和摘要，但不固定章数或强制重写成熟章节。

修改后检查邻近上下文和引用，报告改了什么、依据什么、仍缺什么。只有用户明确要求维护偏好时才更新导师档案；一次性批注不自动上升为永久规则。

## 可执行检查
脚本路径相对于本 Skill 所在目录；所有论文路径由调用者提供，不依赖当前目录。
```bash
python scripts/thesis_check.py --root <论文目录> --main main.tex --out <报告.json>
python scripts/thesis_check.py --root <论文目录> --main main.tex --final --out <定稿报告.json>
python scripts/compile_thesis.py --root <论文目录> --main main.tex --engine <xelatex路径>
```
静态检查只覆盖标签、引用、占位、启发式语言等可判定项，不能证明研究正确、学术原创或版式合规。编译必须结合渲染检查。
