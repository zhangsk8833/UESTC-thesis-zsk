# 电子科技大学中文专业硕士论文工作包

适用于中文专业硕士学位论文，英文只用于学校要求的摘要和扉页。研究内容由作者材料决定；本包不提供虚构实验，不保证任何 AI 检测结果。

## 内容
- `skills/uestc-thesis-writer`：导师偏好、材料证据、主线与章节写作、自然表达、引用审校及编译。
- `thesis-template`：基于 DissertationUESTC 的 `promaster` 工程；`main.tex` 电子阅读入口，`main-print.tex` 打印入口。
- `skills/uestc-tex2docx`：LaTeX → Pandoc AST → editable OMML/Word，独立转换和验收。
- `school-profile`：学校规则与依据；`examples/conversion-demo`：专用转换测试数据，不是论文内容。
- `validation/REPORT.md`：实际完成的验证与当前边界。请先看这个文件再判断转换器能否处理你的全文。

## 开始使用
1. 将两个 Skill 文件夹复制到 Codex 的 skills 目录，重启或重新打开会话使其可发现。保留已有技能的备份。Skill 路径不依赖这台电脑的用户名。
2. 安装 Python 依赖 `python -m pip install -r requirements.txt`；准备 Pandoc 3.4+ 和 TeX Live 2024+。旧 TeX Live 2020 不能作为此模板的验证环境。
3. 复制 thesis-template 为实际论文项目；填写 metadata.tex 和 project/brief.json，提交实验原始结果、代码及主要参考文献。先建立证据与章节映射，再写章节。
4. 对 Codex 说：“使用 $uestc-thesis-writer，依据这些材料先完成输入盘点和章节主线。所有缺证结论记录在 issues 中。”局部改稿可直接指定章节，不必重走所有阶段。
5. Word 输出时说：“使用 $uestc-tex2docx 转换此项目，使用我提供的学校专业硕士封面与规范，更新域并逐页检查。”命令见相应 SKILL.md。

模板是可编译的写作骨架，待填字段和章节提示刻意保留，`--final` 检查应失败，不能当作已完成论文。完整版不是一键支持所有 LaTeX 宏包：复杂环境需按支持矩阵适配。

## 设计依据
重点采用 Digital-Mentor 的导师论证偏好，以及 academic-writing-skills 的写作任务划分和证据审校思路；参考其他项目的规范组织、中文论文工作流和 Word 构建经验。导师规则逐条区分原始依据与中文适配，师兄论文仅提炼写法，不复制内容或研究框架。见 `docs/SOURCES.md`、`THIRD_PARTY_NOTICES.md`。

用户资料、原始师兄论文、学校 DOCX 原件、未发表实验和本机绝对路径不随公共工作包上传。学校模板在运行时由用户提供。
