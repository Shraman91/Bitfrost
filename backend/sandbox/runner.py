import os
import sys
import re
import tempfile
import subprocess
import logging
from typing import Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger("agentarena.sandbox")


class SandboxResult(BaseModel):
    passed: bool = False
    score: float = 0.0
    passed_tests: int = 0
    total_tests: int = 0
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None


def parse_unittest_output(stdout: str, stderr: str) -> tuple[int, int, bool]:
    """
    Parses Python unittest output from stderr/stdout.
    Returns: (passed_tests, total_tests, passed_all)
    """
    output = f"{stdout}\n{stderr}"
    
    # Match "Ran X tests in Ys" or "Ran X test in Ys"
    ran_match = re.search(r"Ran (\d+) tests? in", output)
    if not ran_match:
        return 0, 0, False

    total_tests = int(ran_match.group(1))

    # Check for OK (may be "OK" or "OK (skipped=1)")
    if re.search(r"\bOK\b", output) and not re.search(r"\bFAILED\b", output):
        return total_tests, total_tests, True

    # Check for FAILED (failures=F, errors=E)
    failed_match = re.search(r"FAILED \((.*?)\)", output)
    if failed_match:
        info_str = failed_match.group(1)
        failures = 0
        errors = 0
        f_match = re.search(r"failures=(\d+)", info_str)
        if f_match:
            failures = int(f_match.group(1))
        e_match = re.search(r"errors=(\d+)", info_str)
        if e_match:
            errors = int(e_match.group(1))
        
        failed_count = failures + errors
        passed_tests = max(0, total_tests - failed_count)
        return passed_tests, total_tests, False

    return 0, total_tests, False


def run_tests_in_sandbox(
    files: Dict[str, str],
    hidden_tests: str,
    timeout: int = 10
) -> SandboxResult:
    """
    Executes agent code against hidden tests in an isolated temporary environment.
    """
    with tempfile.TemporaryDirectory(prefix="arena_sandbox_") as tmpdir:
        # 1. Write agent files
        for filename, content in files.items():
            # Prevent path traversal
            clean_name = os.path.normpath(filename).lstrip(r"\/")
            full_path = os.path.join(tmpdir, clean_name)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        # 2. Write hidden tests
        test_file_path = os.path.join(tmpdir, "test_solution.py")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(hidden_tests)

        # 3. Restricted execution environment
        clean_env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": ".",
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\WINDOWS"),
            "PYTHONUNBUFFERED": "1"
        }

        # 4. Execute test subprocess
        cmd = [sys.executable, "-m", "unittest", "test_solution.py"]
        try:
            proc = subprocess.run(
                cmd,
                cwd=tmpdir,
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            stdout = proc.stdout
            stderr = proc.stderr
            
            passed_tests, total_tests, passed_all = parse_unittest_output(stdout, stderr)
            score = round(passed_tests / total_tests, 4) if total_tests > 0 else 0.0

            return SandboxResult(
                passed=passed_all,
                score=score,
                passed_tests=passed_tests,
                total_tests=total_tests,
                stdout=stdout,
                stderr=stderr,
                error=None if passed_all else ("Tests failed" if total_tests > 0 else stderr[:200])
            )

        except subprocess.TimeoutExpired as te:
            stdout = te.stdout or ""
            stderr = te.stderr or ""
            return SandboxResult(
                passed=False,
                score=0.0,
                passed_tests=0,
                total_tests=0,
                stdout=stdout if isinstance(stdout, str) else stdout.decode("utf-8", errors="ignore"),
                stderr=stderr if isinstance(stderr, str) else stderr.decode("utf-8", errors="ignore"),
                error=f"Execution timed out after {timeout} seconds"
            )
        except Exception as e:
            return SandboxResult(
                passed=False,
                score=0.0,
                passed_tests=0,
                total_tests=0,
                stdout="",
                stderr="",
                error=f"Sandbox execution error: {str(e)}"
            )

