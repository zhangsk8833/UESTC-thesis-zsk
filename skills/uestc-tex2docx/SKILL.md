---
name: uestc-tex2docx
description: 将基于 DissertationUESTC 编写的电子科技大学（UESTC）硕士学位论文 LaTeX 源码（.tex / .bib / 插图）自动解析并转换为严格符合《电子科技大学研究生学位论文撰写规范》的 Word（.docx）文档。
---

# 电子科技大学 LaTeX 转合规 Word 技能（UESTC TeX2Docx）

本技能以学校官方《电子科技大学研究生学位论文撰写规范》预设样式文档（`assets/uestc_master_template.docx`）为母版，通过“LaTeX 结构化解析 → 官方样式注入与 OOXML 精准排版 → 合规自动化校验”三步流水线生成 `.docx` 文件。

## 一、转换流水线

1. **解析 LaTeX 工程为结构化 JSON**：
   ```bash
   python3 skills/uestc-tex2docx/scripts/parse_uestc_tex.py \
     --root thesis-template \
     --main main.tex \
     --out thesis_ast.json
   ```
2. **注入官方母版生成合规 Word**：
   ```bash
   python3 skills/uestc-tex2docx/scripts/tex2docx.py \
     --ast thesis_ast.json \
     --template skills/uestc-tex2docx/assets/uestc_master_template.docx \
     --root thesis-template \
     --out thesis_output.docx
   ```
3. **执行 Word 规范自动化校验**：
   ```bash
   python3 skills/uestc-tex2docx/scripts/validate_docx.py \
     --docx thesis_output.docx
   ```

## 二、核心格式保障

- **页面与分节**：A4 纸张（210×297 mm），上下左右边距 30 mm，页眉/页脚距边界 20 mm；前置独创性声明无页眉页码，中英文摘要/目录起罗马数字页码（`Ⅰ, Ⅱ...`），第一章起阿拉伯数字页码（`1, 2...`）且启用奇偶页不同页眉（奇数页为本章标题，偶数页为“电子科技大学硕士学位论文”，带 0.75 磅下边框线）。
- **字体与段落**：中文宋体、英文与数字 Times New Roman；正文小四（12 pt）、固定值行距 20 磅、两端对齐、首行缩进 2 字符；各级标题采用黑体精确字号与段前段后距，相邻无正文标题自动将第二个标题段前距设为 0 磅。
- **三线表与图表公式**：表格采用上下 1.5 磅、表头底线 0.75 磅的三线表；多行图题/表题自动切换“两端对齐+左右缩进 4 字符”；独立公式小四居中、右对齐分章编号 `(X-Y)`（无引导线），下方“式中”顶格解释。
- **文献与成果**：参考文献按 GB/T 7714-2015 五号悬挂缩进输出，正文引用默认上标；成果列表自动加粗本人姓名（通过 `--author` 指定）。

## 三、已知边界与人工复核项

1. **复杂矢量图**：TikZ/PGFPlots 绘制的复杂图形建议先编译导出为高分辨率 PNG（≥300 dpi）后通过 `\includegraphics` 引入，脚本将自动嵌入 Word。
2. **目录与交叉引用域刷新**：生成的 `.docx` 在 Microsoft Word / WPS 中打开后，建议全选（`Ctrl+A`）并按 `F9` 刷新目录与页码域。
