# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-30 13:45:00 CST
"""
实机测试期补丁打包脚本（ADR-013）。

用法：
    python3 scripts/make_patch.py --desc 修复列表页选择器
    python3 scripts/make_patch.py --files docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md src/shopping/selector_profiles.py --desc 升级
    python3 scripts/make_patch.py --since-commit HEAD~1 --desc 上一commit以来全部改动
    python3 scripts/make_patch.py --auto --desc 自动检测git改动

行为：
1. 收集要打包的相对路径列表：
   - 优先使用 --files
   - 否则使用 --auto：通过 git status / git diff 自动收集（modified + untracked，排除黑名单）
   - --since-commit 用 git diff 列出该 commit 到 HEAD 的改动
2. 排除目录：runtime/、__pycache__/、.git/、patches/、.venv/、node_modules/、.pytest_cache/、.mypy_cache/、phase0_outputs/
3. 排除文件：*.pyc, .DS_Store
4. 生成 zip：patches/patch_<YYYYMMDD_HHMMSS>_<safe_desc>.zip
   - zip 内目录从 "soundproof-agent/" 开始，便于用户直接覆盖到
     /Users/naturist/MusicProject/Shopping-Agent/soundproof-agent/
5. 附 PATCH_NOTES.md（zip 内根目录），包括：
   - 时间戳、描述、文件清单、应用方法、回滚方法
6. 在终端输出：zip 路径、文件数、字节数、应用提示。

示例（覆盖到 Mac）：
    cd /Users/naturist/MusicProject/Shopping-Agent
    unzip -o /path/to/patch_xxx.zip
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Iterable, List, Set

# 工程根（脚本所在目录的父级），相对路径都以此为基准。
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # soundproof-agent/
PATCHES_DIR = PROJECT_ROOT.parent / "patches"  # /home/user/test/patches/
ZIP_INNER_PREFIX = "soundproof-agent"  # zip 内目录前缀

EXCLUDE_DIRS = {
    "runtime", "__pycache__", ".git", "patches", ".venv", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build",
    "phase0_outputs",
}
EXCLUDE_FILE_SUFFIXES = {".pyc"}
EXCLUDE_FILE_NAMES = {".DS_Store"}

DEFAULT_TARGET_PATH = "/Users/naturist/MusicProject/Shopping-Agent/soundproof-agent"


def _now_stamp() -> str:
    """北京时间时间戳。"""
    cst = _dt.timezone(_dt.timedelta(hours=8))
    return _dt.datetime.now(cst).strftime("%Y%m%d_%H%M%S")


def _safe_desc(desc: str) -> str:
    """把描述文本转成文件名安全形式。"""
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", desc.strip())
    return s[:40] or "patch"


def _is_excluded(rel_path: Path) -> bool:
    parts = rel_path.parts
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    if rel_path.name in EXCLUDE_FILE_NAMES:
        return True
    if rel_path.suffix in EXCLUDE_FILE_SUFFIXES:
        return True
    return False


def _git(args: List[str]) -> str:
    """在仓库根（PROJECT_ROOT.parent）执行 git 命令，返回 stdout 文本。"""
    repo_root = PROJECT_ROOT.parent
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(f"[git 错误] git {' '.join(args)}\n{result.stderr}\n")
        return ""
    return result.stdout


def _auto_collect_via_git() -> List[Path]:
    """通过 git status 自动收集 modified + untracked 文件（相对于 soundproof-agent/）。"""
    repo_root = PROJECT_ROOT.parent
    out = _git(["status", "--porcelain", "-z"])
    if not out:
        return []
    files: List[Path] = []
    # -z 模式下用 \0 分隔；处理 rename 时格式是 "R xx -> yy"，但 -z 用 \0 分隔旧新
    raw_entries = out.split("\0")
    i = 0
    while i < len(raw_entries):
        entry = raw_entries[i]
        if not entry:
            i += 1
            continue
        status = entry[:2]
        path_str = entry[3:]
        # 重命名：下一个 \0 段是旧路径，跳过它
        if status[0] == "R":
            i += 2
        else:
            i += 1
        abs_path = (repo_root / path_str).resolve()
        # 仅收集 soundproof-agent/ 内文件
        try:
            rel_to_project = abs_path.relative_to(PROJECT_ROOT)
        except ValueError:
            continue
        if not abs_path.is_file():
            continue
        if _is_excluded(rel_to_project):
            continue
        files.append(rel_to_project)
    return files


def _collect_via_since_commit(since: str) -> List[Path]:
    repo_root = PROJECT_ROOT.parent
    out = _git(["diff", "--name-only", "-z", f"{since}..HEAD"])
    if not out:
        out = _git(["diff", "--name-only", "-z", since])
    if not out:
        return []
    files: List[Path] = []
    for path_str in out.split("\0"):
        if not path_str:
            continue
        abs_path = (repo_root / path_str).resolve()
        try:
            rel_to_project = abs_path.relative_to(PROJECT_ROOT)
        except ValueError:
            continue
        if not abs_path.is_file():
            continue
        if _is_excluded(rel_to_project):
            continue
        files.append(rel_to_project)
    return files


def _collect_explicit(file_args: List[str]) -> List[Path]:
    files: List[Path] = []
    for f in file_args:
        p = Path(f)
        if not p.is_absolute():
            # 优先尝试以 PROJECT_ROOT 为基准
            candidate = (PROJECT_ROOT / p).resolve()
            if not candidate.exists():
                # 再尝试当前工作目录
                candidate = (Path.cwd() / p).resolve()
            p = candidate
        else:
            p = p.resolve()
        if not p.exists():
            sys.stderr.write(f"[警告] 找不到文件：{f}\n")
            continue
        if not p.is_file():
            sys.stderr.write(f"[警告] 跳过非文件：{f}\n")
            continue
        try:
            rel = p.relative_to(PROJECT_ROOT)
        except ValueError:
            sys.stderr.write(f"[警告] 文件不在 soundproof-agent/ 下，跳过：{f}\n")
            continue
        if _is_excluded(rel):
            sys.stderr.write(f"[警告] 文件在排除列表，跳过：{rel}\n")
            continue
        files.append(rel)
    return files


def _build_notes(files: List[Path], desc: str, stamp: str) -> str:
    cst = _dt.timezone(_dt.timedelta(hours=8))
    now_str = _dt.datetime.now(cst).strftime("%Y-%m-%d %H:%M:%S CST")
    lines = [
        "<!--",
        "创建该文件的LLM大模型名称：Arena.ai Agent Mode",
        f"创建时间（北京时间，精确到秒）：{now_str}",
        "-->",
        "",
        f"# 补丁说明 patch_{stamp}",
        "",
        f"- **时间**：{now_str}",
        f"- **描述**：{desc}",
        f"- **包含文件数**：{len(files)}",
        f"- **目标覆盖路径**：`{DEFAULT_TARGET_PATH}`",
        "",
        "## 应用方法",
        "",
        "在 Mac 上执行：",
        "",
        "```bash",
        f"cd {Path(DEFAULT_TARGET_PATH).parent}",
        f"unzip -o /path/to/patch_{stamp}_*.zip",
        "```",
        "",
        "或解压后手动覆盖。zip 内目录从 `soundproof-agent/` 开始。",
        "",
        "## 应用前置条件",
        "",
        "- 如本补丁修改了 `pyproject.toml`，请重新 `uv sync`。",
        "- 如本补丁修改了 `tests/`，请重新跑 `PYTHONPATH=src python3 -m unittest discover -s tests -v`。",
        "- 如本补丁修改了 `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md`，对应 docx 应该已在 Agent 端同步过。",
        "",
        "## 回滚方法",
        "",
        "项目使用 git 管理，回滚直接：",
        "",
        "```bash",
        f"cd {DEFAULT_TARGET_PATH}",
        "git diff   # 查看本补丁带来的差异",
        "git restore <受影响的文件路径>",
        "```",
        "",
        "## 包含的文件清单",
        "",
    ]
    for f in sorted(files):
        lines.append(f"- `{f.as_posix()}`")
    lines.append("")
    return "\n".join(lines)


def make_patch(files: List[Path], desc: str) -> Path:
    PATCHES_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _now_stamp()
    safe = _safe_desc(desc)
    zip_path = PATCHES_DIR / f"patch_{stamp}_{safe}.zip"

    notes = _build_notes(files, desc, stamp)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 写入 PATCH_NOTES.md 在 zip 根目录
        zf.writestr("PATCH_NOTES.md", notes)
        for rel in files:
            abs_path = PROJECT_ROOT / rel
            arcname = f"{ZIP_INNER_PREFIX}/{rel.as_posix()}"
            zf.write(str(abs_path), arcname)

    return zip_path


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="实机测试期 zip 补丁打包（ADR-013）")
    parser.add_argument("--desc", required=True, help="本补丁的简短描述（中英文均可）")
    src_group = parser.add_mutually_exclusive_group()
    src_group.add_argument(
        "--auto", action="store_true",
        help="通过 git status 自动收集 modified + untracked 文件",
    )
    src_group.add_argument(
        "--since-commit", default=None,
        help="收集 <commit>..HEAD 的所有改动文件（默认相对于 PROJECT 根）",
    )
    src_group.add_argument(
        "--files", nargs="+", default=None,
        help="手工指定要打包的文件路径列表（相对 soundproof-agent/ 或绝对）",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只列出会打包的文件，不实际写 zip",
    )
    args = parser.parse_args(argv)

    if args.files:
        files = _collect_explicit(args.files)
    elif args.since_commit:
        files = _collect_via_since_commit(args.since_commit)
    else:
        # 默认 --auto
        files = _auto_collect_via_git()

    if not files:
        sys.stderr.write("[错误] 没有要打包的文件。\n")
        return 1

    # 去重并排序
    seen: Set[Path] = set()
    unique_files: List[Path] = []
    for f in files:
        if f in seen:
            continue
        seen.add(f)
        unique_files.append(f)
    unique_files.sort()

    print(f"将打包 {len(unique_files)} 个文件：")
    for f in unique_files:
        print(f"  - {f.as_posix()}")

    if args.dry_run:
        print("\n[dry-run] 未实际写 zip。")
        return 0

    zip_path = make_patch(unique_files, args.desc)
    size_kb = zip_path.stat().st_size / 1024

    print(f"\n[OK] 已生成补丁：{zip_path}")
    print(f"     文件数 {len(unique_files)}，大小 {size_kb:.1f} KB")
    print(f"\n用户在 Mac 上应用：")
    print(f"  cd {Path(DEFAULT_TARGET_PATH).parent}")
    print(f"  unzip -o {zip_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
