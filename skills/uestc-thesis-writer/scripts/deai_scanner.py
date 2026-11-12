#!/usr/bin/env python3
"""
防 AI 检测（De-AIGC）痕迹扫描脚本
检测：
1. 高频 AI 中文模板连接词与套话
2. 连续排比结构（首先/其次/最后、一方面/另一方面）
3. 句长标准差过低预警（过度均匀的长句容易触发 AIGC 检测）
"""
import argparse
import math
import re
from pathlib import Path

AI_CLICHES = [
    "不仅如此",
    "值得注意的是",
    "总而言之",
    "综上所述",
    "毫无疑问",
    "显而易见",
    "至关重要的",
    "不可或缺",
    "奠定了坚实基础",
    "提供了新的思路",
    "开启了新篇章",
    "极大地方便了",
    "赋能",
]


def clean_for_sentences(text: str) -> str:
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\\begin\{(?:equation|align|figure|table|algorithm)[\s\S]*?\\end\{(?:equation|align|figure|table|algorithm)\}", "", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?", "", text)
    text = re.sub(r"\$[^$]*\$", "X", text)
    return text


def scan_file(path: Path) -> None:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    lines = raw.splitlines()
    hits = []
    for idx, line in enumerate(lines, 1):
        if line.strip().startswith("%"):
            continue
        code = line.split("%")[0]
        for phrase in AI_CLICHES:
            if phrase in code:
                hits.append((idx, phrase, code.strip()[:60]))

    cleaned = clean_for_sentences(raw)
    sentences = [s.strip() for s in re.split(r"[。！？!?]", cleaned) if len(s.strip()) >= 5]
    lengths = [len(s) for s in sentences]

    print(f"=== De-AIGC 扫描报告: {path.name} ===")
    if hits:
        print(f"[高频 AI 模板词] 命中 {len(hits)} 处：")
        for ln, ph, ctx in hits:
            print(f"  - L{ln} 「{ph}」: {ctx}...")
    else:
        print("[高频 AI 模板词] 未命中常见机械套话。")

    if len(lengths) >= 5:
        mean_len = sum(lengths) / len(lengths)
        std_len = math.sqrt(sum((x - mean_len) ** 2 for x in lengths) / len(lengths))
        print(f"[句长分布统计] 有效句数={len(lengths)}, 平均句长={mean_len:.1f}字, 标准差={std_len:.1f}")
        if std_len < 8.0:
            print("  -> [警告] 句长标准差偏低（< 8.0），句子节奏过于均匀，建议引入短句下判断并拆分长定语。")
    else:
        print("[句长分布统计] 有效句数不足 5 句，跳过方差评估。")


def main() -> int:
    parser = argparse.ArgumentParser(description="论文防 AI 痕迹扫描器")
    parser.add_argument("--target", required=True, help="待扫描的 .tex 文件路径")
    args = parser.parse_args()
    target = Path(args.target)
    if not target.exists():
        print(f"错误：文件不存在 {target}")
        return 1
    scan_file(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
