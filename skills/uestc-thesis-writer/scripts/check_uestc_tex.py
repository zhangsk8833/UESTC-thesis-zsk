#!/usr/bin/env python3
"""
电子科技大学（UESTC）专业硕士学位论文 LaTeX 工程静态合规核查脚本
检查项目：
1. 导师/校规禁用词与第一人称复数（“我们”“笔者”“首次”“填补空白”等）
2. 英文摘要禁用 "This paper"（应为 "This thesis"）
3. 中文摘要与致谢字数上限（≤ 800 字）
4. 核心研究章末尾是否包含“本章小结”
5. \\cite{} 与 \\ref{} / \\label{} 基本配对核查
"""
import argparse
import re
from pathlib import Path

FORBIDDEN_TERMS = [
    ("我们", "禁用非唯一作者人称，改为“本文”“本节”或客观主语"),
    ("笔者", "禁用“笔者”，改为“本文”"),
    ("显著提升", "导师偏好：避免空洞夸张词，请替换为具体量化数值对比"),
    ("极大增强", "导师偏好：避免夸张副词，请替换为具体指标增益"),
    ("革命性", "导师偏好：禁用夸张形容词"),
    ("颠覆性", "导师偏好：禁用夸张形容词"),
    ("填补空白", "校规：无充分证据禁用“填补空白”"),
    ("国际领先", "校规：无充分证据禁用“领先”"),
    ("首次提出", "校规：无充分证据禁用“首次”"),
    ("完美解决", "导师偏好：避免绝对化结论"),
]


def strip_tex_commands(text: str) -> str:
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?", "", text)
    text = re.sub(r"[{}$\\]", "", text)
    return re.sub(r"\s+", "", text)


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    name = path.name

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("%"):
            continue
        code_part = line.split("%")[0]
        for term, reason in FORBIDDEN_TERMS:
            if term in code_part:
                issues.append(f"[{name}:L{idx}] 禁用/高风险词「{term}」 -> {reason}")
        if "abstract" in name.lower() and re.search(r"\bthis\s+paper\b", code_part, re.I):
            issues.append(f"[{name}:L{idx}] 英文摘要禁止使用 'This paper'，请改为 'This thesis'")

    if "abstract" in name.lower():
        m = re.search(r"\\begin\{chineseabstract\}(.*?)\\end\{chineseabstract\}", content, re.S)
        if m:
            cn_len = len(strip_tex_commands(m.group(1)))
            if cn_len > 800:
                issues.append(f"[{name}] 中文摘要约 {cn_len} 字，超过校规一般上限（800 字）")

    if "acknowledgement" in name.lower():
        m = re.search(r"\\begin\{thanks\}(.*?)\\end\{thanks\}", content, re.S)
        body = m.group(1) if m else content
        ack_len = len(strip_tex_commands(body))
        if ack_len > 800:
            issues.append(f"[{name}] 致谢约 {ack_len} 字，超过校规一般上限（800 字）")

    if re.match(r"chap0[2-4]", name):
        if "本章小结" not in content:
            issues.append(f"[{name}] 校规要求中间各章末尾必须包含“本章小结”")

    return issues


def check_refs_and_cites(tex_files: list[Path], bib_files: list[Path]) -> list[str]:
    issues: list[str] = []
    all_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in tex_files)
    labels = set(re.findall(r"\\label\{([^}]+)\}", all_text))
    refs = set(re.findall(r"\\(?:eq)?ref\{([^}]+)\}", all_text))
    missing_labels = sorted(refs - labels)
    for lbl in missing_labels:
        issues.append(f"[交叉引用] 引用了未定义的标签 \\ref{{{lbl}}}")

    cites_raw = re.findall(r"\\cite[a-zA-Z]*\{([^}]+)\}", all_text)
    cited_keys = {k.strip() for group in cites_raw for k in group.split(",") if k.strip()}

    bib_keys: set[str] = set()
    for bf in bib_files:
        btxt = bf.read_text(encoding="utf-8", errors="ignore")
        bib_keys.update(re.findall(r"@\w+\{([^,]+),", btxt))

    if bib_keys:
        for ck in sorted(cited_keys - bib_keys):
            issues.append(f"[参考文献] 正文引用 \\cite{{{ck}}} 在 .bib 中未找到")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="UESTC 学位论文 LaTeX 校规静态核查")
    parser.add_argument("--root", default="thesis-template", help="LaTeX 工程根目录")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"错误：目录不存在 {root}")
        return 1

    tex_files = sorted(root.rglob("*.tex"))
    bib_files = sorted(root.rglob("*.bib"))

    all_issues: list[str] = []
    for tf in tex_files:
        all_issues.extend(check_file(tf))
    all_issues.extend(check_refs_and_cites(tex_files, bib_files))

    if not all_issues:
        print(f"[PASS] 共扫描 {len(tex_files)} 个 .tex 文件，未发现校规与禁用词违规项。")
        return 0

    print(f"[WARN] 共发现 {len(all_issues)} 项待处理问题：")
    for item in all_issues:
        print("  -", item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
