# 第三方来源与许可

本包不是把所有上游重新标成 MIT 的合并项目。自主编写的适配说明和脚本与原样保留的第三方文件分开处理；学校文本、校徽、字体及上游文件保留其权利归属。仓库已有根 LICENSE 不能覆盖这些第三方材料。

- Digital-Mentor、codex-claude-academic-skills、master-thesis-studio-skill：上游 MIT。这里参考其组织与规则，自主编写中文适配，没有复制整个技能库。
- academic-writing-skills：上游 **PolyForm Noncommercial 1.0.0**，不是 MIT。以个人非商业学位论文为使用场景；若复用该项目代码或文字，需遵守其许可，不能把这些内容作为无条件商业可用资源。
- paper-write 所在 best-skills：Apache-2.0。参考其方法，不直接分发整个技能文件。
- DissertationUESTC：保留原样 DissertUESTC.cls / DissertUESTC.bst 和上游作者说明；上游 README 标明 LPPL。字体具有各自许可，不能从模板源码许可推定字体可自由再发布。本分支沿用目标仓库已存在的字体与校徽，不新增系统字体上传。
- `skills/uestc-tex2docx/assets/gb7714-2015.csl` 来源 [citation-style-language/styles](https://github.com/citation-style-language/styles/blob/master/china-national-standard-gb-t-7714-2015-numeric.csl)，保留文件内作者和 CC BY-SA 3.0 声明。修改：作者姓氏 text-case 从 uppercase 改为 capitalize-first，以适配学校示例；需继续核对机构作者与特殊姓名。该衍生 CSL 继续遵守 CC BY-SA 3.0。
- Python、Pandoc、python-docx、docxcompose、PyMuPDF 和其他依赖按各自许可使用，本包不将其二进制重许可或打包。

完整上游链接及版本见 docs/SOURCES.md。使用者应在分发包含字体、学校表格或第三方改写文本的衍生包前核对相应原始许可。
