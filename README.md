# UESTC-thesis-zsk：电子科技大学专业硕士论文 Skill 与模板工程

本仓库整合了课题组导师学术偏好（[Digital-Mentor](https://github.com/Gavin-Jiang-97/Digital-Mentor)）、开源学术写作与去 AI 检测实践（[academic-writing-skills](https://github.com/bahayonghang/academic-writing-skills)、[codex-claude-academic-skills](https://github.com/zLanqing/codex-claude-academic-skills)、[paper-write](https://github.com/xstongxue/best-skills/blob/main/skills/paper-write/SKILL.md)、[master-thesis-studio-skill](https://github.com/darksider-9/master-thesis-studio-skill)），以及电子科技大学专业硕士撰写规范与 [DissertationUESTC](https://github.com/MGG1996/DissertationUESTC) LaTeX 模板。

## 目录结构

- `skills/uestc-thesis-writer/`：专硕论文写作、防 AIGC 润色、导师偏好对齐与校规自检 Skill。
- `skills/uestc-tex2docx/`：将 `DissertationUESTC` LaTeX 源码一键转为符合学校官方规范的 Word（`.docx`）文档。
- `thesis-template/`：基于 `DissertationUESTC` 改造的专业硕士（`promaster`）模块化 LaTeX 工程模板。

## 快速安装 Skill

### Claude Code / Codex 全局安装
```bash
cp -r skills/uestc-thesis-writer ~/.claude/skills/
cp -r skills/uestc-tex2docx ~/.claude/skills/
# 如使用 Codex，将 ~/.claude/skills/ 替换为 ~/.codex/skills/
```

## 补全模板类文件（首次使用）

本仓库已预置完整模块化 `main.tex`、`chapters/*.tex` 与 `latexmkrc`。首次编译前，请从上游仓库 [MGG1996/DissertationUESTC](https://github.com/MGG1996/DissertationUESTC) 复制以下三个核心文件/目录放入 `thesis-template/`：
- `DissertUESTC.cls`
- `DissertUESTC.bst`
- `font/`

## 标准写作与交付工作流

1. **填写资产清单**：将实验结果路径、仿真代码路径与核心参考文献填入 `thesis-template/manifest.yaml`。
2. **由内向外撰写**：调用 `uestc-thesis-writer`，按“第 3~4 章方法与实验 → 第 2 章理论基础 → 第 1 章绪论 → 结论与摘要”逐章写入 `thesis-template/chapters/*.tex`。
3. **防 AI 润色与校规双检**：
   ```bash
   python3 skills/uestc-thesis-writer/scripts/check_uestc_tex.py --root thesis-template
   python3 skills/uestc-thesis-writer/scripts/deai_scanner.py --target thesis-template/chapters/chap03_work1.tex
   ```
4. **编译 PDF（本地 XeLaTeX 或 Overleaf TeXLive 2024）**：
   ```bash
   python3 skills/uestc-thesis-writer/scripts/compile_thesis.py --root thesis-template --main main
   ```
5. **一键转合规 Word**：
   ```bash
   python3 skills/uestc-tex2docx/scripts/parse_uestc_tex.py --root thesis-template --main main.tex --out thesis_ast.json
   python3 skills/uestc-tex2docx/scripts/tex2docx.py --ast thesis_ast.json --template skills/uestc-tex2docx/assets/uestc_master_template.docx --root thesis-template --out thesis_output.docx
   python3 skills/uestc-tex2docx/scripts/validate_docx.py --docx thesis_output.docx
   ```
