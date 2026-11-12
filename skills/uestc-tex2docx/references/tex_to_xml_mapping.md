# LaTeX 命令到 Word OOXML 映射规则

1. **章节层次映射**：
   - `\chapter{标题}` → 新建 Word 分节（设置奇数页页眉为`第X章 标题`，偶数页为`电子科技大学硕士学位论文`），写入 `Heading 1` 样式；
   - `\section{标题}` → 映射 `Heading 2`；`\subsection{标题}` → 映射 `Heading 3`；`\subsubsection{标题}` → 映射 `Heading 4`。
2. **中英混排字体分离**：
   - 遍历文本 Run：中文及全角标点指定 `w:eastAsia="宋体"`（标题用`"黑体"`），ASCII 字母与数字指定 `w:ascii="Times New Roman"`、`w:hAnsi="Times New Roman"`。
3. **引用与交叉引用映射**：
   - `\cite{k1,k2}` → 解析 `.bib` 顺序编号，输出上标 `[1, 2]`（若前文紧邻“文献”二字则输出非上标 `[1, 2]`）；
   - `\ref{fig:xxx}` / `\ref{tab:xxx}` / `\eqref{eq:xxx}` → 解析为对应分章编号（如 `3-1`、`(3-1)`）。
4. **三线表映射**：
   - 解析 `tabular` / `booktabs`（`\toprule`、`\midrule`、`\bottomrule`），通过 `lxml` 操作 `w:tcBorders` / `w:tblBorders`，隐藏左右竖线，设置顶/底边框 `sz=12`（1.5pt）、表头底线 `sz=6`（0.75pt）。
5. **公式右对齐编号布局**：
   - 采用 3 列无边框满宽表格（左列 15% 空白、中列 70% 居中公式、右列 15% 右对齐 `(X-Y)`），确保公式严格居中且编号贴右边界、无引导线。
