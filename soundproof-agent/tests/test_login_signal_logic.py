# 创建该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-05-30 17:15:00 CST
#
# 目的：独立验证淘宝登录态判定逻辑（不依赖 Playwright，不依赖 FakePage）。
#
# 教训（2026-05-30 第四次调试得到）：
# - dry-run 测试用 FakePage 直接返回 login_payload dict，绕过了 _extract_login_status
#   内部的 JS 判定逻辑，所以即便 JS 判定有 bug 也不会被测出来。
# - 本测试把 JS 判定规则用 Python 重新实现一份（_evaluate_login_signals_py），
#   做"规则层"单元测试。若以后改 JS 判定，必须同步改这里的 Python 镜像并重跑。
# - 严格说理想做法是用 mini DOM 库 + 把 JS 跑在 Python 里（如 dukpy/STPyV8），
#   但对当前判定逻辑的复杂度而言，"规则镜像"已经足够覆盖核心场景。

from __future__ import annotations

import re
import unittest


# ===== Python 镜像：与 playwright_executor._extract_login_status 里的 JS 等价 =====
# 修改 JS 时务必同步修改这里！

SSO_NICK_COOKIES = ["tracknick", "_nk_", "lgc", "dnk", "lid"]
SSO_TOKEN_COOKIES = ["_tb_token_", "unb", "aui", "sgcookie"]


def _evaluate_login_signals_py(cookie_str: str, body_text: str) -> dict:
    """JS 判定规则的 Python 镜像，必须与 _extract_login_status 中的 JS 保持等价。"""

    signals: list[str] = []
    has_nick = any(re.search(r"(?:^|;\s*)" + name + r"=", cookie_str) for name in SSO_NICK_COOKIES)
    if has_nick:
        signals.append("cookie_nick")
    has_token = any(re.search(r"(?:^|;\s*)" + name + r"=", cookie_str) for name in SSO_TOKEN_COOKIES)
    if has_token:
        signals.append("cookie_token")
    has_logout = "退出" in body_text
    if has_logout:
        signals.append("body_logout_text")

    has_login_hint = ("亲，请登录" in body_text) or ("请登录" in body_text)

    # 关键改进：如果页面明确提示"请登录"，则无论 Cookie 如何，都判定为未登录
    if has_login_hint:
        is_logged_in = False
        confidence = "high"
        signals.append("body_login_hint")
    else:
        # 只有在没有登录提示的情况下，才信任强信号
        has_strong = has_nick or has_token or has_logout
        if has_strong:
            is_logged_in = True
            confidence = "high"
        else:
            is_logged_in = False
            confidence = "low"

    return {
        "is_logged_in": is_logged_in,
        "confidence": confidence,
        "signals": signals,
        "has_login_hint": has_login_hint,
    }


class LoginSignalLogicTestCase(unittest.TestCase):
    """淘宝登录态判定规则的覆盖测试。"""

    def test_tracknick_alone_marks_logged_in(self) -> None:
        """仅有 tracknick 且无登录提示 也能判定为已登录。"""

        result = _evaluate_login_signals_py(
            cookie_str="cna=abc; tracknick=naturist; xlly_s=1",
            body_text="淘宝首页 我的淘宝 已买到的宝贝",
        )
        self.assertTrue(result["is_logged_in"])
        self.assertEqual(result["confidence"], "high")
        self.assertIn("cookie_nick", result["signals"])

    def test_lgc_alone_marks_logged_in(self) -> None:
        """仅有 lgc 也能判定为已登录。"""

        result = _evaluate_login_signals_py(
            cookie_str="lgc=naturist",
            body_text="淘宝首页",
        )
        self.assertTrue(result["is_logged_in"])
        self.assertIn("cookie_nick", result["signals"])

    def test_tb_token_marks_logged_in(self) -> None:
        """仅有 _tb_token_ 也能判定为已登录。"""

        result = _evaluate_login_signals_py(
            cookie_str="_tb_token_=abcdef123",
            body_text="正常",
        )
        self.assertTrue(result["is_logged_in"])
        self.assertIn("cookie_token", result["signals"])

    def test_unb_cookie_legacy_still_works(self) -> None:
        """旧版 unb cookie 仍兼容（避免淘宝改回老方案）。"""

        result = _evaluate_login_signals_py(
            cookie_str="unb=12345",
            body_text="",
        )
        self.assertTrue(result["is_logged_in"])

    def test_nk_cookie_legacy_still_works(self) -> None:
        """旧版 _nk_ cookie 仍兼容。"""

        result = _evaluate_login_signals_py(
            cookie_str="_nk_=naturist",
            body_text="",
        )
        self.assertTrue(result["is_logged_in"])

    def test_login_hint_alone_marks_not_logged_in(self) -> None:
        """只有"亲，请登录" hint 没有任何 SSO cookie → 未登录。"""

        result = _evaluate_login_signals_py(
            cookie_str="cna=abc",
            body_text="亲，请登录 免费注册",
        )
        self.assertFalse(result["is_logged_in"])
        self.assertEqual(result["confidence"], "high")
        self.assertIn("body_login_hint", result["signals"])

    def test_no_signal_at_all_returns_low_confidence(self) -> None:
        """既无强信号又无 hint（可能页面还没加载完）→ confidence=low。"""

        result = _evaluate_login_signals_py(
            cookie_str="",
            body_text="",
        )
        self.assertFalse(result["is_logged_in"])
        self.assertEqual(result["confidence"], "low")

    def test_real_world_logged_in_artifact_2026_05_30(self) -> None:
        """回归测试：验证 2026-05-30 用户实机回传的-即便有 SSO Cookie-但只要含登录 hint 就应判定为未登录。

        当时 cookie_keys 含 tracknick / lgc / dnk / aui / _tb_token_，且 body 含"亲，请登录"。
        此状态下不应判定为已登录，以防止 open_login_window 过早关闭。
        """

        cookie_str = "; ".join([
            "cna=abc",
            "tracknick=naturist",
            "lgc=naturist",
            "dnk=naturist",
            "aui=12345",
            "_tb_token_=token123",
            "xlly_s=1",
        ])
        body_text = "中国大陆 亲，请登录 免费注册 网页无障碍 切换企业版 已买到的宝贝 我的淘宝"
        result = _evaluate_login_signals_py(cookie_str=cookie_str, body_text=body_text)
        self.assertFalse(result["is_logged_in"])
        self.assertEqual(result["confidence"], "high")
        self.assertIn("body_login_hint", result["signals"])

    def test_logout_text_alone_marks_logged_in(self) -> None:
        """body 含"退出"字样也算登录（某些场景 Cookie 还没加载，但 DOM 渲染好了）。"""

        result = _evaluate_login_signals_py(
            cookie_str="cna=abc",
            body_text="我的淘宝 退出 已买到的宝贝",
        )
        self.assertTrue(result["is_logged_in"])
        self.assertIn("body_logout_text", result["signals"])


class LoginSignalLogicConsistencyTestCase(unittest.TestCase):
    """验证 Python 镜像与 JS 实现的常量定义保持一致。

    用读取 JS 源代码字符串的方式找到 ssoNickCookies / ssoTokenCookies 数组，
    与 Python 端的 SSO_NICK_COOKIES / SSO_TOKEN_COOKIES 做匹配。
    """

    def test_js_and_python_cookie_lists_match(self) -> None:
        from pathlib import Path

        source = Path(__file__).resolve().parent.parent / "src" / "shopping" / "playwright_executor.py"
        text = source.read_text(encoding="utf-8")

        # 抓 ssoNickCookies 与 ssoTokenCookies 的 JS 数组定义
        nick_match = re.search(r"ssoNickCookies\s*=\s*\[([^\]]+)\]", text)
        token_match = re.search(r"ssoTokenCookies\s*=\s*\[([^\]]+)\]", text)
        self.assertIsNotNone(nick_match, "未在 JS 中找到 ssoNickCookies 定义")
        self.assertIsNotNone(token_match, "未在 JS 中找到 ssoTokenCookies 定义")

        def _parse_js_array(raw: str) -> list[str]:
            return [piece.strip().strip("'").strip('"') for piece in raw.split(",") if piece.strip()]

        js_nick = _parse_js_array(nick_match.group(1))
        js_token = _parse_js_array(token_match.group(1))
        self.assertEqual(js_nick, SSO_NICK_COOKIES, "JS 与 Python 的 SSO_NICK_COOKIES 不一致")
        self.assertEqual(js_token, SSO_TOKEN_COOKIES, "JS 与 Python 的 SSO_TOKEN_COOKIES 不一致")


if __name__ == "__main__":
    unittest.main()
