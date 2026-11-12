#!/usr/bin/env python3
"""
解析电子科技大学 DissertationUESTC LaTeX 工程为结构化 JSON AST。
支持展开 \\input / \\include，提取中英文摘要、章/节/段落、图表、公式、致谢、成果与 GB/T 7714 参考文献。
"""
import argparse
import json
import re
from pathlib import Path

CN_NUMS = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]


def strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        m = re.search(r"(?<!\\)%", line)
        lines.append(line[: m.start()] if m else line)
    return "\n".join(lines)


def expand_inputs(tex_path: Path, root: Path, seen: set[Path] | None = None) -> str:
    if seen is None:
        seen = set()
    tex_path = tex_path.resolve()
    if tex_path in seen or not tex_path.exists():
        return ""
    seen.add(tex_path)
    raw = strip_comments(tex_path.read_text(encoding="utf-8", errors="ignore"))

    def _repl(match: re.Match) -> str:
        rel = match.group(1).strip()
        cand = root / (rel if rel.endswith(".tex") else f"{rel}.tex")
        if not cand.exists():
            cand = tex_path.parent / (rel if rel.endswith(".tex") else f"{rel}.tex")
        return expand_inputs(cand, root, seen)

    return re.sub(r"\\(?:input|include)\{([^}]+)\}", _repl, raw)


def parse_bib(bib_paths: list[Path]) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for bp in bib_paths:
        if not bp.exists():
            continue
        txt = bp.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+)\s*,([\s\S]*?)\n\}", txt):
            etype, key, body = m.group(1).lower(), m.group(2).strip(), m.group(3)
            fields: dict[str, str] = {"_type": etype}
            for fm in re.finditer(r"(\w+)\s*=\s*[\{\"]([\s\S]*?)[\}\"]\s*(?:,|$)", body):
                fields[fm.group(1).lower()] = re.sub(r"\s+", " ", fm.group(2)).strip()
            entries[key] = fields
    return entries


def format_gb7714(idx: int, fields: dict[str, str]) -> str:
    etype = fields.get("_type", "article")
    author = fields.get("author", "Unknown").replace(" and ", ", ")
    title = fields.get("title", "").strip("{}")
    year = fields.get("year", "")
    pages = fields.get("pages", "").replace("--", "-")
    if etype == "article":
        journal = fields.get("journal", "")
        vol = fields.get("volume", "")
        num = fields.get("number", "")
        vol_str = f"{vol}({num})" if vol and num else vol
        tail = f": {pages}" if pages else ""
        return f"[{idx}] {author}. {title}[J]. {journal}, {year}, {vol_str}{tail}."
    if etype in ("inproceedings", "conference"):
        book = fields.get("booktitle", "")
        tail = f": {pages}" if pages else ""
        return f"[{idx}] {author}. {title}[C]. {book}, {year}{tail}."
    if etype in ("book", "monograph"):
        pub = fields.get("publisher", "")
        addr = fields.get("address", "")
        loc = f"{addr}: " if addr else ""
        return f"[{idx}] {author}. {title}[M]. {loc}{pub}, {year}."
    if etype in ("phdthesis", "mastersthesis"):
        school = fields.get("school", "")
        return f"[{idx}] {author}. {title}[D]. {school}, {year}."
    return f"[{idx}] {author}. {title}[EB/OL]. {year}."


def clean_inline_tex(text: str) -> str:
    text = re.sub(r"\\textbf\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\textit\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\emph\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_tabular(tbl_tex: str) -> list[list[str]]:
    m = re.search(r"\\begin\{tabular\}(?:\[[^\]]*\])?\{[^}]*\}([\s\S]*?)\\end\{tabular\}", tbl_tex)
    if not m:
        return []
    body = m.group(1)
    body = re.sub(r"\\(?:toprule|midrule|bottomrule|hline|cline\{[^}]*\})", "", body)
    rows = []
    for raw_row in re.split(r"\\\\", body):
        raw_row = raw_row.strip()
        if not raw_row:
            continue
        cells = [clean_inline_tex(c) for c in raw_row.split("&")]
        rows.append(cells)
    return rows


def parse_blocks(body: str, chap_idx: int, counters: dict[str, int], labels: dict[str, str], cite_order: list[str]) -> list[dict]:
    blocks: list[dict] = []
    pattern = re.compile(
        r"(\\section\*?\{[^}]+\}|\\subsection\*?\{[^}]+\}|\\subsubsection\*?\{[^}]+\}|"
        r"\\begin\{figure\}[\s\S]*?\\end\{figure\}|"
        r"\\begin\{table\}[\s\S]*?\\end\{table\}|"
        r"\\begin\{equation\}[\s\S]*?\\end\{equation\}|"
        r"\\begin\{align\}[\s\S]*?\\end\{align\}|"
        r"\\begin\{(?:itemize|enumerate)\}[\s\S]*?\\end\{(?:itemize|enumerate)\})"
    )

    def register_cites(s: str) -> None:
        for cm in re.finditer(r"\\cite[a-zA-Z]*\{([^}]+)\}", s):
            for k in cm.group(1).split(","):
                k = k.strip()
                if k and k not in cite_order:
                    cite_order.append(k)

    parts = pattern.split(body)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        register_cites(part)
        if m := re.match(r"\\section\*?\{([^}]+)\}", part):
            blocks.append({"type": "heading", "level": 2, "text": clean_inline_tex(m.group(1))})
        elif m := re.match(r"\\subsection\*?\{([^}]+)\}", part):
            blocks.append({"type": "heading", "level": 3, "text": clean_inline_tex(m.group(1))})
        elif m := re.match(r"\\subsubsection\*?\{([^}]+)\}", part):
            blocks.append({"type": "heading", "level": 4, "text": clean_inline_tex(m.group(1))})
        elif part.startswith("\\begin{figure}"):
            counters["fig"] += 1
            num = f"{chap_idx}-{counters['fig']}"
            img = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", part)
            cap = re.search(r"\\caption\{([^}]+)\}", part)
            lbl = re.search(r"\\label\{([^}]+)\}", part)
            if lbl:
                labels[lbl.group(1).strip()] = num
            blocks.append({
                "type": "figure",
                "number": num,
                "path": img.group(1).strip() if img else "",
                "caption": clean_inline_tex(cap.group(1)) if cap else "",
            })
        elif part.startswith("\\begin{table}"):
            counters["tab"] += 1
            num = f"{chap_idx}-{counters['tab']}"
            cap = re.search(r"\\caption\{([^}]+)\}", part)
            lbl = re.search(r"\\label\{([^}]+)\}", part)
            if lbl:
                labels[lbl.group(1).strip()] = num
            blocks.append({
                "type": "table",
                "number": num,
                "caption": clean_inline_tex(cap.group(1)) if cap else "",
                "rows": parse_tabular(part),
            })
        elif part.startswith("\\begin{equation}") or part.startswith("\\begin{align}"):
            counters["eq"] += 1
            num = f"({chap_idx}-{counters['eq']})"
            lbl = re.search(r"\\label\{([^}]+)\}", part)
            if lbl:
                labels[lbl.group(1).strip()] = f"{chap_idx}-{counters['eq']}"
            eq_inner = re.sub(r"\\begin\{(?:equation|align)\}|\\end\{(?:equation|align)\}|\\label\{[^}]+\}", "", part).strip()
            blocks.append({"type": "equation", "number": num, "latex": eq_inner})
        elif part.startswith("\\begin{itemize}") or part.startswith("\\begin{enumerate}"):
            items = [clean_inline_tex(x) for x in re.split(r"\\item\s*", re.sub(r"\\begin\{(?:itemize|enumerate)\}|\\end\{(?:itemize|enumerate)\}", "", part)) if x.strip()]
            blocks.append({"type": "list", "ordered": "enumerate" in part, "items": items})
        else:
            for para in re.split(r"\n\s*\n", part):
                p = clean_inline_tex(para)
                if p:
                    blocks.append({"type": "paragraph", "text": p})
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description="解析 UESTC LaTeX 工程为 JSON AST")
    parser.add_argument("--root", default="thesis-template")
    parser.add_argument("--main", default="main.tex")
    parser.add_argument("--out", default="thesis_ast.json")
    args = parser.parse_args()

    root = Path(args.root)
    full_tex = expand_inputs(root / args.main, root)

    cn_abs = re.search(r"\\begin\{chineseabstract\}([\s\S]*?)\\end\{chineseabstract\}", full_tex)
    cn_kw = re.search(r"\\chinesekeywords\{([^}]*)\}", full_tex)
    en_abs = re.search(r"\\begin\{englishabstract\}([\s\S]*?)\\end\{englishabstract\}", full_tex)
    en_kw = re.search(r"\\englishkeywords\{([^}]*)\}", full_tex)
    thanks_m = re.search(r"\\begin\{thanks\}([\s\S]*?)\\end\{thanks\}", full_tex)
    pub_m = re.search(r"\\begin\{publications\}([\s\S]*?)\\end\{publications\}", full_tex)

    doc_body_m = re.search(r"\\begin\{document\}([\s\S]*?)\\end\{document\}", full_tex)
    doc_body = doc_body_m.group(1) if doc_body_m else full_tex

    chap_splits = list(re.finditer(r"\\chapter\{([^}]+)\}", doc_body))
    chapters = []
    labels: dict[str, str] = {}
    cite_order: list[str] = []

    for i, cm in enumerate(chap_splits):
        title = clean_inline_tex(cm.group(1))
        start = cm.end()
        end = chap_splits[i + 1].start() if i + 1 < len(chap_splits) else len(doc_body)
        chunk = doc_body[start:end]
        for tail_cmd in ("\\begin{thanks}", "\\bibliography", "\\begin{publications}"):
            if tail_cmd in chunk:
                chunk = chunk[: chunk.index(tail_cmd)]
        chap_idx = i + 1
        cn_title = f"第{CN_NUMS[chap_idx] if chap_idx < len(CN_NUMS) else chap_idx}章 {title}"
        counters = {"fig": 0, "tab": 0, "eq": 0}
        blocks = parse_blocks(chunk, chap_idx, counters, labels, cite_order)
        chapters.append({"index": chap_idx, "title": title, "full_title": cn_title, "blocks": blocks})

    bib_entries = parse_bib(list(root.rglob("*.bib")))
    references = [format_gb7714(idx + 1, bib_entries.get(k, {"title": k})) for idx, k in enumerate(cite_order)]
    cite_map = {k: idx + 1 for idx, k in enumerate(cite_order)}

    publications = []
    if pub_m:
        for item in re.split(r"\\item\s*", pub_m.group(1)):
            t = clean_inline_tex(item)
            if t and not t.startswith("\\begin"):
                publications.append(t)

    ast = {
        "chinese_abstract": clean_inline_tex(cn_abs.group(1)) if cn_abs else "",
        "chinese_keywords": clean_inline_tex(cn_kw.group(1)) if cn_kw else "",
        "english_abstract": clean_inline_tex(en_abs.group(1)) if en_abs else "",
        "english_keywords": clean_inline_tex(en_kw.group(1)) if en_kw else "",
        "chapters": chapters,
        "thanks": clean_inline_tex(thanks_m.group(1)) if thanks_m else "",
        "references": references,
        "publications": publications,
        "labels": labels,
        "cite_map": cite_map,
    }

    Path(args.out).write_text(json.dumps(ast, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 解析完成：{len(chapters)} 章，{len(references)} 条参考文献 -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
