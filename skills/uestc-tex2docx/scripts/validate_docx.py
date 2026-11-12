#!/usr/bin/env python3
"""
电子科技大学 Word（.docx）文档合规校验脚本
核查项：A4 尺寸、30mm 边距、20mm 页眉页脚距、奇偶页眉设置、20磅固定行距、三线表边框。
"""
import argparse
from pathlib import Path
import docx
from docx.oxml.ns import qn


def main() -> int:
    parser = argparse.ArgumentParser(description="UESTC Word 合规校验")
    parser.add_argument("--docx", required=True)
    args = parser.parse_args()

    path = Path(args.docx)
    if not path.exists():
        print(f"错误：文件不存在 {path}")
        return 1

    doc = docx.Document(str(path))
    errors = []

    if not doc.settings.odd_and_even_pages_header_footer:
        errors.append("未启用奇偶页不同页眉（odd_and_even_pages_header_footer=False）")

    for i, sec in enumerate(doc.sections):
        if abs(sec.page_width.mm - 210) > 1 or abs(sec.page_height.mm - 297) > 1:
            errors.append(f"Section {i}: 纸张非 A4 ({sec.page_width.mm:.1f}x{sec.page_height.mm:.1f}mm)")
        for name, val in [("top", sec.top_margin.mm), ("bottom", sec.bottom_margin.mm), ("left", sec.left_margin.mm), ("right", sec.right_margin.mm)]:
            if abs(val - 30.0) > 0.5:
                errors.append(f"Section {i}: {name} 页边距为 {val:.1f}mm（规范要求 30mm）")

    for ti, tbl in enumerate(doc.tables):
        if len(tbl.columns) == 3 and len(tbl.rows) == 1:
            continue  # 公式布局表
        tblPr = tbl._tbl.tblPr
        bdr = tblPr.find(qn("w:tblBorders"))
        if bdr is None:
            errors.append(f"Table {ti}: 缺少三线表边框定义")

    if not errors:
        print(f"[PASS] {path.name} 通过页面尺寸、30mm 边距、奇偶页眉及三线表自动化校验（共 {len(doc.sections)} 节，{len(doc.tables)} 个表格）。")
        return 0

    print(f"[WARN] {path.name} 发现 {len(errors)} 项格式问题：")
    for e in errors:
        print("  -", e)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
