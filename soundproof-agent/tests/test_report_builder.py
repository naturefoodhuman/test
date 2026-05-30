# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 02:58:44 CST

from __future__ import annotations

import unittest

from shopping.report_builder import ShoppingReportBuilder
from shopping.schemas import ProductComparisonSummary, ProductDetail, RejectedListingProduct, ShoppingSearchIntent, ShoppingSessionSnapshot, WorkflowStepTrace


class ShoppingReportBuilderTestCase(unittest.TestCase):
    """Markdown 报告生成测试。"""

    def test_build_markdown(self) -> None:
        builder = ShoppingReportBuilder()
        snapshot = ShoppingSessionSnapshot(
            run_id="run_001",
            search_intent=ShoppingSearchIntent(
                scene="高架低频卧室",
                budget_level="medium",
                solution_type="replace_window",
                primary_keywords=["隔音窗", "夹胶中空"],
            ),
            search_query="隔音窗 夹胶中空 系统窗",
            detailed_products=[
                ProductDetail(
                    title="70系统平开窗 5+5夹胶+20A+5中空",
                    price_text="718元/㎡",
                    shop_name="XX门窗旗舰店",
                    glass_spec="5+5夹胶+20A+5中空玻璃",
                    frame_spec="70系统平开窗",
                    seal_spec="三道密封",
                    ranking_score=3.2,
                    ranking_reasons=["低频场景下夹胶结构加分"],
                )
            ],
            filtered_out_products=[RejectedListingProduct(title="密封条", reason="命中配件关键词")],
            comparison_summary=ProductComparisonSummary(
                recommended_option="70系统平开窗 5+5夹胶+20A+5中空",
                reason_summary="低频场景与性价比平衡较好。",
                risk_points=["需确认安装工艺"],
                search_refinement=["继续筛选三道密封与夹胶配置"],
            ),
            workflow_notes=["搜索频率正常"],
            artifact_names=["run_001_taobao_search_x.json"],
            step_traces=[WorkflowStepTrace(step="search_listings", duration_ms=123, notes=["候选数：2"])],
        )

        markdown = builder.build_markdown(snapshot)
        self.assertIn("# 购物决策报告", markdown)
        self.assertIn("运行 ID：run_001", markdown)
        self.assertIn("工作流备注", markdown)
        self.assertIn("步骤轨迹", markdown)
        self.assertIn("需确认安装工艺", markdown)
        self.assertIn("被过滤候选", markdown)
        self.assertIn("密封条", markdown)


if __name__ == "__main__":
    unittest.main()
