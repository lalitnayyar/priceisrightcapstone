"""
Test Report Generator
Runs the full test suite and writes a timestamped Markdown report:
  tests/results/result_YYYYMMDD_HHMMSS.md

Usage:
    python3 tests/report_generator.py
    python3 tests/report_generator.py --output /custom/path/result.md
"""
import sys
import os
import unittest
import time
import json
import argparse
import traceback
import platform
from datetime import datetime, timezone
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─────────────────────────────────────────────────────────────────────────────
# Custom test result collector
# ─────────────────────────────────────────────────────────────────────────────
class DetailedTestResult(unittest.TestResult):
    """Collects test results with timing and full error details."""

    def __init__(self):
        super().__init__()
        self.test_records = []
        self._start_times = {}

    def startTest(self, test):
        super().startTest(test)
        self._start_times[test.id()] = time.monotonic()

    def _record(self, test, status, detail=""):
        elapsed = time.monotonic() - self._start_times.get(test.id(), 0)
        parts = test.id().split(".")
        module = parts[-3] if len(parts) >= 3 else parts[0]
        cls = parts[-2] if len(parts) >= 2 else ""
        method = parts[-1]
        self.test_records.append({
            "id": test.id(),
            "module": module,
            "class": cls,
            "method": method,
            "status": status,
            "elapsed": elapsed,
            "detail": detail,
            "doc": (test.shortDescription() or "").strip(),
        })

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        tb = "".join(traceback.format_exception(*err))
        self._record(test, "FAIL", tb)

    def addError(self, test, err):
        super().addError(test, err)
        tb = "".join(traceback.format_exception(*err))
        self._record(test, "ERROR", tb)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, "SKIP", reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._record(test, "XFAIL")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._record(test, "XPASS")


# ─────────────────────────────────────────────────────────────────────────────
# Markdown report builder
# ─────────────────────────────────────────────────────────────────────────────
def build_markdown_report(result: DetailedTestResult, total_elapsed: float,
                           run_dt: datetime) -> str:
    records = result.test_records
    total = len(records)
    passed = sum(1 for r in records if r["status"] == "PASS")
    failed = sum(1 for r in records if r["status"] == "FAIL")
    errors = sum(1 for r in records if r["status"] == "ERROR")
    skipped = sum(1 for r in records if r["status"] == "SKIP")
    xfail = sum(1 for r in records if r["status"] == "XFAIL")
    xpass = sum(1 for r in records if r["status"] == "XPASS")
    pass_rate = (passed / total * 100) if total > 0 else 0.0

    # Overall status badge
    if failed == 0 and errors == 0:
        overall = "✅ ALL TESTS PASSED"
        badge_line = f"> **{overall}** — {passed}/{total} tests passed in {total_elapsed:.2f}s"
    else:
        overall = f"❌ {failed + errors} TEST(S) FAILED"
        badge_line = f"> **{overall}** — {passed}/{total} passed, {failed} failed, {errors} errors in {total_elapsed:.2f}s"

    # Group records by module
    modules: dict = {}
    for r in records:
        modules.setdefault(r["module"], []).append(r)

    # Status emoji map
    STATUS_EMOJI = {
        "PASS": "✅", "FAIL": "❌", "ERROR": "💥",
        "SKIP": "⏭️", "XFAIL": "🔶", "XPASS": "🔷",
    }

    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines.append("# 🧪 Price Is Right — Test Run Report")
    lines.append("")
    lines.append(badge_line)
    lines.append("")
    lines.append(f"**Run timestamp:** `{run_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}`  ")
    lines.append(f"**Python version:** `{platform.python_version()}`  ")
    lines.append(f"**Platform:** `{platform.system()} {platform.release()} ({platform.machine()})`  ")
    lines.append(f"**Total duration:** `{total_elapsed:.3f}s`  ")
    lines.append("")

    # ── Summary table ────────────────────────────────────────────────────────
    lines.append("## 📊 Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total tests | **{total}** |")
    lines.append(f"| ✅ Passed | **{passed}** |")
    lines.append(f"| ❌ Failed | **{failed}** |")
    lines.append(f"| 💥 Errors | **{errors}** |")
    lines.append(f"| ⏭️ Skipped | **{skipped}** |")
    lines.append(f"| 🔶 Expected failures | **{xfail}** |")
    lines.append(f"| Pass rate | **{pass_rate:.1f}%** |")
    lines.append(f"| Total duration | **{total_elapsed:.3f}s** |")
    lines.append("")

    # ── Module breakdown ─────────────────────────────────────────────────────
    lines.append("## 📦 Module Breakdown")
    lines.append("")
    lines.append("| Module | Total | ✅ Pass | ❌ Fail | 💥 Error | ⏭️ Skip | Duration |")
    lines.append("|--------|-------|---------|---------|---------|---------|----------|")
    for mod_name, recs in sorted(modules.items()):
        m_total = len(recs)
        m_pass = sum(1 for r in recs if r["status"] == "PASS")
        m_fail = sum(1 for r in recs if r["status"] == "FAIL")
        m_err = sum(1 for r in recs if r["status"] == "ERROR")
        m_skip = sum(1 for r in recs if r["status"] == "SKIP")
        m_dur = sum(r["elapsed"] for r in recs)
        lines.append(f"| `{mod_name}` | {m_total} | {m_pass} | {m_fail} | {m_err} | {m_skip} | {m_dur:.3f}s |")
    lines.append("")

    # ── Detailed results per module ──────────────────────────────────────────
    lines.append("## 🔍 Detailed Results")
    lines.append("")

    for mod_name, recs in sorted(modules.items()):
        # Group by class
        classes: dict = {}
        for r in recs:
            classes.setdefault(r["class"], []).append(r)

        lines.append(f"### `{mod_name}`")
        lines.append("")

        for cls_name, cls_recs in sorted(classes.items()):
            lines.append(f"#### {cls_name}")
            lines.append("")
            lines.append("| # | Test | Status | Duration | Description |")
            lines.append("|---|------|--------|----------|-------------|")
            for i, r in enumerate(cls_recs, 1):
                emoji = STATUS_EMOJI.get(r["status"], "❓")
                method = r["method"]
                status = f"{emoji} {r['status']}"
                dur = f"{r['elapsed']*1000:.1f}ms"
                doc = r["doc"][:60] + "…" if len(r["doc"]) > 60 else r["doc"]
                lines.append(f"| {i} | `{method}` | {status} | {dur} | {doc} |")
            lines.append("")

    # ── Failures and errors detail ───────────────────────────────────────────
    failures_and_errors = [r for r in records if r["status"] in ("FAIL", "ERROR")]
    if failures_and_errors:
        lines.append("## ❌ Failures & Errors — Full Detail")
        lines.append("")
        for r in failures_and_errors:
            emoji = "❌" if r["status"] == "FAIL" else "💥"
            lines.append(f"### {emoji} `{r['id']}`")
            lines.append("")
            if r["doc"]:
                lines.append(f"**Description:** {r['doc']}")
                lines.append("")
            lines.append("```")
            lines.append(r["detail"].strip())
            lines.append("```")
            lines.append("")

    # ── Skipped tests ────────────────────────────────────────────────────────
    skipped_recs = [r for r in records if r["status"] == "SKIP"]
    if skipped_recs:
        lines.append("## ⏭️ Skipped Tests")
        lines.append("")
        lines.append("| Test | Reason |")
        lines.append("|------|--------|")
        for r in skipped_recs:
            reason = r["detail"][:80].replace("|", "\\|")
            lines.append(f"| `{r['id']}` | {reason} |")
        lines.append("")

    # ── Slowest tests ────────────────────────────────────────────────────────
    slowest = sorted(records, key=lambda r: r["elapsed"], reverse=True)[:10]
    lines.append("## 🐢 10 Slowest Tests")
    lines.append("")
    lines.append("| Rank | Test | Duration |")
    lines.append("|------|------|----------|")
    for i, r in enumerate(slowest, 1):
        lines.append(f"| {i} | `{r['method']}` | {r['elapsed']*1000:.1f}ms |")
    lines.append("")

    # ── Environment ──────────────────────────────────────────────────────────
    lines.append("## 🖥️ Environment")
    lines.append("")
    lines.append("| Variable | Value |")
    lines.append("|----------|-------|")
    lines.append(f"| Python | `{sys.version}` |")
    lines.append(f"| OS | `{platform.platform()}` |")
    lines.append(f"| CPU | `{platform.processor() or 'unknown'}` |")

    # Check key packages
    packages = ["openai", "anthropic", "chromadb", "gradio", "fastapi",
                "torch", "sentence_transformers", "feedparser", "pydantic"]
    lines.append("")
    lines.append("**Package versions:**")
    lines.append("")
    lines.append("| Package | Version |")
    lines.append("|---------|---------|")
    for pkg in packages:
        try:
            import importlib.metadata
            ver = importlib.metadata.version(pkg)
        except Exception:
            ver = "not installed"
        lines.append(f"| `{pkg}` | `{ver}` |")
    lines.append("")

    # ── Footer ───────────────────────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated by `tests/report_generator.py` at "
                 f"`{run_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}`*  ")
    lines.append("*Price Is Right — Autonomous 7-Agent AI Deal Hunter*  ")
    lines.append("*Lalit Nayyar | lalitnayyar@gmail.com | +971508320336*")
    lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────
def run_tests(output_path: str = None) -> int:
    run_dt = datetime.now(timezone.utc)
    ts = run_dt.strftime("%Y%m%d_%H%M%S")

    if output_path is None:
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        output_path = os.path.join(results_dir, f"result_{ts}.md")

    print(f"\n{'='*60}")
    print(f"  Price Is Right — Test Suite")
    print(f"  Run: {run_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}\n")

    # Discover and load all tests
    loader = unittest.TestLoader()
    tests_dir = os.path.dirname(__file__)
    suite = loader.discover(tests_dir, pattern="test_*.py")

    # Run with our custom result collector
    result = DetailedTestResult()
    t0 = time.monotonic()
    suite.run(result)
    total_elapsed = time.monotonic() - t0

    # Console summary
    total = result.testsRun
    passed = sum(1 for r in result.test_records if r["status"] == "PASS")
    failed = sum(1 for r in result.test_records if r["status"] == "FAIL")
    errors = sum(1 for r in result.test_records if r["status"] == "ERROR")
    skipped = sum(1 for r in result.test_records if r["status"] == "SKIP")

    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} passed | {failed} failed | "
          f"{errors} errors | {skipped} skipped")
    print(f"  Duration: {total_elapsed:.3f}s")
    print(f"{'='*60}")

    # Print failures to console
    for r in result.test_records:
        if r["status"] in ("FAIL", "ERROR"):
            print(f"\n  {'❌' if r['status']=='FAIL' else '💥'} {r['id']}")
            print(f"  {r['detail'][:300]}")

    # Generate Markdown report
    md = build_markdown_report(result, total_elapsed, run_dt)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\n  📄 Report saved: {output_path}\n")

    # Return exit code
    return 0 if (failed == 0 and errors == 0) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Price Is Right test suite and generate report")
    parser.add_argument("--output", "-o", help="Output path for the Markdown report")
    args = parser.parse_args()
    sys.exit(run_tests(output_path=args.output))
