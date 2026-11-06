import subprocess
import sys
from pathlib import Path


def test_ci_workflow_file_exists_and_valid():
    workflow_path = Path(".github/workflows/ci.yml")
    assert workflow_path.exists(), "ci.yml must exist"
    content = workflow_path.read_text(encoding="utf-8")
    assert "name: CI" in content
    assert "setup-python" in content
    assert "test-backend" in content
    assert "build-frontend" in content
    assert "assemble-site" in content


def test_makefile_has_ci_targets():
    makefile_path = Path("Makefile")
    assert makefile_path.exists()
    content = makefile_path.read_text(encoding="utf-8")
    assert "ci-local:" in content, "Makefile must have ci-local target"
    assert "ci-act:" in content, "Makefile must have ci-act target"


def test_local_ci_runner_dry_run():
    runner_script = Path("scripts/run_ci_local.py")
    assert runner_script.exists(), "scripts/run_ci_local.py must exist"

    result = subprocess.run(
        [sys.executable, str(runner_script), "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Dry run failed: {result.stderr}"
    assert "Backend Lint" in result.stdout
    assert "Backend Tests" in result.stdout
    assert "Frontend Tests" in result.stdout
    assert "Build Frontend" in result.stdout
    assert "Assemble Site" in result.stdout


def test_local_ci_runner_skip_flags():
    runner_script = Path("scripts/run_ci_local.py")
    result = subprocess.run(
        [sys.executable, str(runner_script), "--dry-run", "--skip-frontend"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Frontend Tests & Coverage" in result.stdout
    assert "--skip-frontend" in result.stdout
