# 输入和迁移

Python 3.10+；Pandoc 3.4+；依赖见 Skill 内 requirements.txt。实际回归环境记录于项目 validation/REPORT.md。需要中文字体和 Times New Roman。排版检查需要 Word 或 LibreOffice。

工程结构使用 `main.tex`、`metadata.tex`、`macros.tex`、`.bib` 和原始插图，沿用本项目 thesis-template。公式宏放 macros.tex，避免依赖 class 私有实现。章节路径相对主项目根目录；每个 include 文件纳入哈希清单，循环引用和缺文件报错。

旧工程迁移：先完整备份；识别主入口和实际使用的章节；把封面参数移至 metadata.tex；保持 cite/label 不变；先单章含公式图表样本，再全文。不要以正则批量删除未知命令。条件编译和 includeonly 需提供明确的独立导出入口，脚本不猜分支。

元数据字段与 template/metadata.tex 相同。DegreeCategory 为实际专业学位类别，DegreeField 为领域，二者不能混用；领域不适用时留空。英文扉页是校规所需，不表示正文改为英文。真实姓名、日期、分类号、UDC、评阅人只能据作者资料填写。没有确定信息保留待填，禁止填入师兄资料。

--cover 指向官方专业硕士封面 DOCX；--spec 指向含学校声明页的规范 DOCX。固定页面必须对照用户版本复核，脚本以当前提供版本为基准，学校更新模板后不能未经核对沿用替换规则。声明签名留空，不自动签名。

--out 旁生成 `<文件名>-conversion`，包含 normalized.tex、semantic.json、Pandoc 中间 DOCX、报告。它们可能含未发表论文内容，不应自动提交公共仓库。
