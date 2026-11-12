#!/usr/bin/env python3
"""
将 parse_uestc_tex.py 输出的 JSON AST 注入电子科大官方样式母版，生成合规 .docx。
严格执行：
- A4 页面、30mm 边距、20mm 页眉页脚
- 中文字体宋体/黑体、英数 Times New Roman、正文小四 20 磅固定行距首行缩进 2 字符
- 三线表（上下 1.5pt、表头底线 0.75pt，无竖线）
- 公式居中 + 右对齐编号（无引导线）
- 分节页码（前置罗马数字 Ⅰ 起，正文阿拉伯数字 1 起）与奇偶页眉（0.75pt 下边框）
"""
import argparse
import json
import re
from pathlib import Path

import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Mm, Pt


def set_run_font(run, cn_font: str = "宋体", en_font: str = "Times New Roman", size_pt: float = 12, bold: bool = False):
    run.font.name = en_font
    run.font.size = Pt(size_pt)
    run.bold = bold
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), en_font)
    rFonts.set(qn("w:hAnsi"), en_font)
    rFonts.set(qn("w:eastAsia"), cn_font)


def add_mixed_runs(p, text: str, cn_font="宋体", size_pt=12, bold=False, cite_map=None, labels=None):
    cite_map = cite_map or {}
    labels = labels or {}

    # Replace \ref / \eqref
    def _ref_repl(m):
        key = m.group(1).strip()
        num = labels.get(key, "??")
        return f"({num})" if m.group(0).startswith("\\eqref") else num

    text = re.sub(r"\\(?:eq)?ref\{([^}]+)\}", _ref_repl, text)

    # Split by \cite{...}
    parts = re.split(r"(\\cite[a-zA-Z]*\{[^}]+\})", text)
    for idx, part in enumerate(parts):
        if not part:
            continue
        cm = re.match(r"\\cite[a-zA-Z]*\{([^}]+)\}", part)
        if cm:
            nums = [str(cite_map.get(k.strip(), "?")) for k in cm.group(1).split(",") if k.strip()]
            cite_str = f"[{', '.join(nums)}]"
            prev = parts[idx - 1] if idx > 0 else ""
            is_inline_noun = prev.rstrip().endswith(("文献", "见", "如"))
            r = p.add_run(cite_str)
            set_run_font(r, cn_font, "Times New Roman", size_pt, bold)
            r.font.superscript = not is_inline_noun
        else:
            r = p.add_run(part)
            set_run_font(r, cn_font, "Times New Roman", size_pt, bold)


def set_page_number_format(section, fmt: str = "decimal", start: int | None = None):
    sectPr = section._sectPr
    pgNumType = sectPr.find(qn("w:pgNumType"))
    if pgNumType is None:
        pgNumType = OxmlElement("w:pgNumType")
        sectPr.append(pgNumType)
    pgNumType.set(qn("w:fmt"), fmt)
    if start is not None:
        pgNumType.set(qn("w:start"), str(start))


def add_page_field(p):
    r = p.add_run()
    set_run_font(r, "宋体", "Times New Roman", 9)
    fld1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
    instr = parse_xml(r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls("w"))
    fld2 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"))
    r._r.extend([fld1, instr, fld2])


def set_header_paragraph(header, text: str):
    header.is_linked_to_previous = False
    p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="000000"/></w:pBdr>')
    pPr.append(pBdr)
    r = p.add_run(text)
    set_run_font(r, "宋体", "Times New Roman", 10.5)


def set_footer_page_num(footer):
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_field(p)


def configure_section_margins(section):
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(30)
    section.bottom_margin = Mm(30)
    section.left_margin = Mm(30)
    section.right_margin = Mm(30)
    section.header_distance = Mm(20)
    section.footer_distance = Mm(20)


def add_body_paragraph(doc, text: str, cite_map=None, labels=None, indent: bool = True):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(20)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    if indent:
        pf.first_line_indent = Pt(24)  # 2 个小四全角字符
    add_mixed_runs(p, text, "宋体", 12, False, cite_map, labels)
    return p


def add_heading_paragraph(doc, level: int, text: str, prev_was_heading: bool = False):
    spec = {
        1: (15, WD_ALIGN_PARAGRAPH.CENTER, 24, 18),
        2: (14, WD_ALIGN_PARAGRAPH.LEFT, 18, 6),
        3: (14, WD_ALIGN_PARAGRAPH.LEFT, 12, 6),
        4: (12, WD_ALIGN_PARAGRAPH.LEFT, 12, 6),
    }
    size_pt, align, sb, sa = spec[level]
    if prev_was_heading and level > 1:
        sb = 0
    p = doc.add_paragraph(style=f"Heading {level}" if f"Heading {level}" in doc.styles else None)
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(20)
    pf.space_before = Pt(sb)
    pf.space_after = Pt(sa)
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run_font(r, "黑体", "Times New Roman", size_pt, bold=True)
    return p


def add_three_line_table(doc, rows: list[list[str]], caption: str, num: str, cite_map=None, labels=None):
    cap_text = f"表{num} {caption}"
    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER if len(cap_text) <= 34 else WD_ALIGN_PARAGRAPH.JUSTIFY
    cpf = cp.paragraph_format
    cpf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    cpf.line_spacing = Pt(20)
    cpf.space_before = Pt(12)
    cpf.space_after = Pt(6)
    cpf.keep_with_next = True
    if len(cap_text) > 34:
        cpf.left_indent = Pt(42)
        cpf.right_indent = Pt(42)
    add_mixed_runs(cp, cap_text, "宋体", 10.5, False, cite_map, labels)

    if not rows:
        return
    cols = max(len(r) for r in rows)
    tbl = doc.add_table(rows=len(rows), cols=cols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = tbl._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '<w:left w:val="none"/><w:right w:val="none"/>'
        '<w:insideH w:val="none"/><w:insideV w:val="none"/>'
        '</w:tblBorders>'
    )
    tblPr.append(borders)

    for r_idx, row in enumerate(rows):
        for c_idx in range(cols):
            cell = tbl.cell(r_idx, c_idx)
            val = row[c_idx] if c_idx < len(row) else ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            add_mixed_runs(p, val, "宋体", 10.5, bold=(r_idx == 0), cite_map=cite_map, labels=labels)
            if r_idx == 0:
                tcPr = cell._tc.get_or_add_tcPr()
                tcPr.append(parse_xml(f'<w:tcBorders {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/></w:tcBorders>'))


def add_equation_row(doc, latex: str, number: str):
    tbl = doc.add_table(rows=1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl._tbl.tblPr.append(parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="none"/><w:bottom w:val="none"/>'
        '<w:left w:val="none"/><w:right w:val="none"/>'
        '<w:insideH w:val="none"/><w:insideV w:val="none"/>'
        '</w:tblBorders>'
    ))
    widths = [Cm(2.2), Cm(10.6), Cm(2.2)]
    for i, w in enumerate(widths):
        tbl.cell(0, i).width = w
    p_mid = tbl.cell(0, 1).paragraphs[0]
    p_mid.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_mid.paragraph_format.space_before = Pt(6)
    p_mid.paragraph_format.space_after = Pt(6)
    r_mid = p_mid.add_run(latex)
    set_run_font(r_mid, "宋体", "Times New Roman", 12)

    p_num = tbl.cell(0, 2).paragraphs[0]
    p_num.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_num.paragraph_format.space_before = Pt(6)
    p_num.paragraph_format.space_after = Pt(6)
    r_num = p_num.add_run(number)
    set_run_font(r_num, "宋体", "Times New Roman", 12)


def main() -> int:
    parser = argparse.ArgumentParser(description="将 JSON AST 注入电子科大 Word 母版")
    parser.add_argument("--ast", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--root", default="thesis-template")
    parser.add_argument("--out", required=True)
    parser.add_argument("--author", default="", help="本人姓名（用于在个人成果中加粗）")
    args = parser.parse_args()

    ast = json.loads(Path(args.ast).read_text(encoding="utf-8"))
    doc = docx.Document(args.template)
    doc.settings.odd_and_even_pages_header_footer = True
    configure_section_margins(doc.sections[0])

    cite_map = ast.get("cite_map", {})
    labels = ast.get("labels", {})
    tex_root = Path(args.root)

    # 中文摘要分节（罗马页码 Ⅰ）
    sec_abs = doc.add_section(WD_SECTION.NEW_PAGE)
    configure_section_margins(sec_abs)
    set_page_number_format(sec_abs, "upperRoman", 1)
    set_header_paragraph(sec_abs.header, "摘　要")
    set_header_paragraph(sec_abs.even_page_header, "摘　要")
    set_footer_page_num(sec_abs.footer)
    set_footer_page_num(sec_abs.even_page_footer)

    add_heading_paragraph(doc, 1, "摘　要")
    if ast.get("chinese_abstract"):
        for para in ast["chinese_abstract"].split("\n"):
            if para.strip():
                add_body_paragraph(doc, para.strip())
    if ast.get("chinese_keywords"):
        p = add_body_paragraph(doc, "", indent=False)
        r1 = p.add_run("关键词：")
        set_run_font(r1, "黑体", "Times New Roman", 12, True)
        r2 = p.add_run(ast["chinese_keywords"])
        set_run_font(r2, "宋体", "Times New Roman", 12)

    # 英文摘要分节
    sec_en = doc.add_section(WD_SECTION.NEW_PAGE)
    configure_section_margins(sec_en)
    set_header_paragraph(sec_en.header, "ABSTRACT")
    set_header_paragraph(sec_en.even_page_header, "ABSTRACT")
    set_footer_page_num(sec_en.footer)
    set_footer_page_num(sec_en.even_page_footer)

    add_heading_paragraph(doc, 1, "ABSTRACT")
    if ast.get("english_abstract"):
        for para in ast["english_abstract"].split("\n"):
            if para.strip():
                add_body_paragraph(doc, para.strip())
    if ast.get("english_keywords"):
        p = add_body_paragraph(doc, "", indent=False)
        r1 = p.add_run("Keywords: ")
        set_run_font(r1, "宋体", "Times New Roman", 12, True)
        r2 = p.add_run(ast["english_keywords"])
        set_run_font(r2, "宋体", "Times New Roman", 12)

    # 主体各章（阿拉伯数字页码 1 起，奇偶页眉）
    for idx, ch in enumerate(ast.get("chapters", [])):
        sec_ch = doc.add_section(WD_SECTION.NEW_PAGE)
        configure_section_margins(sec_ch)
        if idx == 0:
            set_page_number_format(sec_ch, "decimal", 1)
        set_header_paragraph(sec_ch.header, ch["full_title"])
        set_header_paragraph(sec_ch.even_page_header, "电子科技大学硕士学位论文")
        set_footer_page_num(sec_ch.footer)
        set_footer_page_num(sec_ch.even_page_footer)

        add_heading_paragraph(doc, 1, ch["full_title"])
        prev_is_heading = True
        for blk in ch.get("blocks", []):
            btype = blk["type"]
            if btype == "heading":
                add_heading_paragraph(doc, blk["level"], blk["text"], prev_was_heading=prev_is_heading)
                prev_is_heading = True
            elif btype == "paragraph":
                is_eq_desc = blk["text"].startswith("式中")
                add_body_paragraph(doc, blk["text"], cite_map, labels, indent=not is_eq_desc)
                prev_is_heading = False
            elif btype == "list":
                for item_i, item_txt in enumerate(blk.get("items", []), 1):
                    prefix = f"({item_i}) " if blk.get("ordered") else "• "
                    add_body_paragraph(doc, prefix + item_txt, cite_map, labels)
                prev_is_heading = False
            elif btype == "figure":
                fp = tex_root / blk.get("path", "")
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(6)
                p_img.paragraph_format.keep_with_next = True
                if blk.get("path") and fp.exists() and fp.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    p_img.add_run().add_picture(str(fp), width=Mm(130))
                else:
                    r_ph = p_img.add_run(f"[插图占位: {blk.get('path', '')}]")
                    set_run_font(r_ph, "宋体", "Times New Roman", 10.5)
                cap_text = f"图{blk['number']} {blk['caption']}"
                cp = doc.add_paragraph()
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER if len(cap_text) <= 34 else WD_ALIGN_PARAGRAPH.JUSTIFY
                cpf = cp.paragraph_format
                cpf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
                cpf.line_spacing = Pt(20)
                cpf.space_before = Pt(6)
                cpf.space_after = Pt(12)
                if len(cap_text) > 34:
                    cpf.left_indent = Pt(42)
                    cpf.right_indent = Pt(42)
                add_mixed_runs(cp, cap_text, "宋体", 10.5, False, cite_map, labels)
                prev_is_heading = False
            elif btype == "table":
                add_three_line_table(doc, blk.get("rows", []), blk["caption"], blk["number"], cite_map, labels)
                prev_is_heading = False
            elif btype == "equation":
                add_equation_row(doc, blk["latex"], blk["number"])
                prev_is_heading = False

    # 致谢、参考文献、成果
    for title, items, style_size in [
        ("致　谢", [ast.get("thanks", "")], 12),
        ("参考文献", ast.get("references", []), 10.5),
        ("攻读硕士学位期间取得的成果", ast.get("publications", []), 10.5),
    ]:
        if not any(items):
            continue
        sec_tail = doc.add_section(WD_SECTION.NEW_PAGE)
        configure_section_margins(sec_tail)
        set_header_paragraph(sec_tail.header, title)
        set_header_paragraph(sec_tail.even_page_header, "电子科技大学硕士学位论文")
        set_footer_page_num(sec_tail.footer)
        set_footer_page_num(sec_tail.even_page_footer)
        add_heading_paragraph(doc, 1, title)
        for line in items:
            if not line.strip():
                continue
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            pf = p.paragraph_format
            pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            pf.line_spacing = Pt(20)
            if title == "参考文献":
                pf.left_indent = Pt(21)
                pf.first_line_indent = Pt(-21)
            elif title == "致　谢":
                pf.first_line_indent = Pt(24)
            if title == "攻读硕士学位期间取得的成果" and args.author and args.author in line:
                for seg in re.split(f"({re.escape(args.author)})", line):
                    if seg:
                        r = p.add_run(seg)
                        set_run_font(r, "宋体", "Times New Roman", style_size, bold=(seg == args.author))
            else:
                r = p.add_run(line)
                set_run_font(r, "宋体", "Times New Roman", style_size)

    doc.save(args.out)
    print(f"[OK] 已生成电子科大合规 Word 文档: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
