"""
locustfile.py — Locust load test script
All parameters are hardcoded here; no CLI flags needed.
Run directly via: python locustfile.py
Or let the workflow run it via: locust -f locustfile.py ...
"""

import os
import sys

import subprocess
from locust import HttpUser, task, between

# ── Test parameters ────────────────────────────────────────────────────────────
TARGET_HOST  = "https://the-internet.herokuapp.com"
NUM_USERS    = 5       # total simulated virtual users
SPAWN_RATE   = 1       # users spawned per second
RUN_TIME     = "30s"   # wall-clock test duration
MAX_ITERATIONS = 3     # each user stops after this many task executions


class WebsiteUser(HttpUser):
    """Simulates a user browsing the target site."""

    host = TARGET_HOST
    wait_time = between(1, 3)  # pause 1–3 s between tasks

    def on_start(self):
        """Called once when a virtual user starts. Reset the iteration counter."""
        self._iterations = 0

        # Pick up an auth token if the Playwright login step ran earlier.
        # Falls back to None so unauthenticated runs still work.
        self._auth_token = os.environ.get("AUTH_TOKEN")

    def _auth_headers(self):
        """Return Authorization header dict, or empty dict if no token."""
        if self._auth_token:
            return {"Authorization": f"Bearer {self._auth_token}"}
        return {}

    @task
    def visit_home(self):
        """Hit the homepage — the main load-test task."""
        self.client.get("/", headers=self._auth_headers(), name="Homepage")

        self._iterations += 1
        if self._iterations >= MAX_ITERATIONS:
            # Stop this virtual user after MAX_ITERATIONS executions.
            self.stop()

# ── Entry point — run directly with `python locustfile.py` ────────────────────
if __name__ == "__main__":
    cmd = [
        sys.executable, "-m", "locust",
        "-f", __file__,
        "--headless",              # no web UI (required for CI)
        "--host",    TARGET_HOST,
        "--users",   str(NUM_USERS),
        "--spawn-rate", str(SPAWN_RATE),
        "--run-time", RUN_TIME,
        "--exit-code-on-error", "1",
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)
