"""
playwright_login.py — Playwright-based login automation (demo stage)

Logs into https://the-internet.herokuapp.com/login, extracts the session
cookie, and writes it to $GITHUB_ENV so later steps in the same job can
read it as AUTH_TOKEN.

Structured to mirror a real Page-Object-Model login class so you can swap
in your company's SSO LoginPage later with minimal changes.

Usage:
    python playwright_login.py
"""

import os
from playwright.sync_api import sync_playwright, Page

# ── Credentials (public practice site — move to GitHub Secrets for real apps) ─
LOGIN_URL = "https://the-internet.herokuapp.com/login"
USERNAME  = "tomsmith"
PASSWORD  = "SuperSecretPassword!"

# Name of the env var written to $GITHUB_ENV (and printed to stdout locally)
TOKEN_ENV_VAR = "AUTH_TOKEN"


# ── Page-Object-Model style class ─────────────────────────────────────────────
# Method names mirror the real SSO flow so swapping in the real LoginPage class
# later means dropping in the new class and keeping the __main__ logic below.

class LoginPage:
    def __init__(self, page: Page):
        self.page = page

    def navigate_to_login(self):
        """Navigate to the login URL."""
        self.page.goto(LOGIN_URL)

    def enter_username(self, username: str):
        """Fill the username field."""
        self.page.fill("#username", username)

    def enter_password(self, password: str):
        """Fill the password field."""
        self.page.fill("#password", password)

    def click_sign_in(self):
        """Submit the login form."""
        self.page.click('button[type="submit"]')

    def wait_for_login_success(self):
        """
        Wait for the post-login page to confirm success.
        The practice site redirects to /secure and shows a flash message.
        Adapt this selector for your real app's success indicator.
        """
        self.page.wait_for_url("**/secure", timeout=10_000)
        flash = self.page.locator(".flash.success")
        flash.wait_for(timeout=5_000)
        text = flash.inner_text()
        assert "You logged into a secure area!" in text, (
            f"Unexpected post-login message: {text!r}"
        )
        print("Login confirmed:", text.strip())


def extract_session_cookie(context) -> str:
    """
    Pull the session cookie from the browser context.
    For a real app you might extract a JWT from localStorage or an
    Authorization header instead — adjust the key name as needed.
    """
    cookies = context.cookies()
    for cookie in cookies:
        # The practice site sets a cookie called "rack.session" after login.
        if "session" in cookie["name"].lower():
            return cookie["value"]
    raise RuntimeError(
        f"Session cookie not found. Available cookies: "
        f"{[c['name'] for c in cookies]}"
    )


def export_token(token: str):
    """
    Write AUTH_TOKEN=<value> to $GITHUB_ENV so it persists to later steps,
    and also print it so local runs can see the value.
    """
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a") as f:
            f.write(f"{TOKEN_ENV_VAR}={token}\n")
        print(f"Written to $GITHUB_ENV: {TOKEN_ENV_VAR}=<token>")
    else:
        # Local run — just print it
        print(f"[local] {TOKEN_ENV_VAR}={token}")


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page    = context.new_page()

        login = LoginPage(page)
        login.navigate_to_login()
        login.enter_username(USERNAME)
        login.enter_password(PASSWORD)
        login.click_sign_in()
        login.wait_for_login_success()

        token = extract_session_cookie(context)
        export_token(token)

        browser.close()

    print("Playwright login automation complete.")
