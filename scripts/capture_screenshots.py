from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8501"
OUTPUT = Path("docs/images")
OUTPUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
    page.goto(BASE_URL, wait_until="networkidle", timeout=60_000)
    page.wait_for_timeout(2_000)
    page.screenshot(path=OUTPUT / "decision-summary.png", full_page=True)

    risk_detail = page.get_by_text("Risk tail detail")
    if risk_detail.count():
        risk_detail.click()
    page.wait_for_timeout(500)
    page.screenshot(path=OUTPUT / "downside-risk.png", full_page=True)

    package_heading = page.get_by_text("Working files")
    if package_heading.count():
        package_heading.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    page.screenshot(path=OUTPUT / "review-package.png", full_page=False)
    browser.close()
