#!/usr/bin/env python3
"""
Test runner script that outputs results in JSON format.
Used by the API to provide test results to the frontend.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_tests():
    """Run pytest and capture results."""
    api_dir = Path(__file__).parent.parent

    # Run pytest with JSON output
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            str(api_dir / "tests"),
            "-v",
            "--tb=short",
            "-q"
        ],
        capture_output=True,
        text=True,
        cwd=str(api_dir)
    )

    # Parse the output
    output = result.stdout + result.stderr
    lines = output.strip().split('\n')

    tests = []
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0
    }

    for line in lines:
        if '::' in line and ('PASSED' in line or 'FAILED' in line or 'ERROR' in line or 'SKIPPED' in line):
            parts = line.split('::')
            if len(parts) >= 2:
                file_name = parts[0].strip()
                test_part = parts[1].strip()

                # Determine status
                if 'PASSED' in line:
                    status = 'passed'
                    test_name = test_part.split(' PASSED')[0].strip()
                    summary["passed"] += 1
                elif 'FAILED' in line:
                    status = 'failed'
                    test_name = test_part.split(' FAILED')[0].strip()
                    summary["failed"] += 1
                elif 'ERROR' in line:
                    status = 'error'
                    test_name = test_part.split(' ERROR')[0].strip()
                    summary["errors"] += 1
                elif 'SKIPPED' in line:
                    status = 'skipped'
                    test_name = test_part.split(' SKIPPED')[0].strip()
                    summary["skipped"] += 1
                else:
                    continue

                summary["total"] += 1

                tests.append({
                    "file": file_name,
                    "name": test_name,
                    "status": status,
                    "full_name": f"{file_name}::{test_name}"
                })

    # Calculate pass rate
    if summary["total"] > 0:
        summary["pass_rate"] = round((summary["passed"] / summary["total"]) * 100, 1)
    else:
        summary["pass_rate"] = 0

    results = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "tests": tests,
        "exit_code": result.returncode,
        "raw_output": output[-2000:] if len(output) > 2000 else output  # Last 2000 chars
    }

    return results


if __name__ == "__main__":
    results = run_tests()
    print(json.dumps(results, indent=2))
