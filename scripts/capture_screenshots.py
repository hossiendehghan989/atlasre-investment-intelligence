"""Capture reproducible, 1440-pixel-wide dashboard evidence from a running Streamlit app."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8501"
OUTPUT = ROOT / "docs" / "images"
OUTPUT.mkdir(parents=True, exist_ok=True)


def wait_for_idle(page) -> None:
    """Allow Streamlit's run-status indicator to disappear before taking evidence."""
    page.wait_for_timeout(3_000)


def capture() -> None:
    """Capture the default illustrative dashboard and its generated working files."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path="/usr/bin/chromium",
            args=["--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1200}, device_scale_factor=1)
        page.goto(BASE_URL, wait_until="networkidle", timeout=60_000)
        page.get_by_role("heading", name="Downside first").wait_for(timeout=60_000)
        wait_for_idle(page)
        page.screenshot(path=OUTPUT / "decision-summary.png", full_page=False)

        risk_detail = page.get_by_text("Risk tail detail")
        risk_detail.click()
        risk_detail.scroll_into_view_if_needed()
        wait_for_idle(page)
        page.screenshot(path=OUTPUT / "downside-risk.png", full_page=False)

        package_heading = page.get_by_text("Working files")
        package_heading.scroll_into_view_if_needed()
        page.get_by_role("button", name="Prepare review files").click()
        page.get_by_text("Review files ready").wait_for(timeout=60_000)
        wait_for_idle(page)
        page.screenshot(path=OUTPUT / "review-package.png", full_page=False)

        preview = page.get_by_text("Preview review memo")
        preview.click()
        memo_title = page.get_by_role("heading", name="Investment Committee Screening Memo — Core-plus screening case")
        memo_title.evaluate("element => element.scrollIntoView({block: 'start'})")
        wait_for_idle(page)
        page.screenshot(path=OUTPUT / "review-memo.png", full_page=False)
        browser.close()


if __name__ == "__main__":
    capture()
