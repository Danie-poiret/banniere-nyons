"""Regression checks for readiness, normal contention and real API failures."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import wait_for_layout_writers as waiter


class WaitForWritersTests(unittest.TestCase):
    def test_two_quiet_checks_are_required(self):
        with patch.object(waiter, "active_writers", side_effect=[[], ["SEO"], [], []]) as query, \
             patch.object(waiter.time, "monotonic", return_value=0), \
             patch.object(waiter.time, "sleep"):
            self.assertTrue(waiter.wait_for_writers("owner/repo"))
            self.assertEqual(query.call_count, 4)

    def test_busy_timeout_defers_without_failure(self):
        with patch.object(waiter, "active_writers", return_value=["SEO"]), \
             patch.object(waiter.time, "monotonic", side_effect=[0, 0, 5]), \
             patch.object(waiter.time, "sleep"):
            self.assertFalse(waiter.wait_for_writers("owner/repo", timeout_seconds=5))

    def test_only_active_known_writers_block(self):
        name = next(iter(waiter.WRITERS))
        response = {"workflow_runs": [
            {"name": name, "status": "completed"},
            {"name": "Stabiliser les composants communs avant affichage", "status": "in_progress"},
            {"name": name, "status": "queued"},
        ]}
        with patch.object(waiter.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(response))):
            self.assertEqual(waiter.active_writers("owner/repo"), [name])

    def test_main_publishes_both_readiness_outcomes(self):
        for ready in (True, False):
            with self.subTest(ready=ready), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "output"
                summary = Path(directory) / "summary"
                with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_OUTPUT": str(output), "GITHUB_STEP_SUMMARY": str(summary)}), \
                     patch.object(waiter, "wait_for_writers", return_value=ready):
                    waiter.main()
                self.assertEqual(output.read_text(), f"ready={str(ready).lower()}\n")
                self.assertEqual(summary.exists(), not ready)

    def test_api_failure_is_not_reported_as_a_deferral(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_OUTPUT": str(output)}), \
                 patch.object(waiter.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "gh")), \
                 self.assertRaises(subprocess.CalledProcessError):
                waiter.main()
            self.assertFalse(output.exists())

    def test_malformed_response_fails(self):
        with patch.object(waiter.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "not JSON")), \
             self.assertRaises(json.JSONDecodeError):
            waiter.active_writers("owner/repo")


if __name__ == "__main__":
    unittest.main()
