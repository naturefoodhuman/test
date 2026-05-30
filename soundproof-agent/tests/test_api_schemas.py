# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 15:18:42 CST

from __future__ import annotations

import unittest

from api.schemas import (
    DetailOnceRequest,
    FullProbeRequest,
    LiveRunRequest,
    ProbeDetailRequest,
    ReplayRunRequest,
    ReviewProbeRequest,
    SearchOnceRequest,
    SearchProbeRequest,
    SelectorBackupActionRequest,
    SelectorOverrideSaveRequest,
)


class ApiSchemasTestCase(unittest.TestCase):
    """API 请求模型测试。"""

    def test_search_once_request(self) -> None:
        payload = SearchOnceRequest(query="隔音窗 夹胶中空", limit=3)
        self.assertEqual(payload.query, "隔音窗 夹胶中空")
        self.assertEqual(payload.limit, 3)

    def test_search_probe_request(self) -> None:
        payload = SearchProbeRequest(query="隔音窗 系统窗", wait_after_load_ms=2000)
        self.assertEqual(payload.wait_after_load_ms, 2000)

    def test_detail_once_request(self) -> None:
        payload = DetailOnceRequest(title="A", detail_url="https://item.taobao.com/item.htm?id=1")
        self.assertTrue(payload.normalize_with_llm)

    def test_probe_detail_request(self) -> None:
        payload = ProbeDetailRequest(detail_url="https://item.taobao.com/item.htm?id=1", wait_after_load_ms=2000)
        self.assertEqual(payload.wait_after_load_ms, 2000)

    def test_review_probe_request(self) -> None:
        payload = ReviewProbeRequest(title="A", detail_url="https://item.taobao.com/item.htm?id=1", limit=6)
        self.assertEqual(payload.limit, 6)

    def test_full_probe_request(self) -> None:
        payload = FullProbeRequest(query="隔音窗", title="A", detail_url="https://item.taobao.com/item.htm?id=1")
        self.assertEqual(payload.review_limit, 10)

    def test_selector_requests(self) -> None:
        save = SelectorOverrideSaveRequest(content='detail:\n  title_selectors: []', backup=True)
        backup = SelectorBackupActionRequest(backup_name='selector_overrides_20250101_000000.yaml')
        self.assertTrue(save.backup)
        self.assertTrue(backup.backup_name.endswith('.yaml'))

    def test_live_run_request_to_context(self) -> None:
        payload = LiveRunRequest(scene="高架低频卧室", budget=9000)
        context = payload.to_consultation_context()
        self.assertEqual(context.scene, "高架低频卧室")
        self.assertEqual(context.budget, 9000)


if __name__ == '__main__':
    unittest.main()
