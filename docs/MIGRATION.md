# 与原型版本的关系

本次在 `codex/chinese-thesis-skills` 分支更新，基线提交为 e40c8c4aa4cd639bdea5d49b24a2f529e1b8ee3e；main 不修改。

旧版按行处理 LaTeX 的 parse_uestc_tex/tex2docx 脚本被 AST 转换流程替代；deai_scanner 的词表提示改为自然表达与事实保真审校，不提供检测概率。旧模板的预设研究内容一/二结构与示例数值改为可调整的占位章节。旧文件可从上述 Git 历史查看，未作为活动 Skill 混入新版本。

迁移已有真实论文时，保留自己的章节、参考文献和图像，不覆盖为本包骨架。先将封面信息移入 metadata.tex，建立 project/ 记录，然后按转换支持矩阵选一章验证。main-print.tex 仅作为打印编译入口，Word 转换使用 main.tex。

模板 class/bst、字体和校徽沿用原仓库内容；本次不新增系统字体至 Git。学校 DOCX 和师兄论文只在本地用于规范/风格提炼，不随提交上传。
