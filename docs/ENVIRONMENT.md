# 依赖与复现

本次验证环境：Windows、Python 3.12、Pandoc 3.4、TeX Live 2026 的 XeLaTeX/BibTeX、Microsoft Word COM；python-docx 1.2.0、docxcompose 2.2.0、PyMuPDF 1.26.6、lxml 6.1.1、PyYAML 6.0.3、Pillow 13.0.0。其他版本按依赖范围安装后仍需重新验证版式。

TeX Live 建议完整安装或使用2024及以上发行版。精简安装需要 ctex、xeCJK、layouts、titlesec、tocloft、notoccite、nomencl、algorithm2e、xunicode、xpatch、koma-script、footmisc、bigfoot、threeparttable、appendix、textpos、xstring、zref、mhchem、chemfig、datetime、boxedminipage、pdfpages、makecell、multirow、floatrow、glossaries、l3experimental、accsupp、ifoddpage、relsize、extarrows、mathspec、xint 及其依赖。以实际 missing .sty 日志补包，不把下载成功等同于编译成功。

本机原 TeX Live 2020 保留；本次使用独立工具路径编译，未修改系统 PATH。便携运行时较大，未放入仓库。以后用 compile_thesis.py 的 --engine 显式指定可用版本。

回归：`python -m unittest discover -s tests -v`。Pandoc 不在 PATH 时设置环境变量 PANDOC 指向其可执行文件。Word 更新域与 PDF 导出：`powershell -File skills/uestc-tex2docx/scripts/render_word.ps1 -InputDoc <docx> -Pdf <pdf> -Refresh`；更新后的 Word 为 `*-updated.docx`。

两个 Skill 目录可独立复制到 Codex skills 目录。转换 Skill 的 requirements.txt 独立列出运行依赖；学校 DOCX 输入仍需由作者提供。
