# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 01:26:58 CST

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from shopping.artifact_inspector import build_artifact_manifest
from shopping.cache_models import ShoppingRunCache
from shopping.report_builder import ShoppingReportBuilder


class ShoppingBundleExporter:
    """购物运行导出器。

    用途：
    - 把某次运行导出成一个独立目录；
    - 方便分享、复盘、handoff；
    - 保留 snapshot / report / artifact manifest / artifact 文件；
    - 可进一步打包成 zip 档案。
    """

    def __init__(self, artifact_root: str | Path) -> None:
        self.artifact_root = Path(artifact_root)
        self.report_builder = ShoppingReportBuilder()

    def build_manifest(self, run_cache: ShoppingRunCache) -> list[dict[str, Any]]:
        """构建某次运行的 artifact manifest。"""

        return build_artifact_manifest(self.artifact_root, run_cache.artifact_names)

    def export_run(self, run_cache: ShoppingRunCache, output_dir: str | Path) -> dict[str, Any]:
        """导出某次运行。"""

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        artifacts_dir = out / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        snapshot = run_cache.to_snapshot()
        report_text = self.report_builder.build_markdown(snapshot)
        manifest = build_artifact_manifest(self.artifact_root, run_cache.artifact_names)

        (out / "snapshot.json").write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
        (out / "run_cache.json").write_text(run_cache.model_dump_json(indent=2), encoding="utf-8")
        (out / "report.md").write_text(report_text, encoding="utf-8")
        (out / "artifact_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        copied_files: list[str] = []
        for item in manifest:
            name = item["name"]
            source = self.artifact_root / name
            target = artifacts_dir / name
            if source.exists() and source.is_file():
                shutil.copy2(source, target)
                copied_files.append(name)

        return {
            "output_dir": str(out),
            "copied_artifacts": copied_files,
            "artifact_count": len(copied_files),
        }

    def export_run_archive(self, run_cache: ShoppingRunCache, output_root: str | Path) -> dict[str, Any]:
        """导出某次运行并打包为 zip。"""

        output_root_path = Path(output_root)
        bundle_dir = output_root_path / run_cache.run_id
        export_result = self.export_run(run_cache, bundle_dir)
        archive_base = str(bundle_dir)
        archive_path = shutil.make_archive(archive_base, "zip", root_dir=bundle_dir)
        export_result.update(
            {
                "archive_path": archive_path,
                "archive_name": Path(archive_path).name,
            }
        )
        return export_result
