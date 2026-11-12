#!/usr/bin/env python3
"""
电子科技大学 LaTeX 学位论文四步编译脚本（XeLaTeX + BibTeX + Makeglossaries）
适配本地 TeXLive 2024+ 环境，失败时提取第一条关键报错。
"""
import argparse
import shutil
import subprocess
from pathlib import Path


def run_step(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=180)
    return proc.returncode, proc.stdout + "\n" + proc.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description="UESTC LaTeX 四步编译助手")
    parser.add_argument("--root", default="thesis-template", help="LaTeX 工程根目录")
    parser.add_argument("--main", default="main", help="主文件名（不含 .tex）")
    args = parser.parse_args()

    root = Path(args.root)
    if not shutil.which("xelatex"):
        print("未检测到 xelatex。请在本地安装 TeXLive 2024+ 或上传至 Overleaf（设置编译器为 XeLaTeX + TeXLive 2024）编译。")
        return 1

    steps = [
        ["xelatex", "-interaction=nonstopmode", "-file-line-error", f"{args.main}.tex"],
        ["bibtex", args.main],
        ["makeglossaries", args.main],
        ["xelatex", "-interaction=nonstopmode", "-file-line-error", f"{args.main}.tex"],
        ["xelatex", "-interaction=nonstopmode", "-file-line-error", f"{args.main}.tex"],
    ]

    for step in steps:
        if step[0] == "makeglossaries" and not shutil.which("makeglossaries"):
            print("[跳过] 未找到 makeglossaries，跳过缩略词表索引生成。")
            continue
        print(f"[执行] {' '.join(step)}")
        rc, out = run_step(step, root)
        if rc != 0:
            print(f"[失败] 命令 {' '.join(step)} 返回码 {rc}")
            for line in out.splitlines():
                if line.startswith("!") or ": error:" in line or ".tex:" in line:
                    print("  >", line)
            return rc

    print(f"[成功] 已生成 {root / (args.main + '.pdf')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
