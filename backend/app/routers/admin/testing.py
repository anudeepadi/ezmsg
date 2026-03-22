"""Admin endpoints for running and viewing test results."""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.security.deps import require_admin
from app.models import User

router = APIRouter(tags=["Testing"])


def run_tests_sync() -> dict[str, Any]:
    """Run pytest and capture results synchronously."""
    api_dir = Path(__file__).parent.parent.parent.parent

    # Run pytest with verbose output
    # Use a different test port to avoid conflicts with running server
    env = {**subprocess.os.environ, "TEST_API_PORT": "8002"}

    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            str(api_dir / "tests"),
            "-v",
            "--tb=line"
        ],
        capture_output=True,
        text=True,
        cwd=str(api_dir),
        timeout=120,  # 2 minute timeout
        env=env
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
        # Look for test result lines like: tests/test_auth.py::test_login_success PASSED
        if '::' in line:
            # Clean up the line
            clean_line = line.strip()

            # Check for status indicators at the end
            for status_str, status_key in [('PASSED', 'passed'), ('FAILED', 'failed'),
                                           ('ERROR', 'error'), ('SKIPPED', 'skipped')]:
                if f' {status_str}' in clean_line or clean_line.endswith(status_str):
                    # Parse test file and name
                    try:
                        # Split by :: to get file and test name
                        parts = clean_line.split('::')
                        if len(parts) >= 2:
                            file_name = parts[0].strip()
                            # Remove 'tests/' prefix if present
                            if file_name.startswith('tests/'):
                                file_name = file_name[6:]

                            # Extract test name (remove status and percentage)
                            test_info = parts[1].strip()
                            # Remove status from end
                            for suffix in [' PASSED', ' FAILED', ' ERROR', ' SKIPPED']:
                                if suffix in test_info:
                                    test_name = test_info.split(suffix)[0].strip()
                                    break
                            else:
                                test_name = test_info

                            # Remove percentage like [100%]
                            if '[' in test_name:
                                test_name = test_name.split('[')[0].strip()

                            summary[status_key] += 1
                            summary["total"] += 1

                            tests.append({
                                "file": file_name,
                                "name": test_name,
                                "status": status_key,
                                "full_name": f"{file_name}::{test_name}"
                            })
                    except Exception:
                        pass
                    break

    # Calculate pass rate
    if summary["total"] > 0:
        summary["pass_rate"] = round((summary["passed"] / summary["total"]) * 100, 1)
    else:
        summary["pass_rate"] = 0

    return {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "tests": tests,
        "exit_code": result.returncode,
        "raw_output": output[-3000:] if len(output) > 3000 else output
    }


@router.post("/run")
async def run_tests(
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Run the API test suite and return results.

    Only available to admin users.
    """
    # Run tests in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, run_tests_sync)
    return results


@router.get("/health")
async def testing_health(
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    Check if the testing infrastructure is available.
    """
    api_dir = Path(__file__).parent.parent.parent.parent
    tests_dir = api_dir / "tests"

    test_files = list(tests_dir.glob("test_*.py"))

    return {
        "status": "available",
        "tests_directory": str(tests_dir),
        "test_files_count": len(test_files),
        "test_files": [f.name for f in test_files]
    }
