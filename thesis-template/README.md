# 中文专业硕士论文起始包

填写 metadata.tex，替换 chapters 和 frontmatter 的待补文本。章数仅为起始结构，可按研究主线增加或合并；正式论文不要保留待补内容。正文以LaTeX为唯一来源。

使用XeLaTeX（上游推荐TeX Live 2024及以上）编译 main.tex，印刷入口 main-print.tex。文件夹必须包含原版 DissertUESTC.cls、DissertUESTC.bst、font/ 及 fig/uestclogo.pdf。当前用户仓库已有这些依赖；字体版权归原权利人，工具本身不授予其再分发权。

在本包根目录运行 `python skills/uestc-thesis-writer/scripts/compile_thesis.py --root thesis-template --engine <xelatex路径>`；已有TeX Live 2020不覆盖。声明签字留空供本人实际签署，不生成伪造签名。专业类别按研究生系统填写，领域不存在时清空并核对上游显示行为。
