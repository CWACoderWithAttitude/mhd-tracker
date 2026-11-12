#!/usr/bin/env python3
"""Local CI pipeline runner.

Mirrors the steps defined in .github/workflows/ci.yml so developers can test
and validate the complete CI pipeline locally without waiting for remote GitHub
runners.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


# ANSI terminal colors
class Colors:
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


@dataclass
class StageResult:
    name: str
    status: str  # PASSED, FAILED, SKIPPED
    duration_s: float = 0.0
    error_message: str | None = None


STAGES = [
    {
        "id": "backend-lint",
        "name": "Backend Lint & Format",
        "commands": [
            ["uv", "run", "ruff", "check", "--fix", "."],
            ["uv", "run", "black", "--check", "."],
        ],
        "category": "backend",
    },
    {
        "id": "backend-test",
        "name": "Backend Tests & Coverage",
        "commands": [
            [
                "uv",
                "run",
                "pytest",
                "--cov=app",
                "--cov-report=html:coverage/backend",
                "--cov-report=xml:coverage/backend/coverage.xml",
            ],
        ],
        "category": "backend",
    },
    {
        "id": "frontend-lint",
        "name": "Frontend Lint & Format",
        "commands": [
            ["npm", "run", "lint"],
            ["npm", "run", "format:check"],
        ],
        "cwd": "frontend",
        "category": "frontend",
    },
    {
        "id": "frontend-test",
        "name": "Frontend Tests & Coverage",
        "commands": [
            ["npm", "run", "test", "--", "--coverage"],
        ],
        "cwd": "frontend",
        "category": "frontend",
    },
    {
        "id": "frontend-build",
        "name": "Build Frontend",
        "commands": [
            ["npm", "run", "build"],
        ],
        "cwd": "frontend",
        "category": "frontend",
    },
    {
        "id": "assemble-site",
        "name": "Assemble Site",
        "custom_func": "assemble_site",
        "category": "site",
    },
]


def assemble_site(project_root: Path) -> None:
    """Assembles the site folder containing frontend build and coverage reports."""
    site_dir = project_root / "site"
    frontend_dist = project_root / "frontend" / "dist"
    coverage_backend = project_root / "coverage" / "backend"
    coverage_frontend = project_root / "frontend" / "coverage"

    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy frontend dist
    if frontend_dist.exists():
        shutil.copytree(frontend_dist, site_dir / "frontend", dirs_exist_ok=True)
    else:
        raise FileNotFoundError(f"Frontend dist not found at {frontend_dist}")

    # 2. Copy coverage reports
    coverage_site = site_dir / "coverage"
    coverage_site.mkdir(parents=True, exist_ok=True)

    if coverage_backend.exists():
        shutil.copytree(coverage_backend, coverage_site / "backend", dirs_exist_ok=True)

    if coverage_frontend.exists():
        shutil.copytree(
            coverage_frontend, coverage_site / "frontend", dirs_exist_ok=True
        )


def run_command(cmd: list[str], cwd: Path | None = None) -> int:
    display_cwd = f" (in {cwd})" if cwd else ""
    cmd_str = " ".join(cmd)
    print(f"  {Colors.CYAN}▸ Executing{Colors.RESET}{display_cwd}: {cmd_str}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def run_pipeline(
    dry_run: bool = False,
    selected_stage: str | None = None,
    skip_backend: bool = False,
    skip_frontend: bool = False,
    skip_site: bool = False,
) -> int:
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print(
        f"\n{Colors.BOLD}{Colors.CYAN}====================================================={Colors.RESET}"
    )
    print(
        f"{Colors.BOLD}{Colors.CYAN}       MHD Tracker - Local CI Pipeline Runner        {Colors.RESET}"
    )
    print(
        f"{Colors.BOLD}{Colors.CYAN}====================================================={Colors.RESET}\n"
    )

    results: list[StageResult] = []

    for stage in STAGES:
        stage_id = stage["id"]
        stage_name = stage["name"]
        category = stage["category"]

        # Filter criteria
        if selected_stage and stage_id != selected_stage:
            continue
        if skip_backend and category == "backend":
            results.append(
                StageResult(
                    name=stage_name, status="SKIPPED", error_message="--skip-backend"
                )
            )
            continue
        if skip_frontend and category == "frontend":
            results.append(
                StageResult(
                    name=stage_name, status="SKIPPED", error_message="--skip-frontend"
                )
            )
            continue
        if skip_site and category == "site":
            results.append(
                StageResult(
                    name=stage_name, status="SKIPPED", error_message="--skip-site"
                )
            )
            continue

        print(f"{Colors.BOLD}[Stage] {stage_name}{Colors.RESET}")

        if dry_run:
            if "commands" in stage:
                cwd_dir = (
                    project_root / stage["cwd"] if "cwd" in stage else project_root
                )
                for cmd in stage["commands"]:
                    print(f"  (dry-run) would run: {' '.join(cmd)} in {cwd_dir}")
            elif stage.get("custom_func"):
                print(f"  (dry-run) would execute Python func: {stage['custom_func']}")
            results.append(
                StageResult(name=stage_name, status="DRY-RUN", duration_s=0.0)
            )
            print()
            continue

        start_time = time.time()
        failed = False
        error_msg = None

        if "commands" in stage:
            cwd_dir = project_root / stage["cwd"] if "cwd" in stage else project_root
            for cmd in stage["commands"]:
                ret = run_command(cmd, cwd=cwd_dir)
                if ret != 0:
                    failed = True
                    error_msg = f"Command failed with code {ret}: {' '.join(cmd)}"
                    break
        elif stage.get("custom_func") == "assemble_site":
            try:
                assemble_site(project_root)
                print(
                    f"  {Colors.GREEN}✓ Site assembled successfully at {project_root / 'site'}{Colors.RESET}"
                )
            except Exception as exc:
                failed = True
                error_msg = str(exc)

        duration = time.time() - start_time

        if failed:
            print(
                f"  {Colors.RED}✗ {stage_name} FAILED ({duration:.2f}s){Colors.RESET}\n"
            )
            results.append(
                StageResult(
                    name=stage_name,
                    status="FAILED",
                    duration_s=duration,
                    error_message=error_msg,
                )
            )
            break
        else:
            print(
                f"  {Colors.GREEN}✓ {stage_name} PASSED ({duration:.2f}s){Colors.RESET}\n"
            )
            results.append(
                StageResult(name=stage_name, status="PASSED", duration_s=duration)
            )

    # Summary table
    print(
        f"{Colors.BOLD}{Colors.CYAN}-----------------------------------------------------{Colors.RESET}"
    )
    print(f"{Colors.BOLD}Pipeline Execution Summary:{Colors.RESET}")
    print(
        f"{Colors.BOLD}{Colors.CYAN}-----------------------------------------------------{Colors.RESET}"
    )

    all_passed = True
    for r in results:
        if r.status == "PASSED":
            badge = f"{Colors.GREEN}PASSED{Colors.RESET}"
        elif r.status in ("DRY-RUN", "SKIPPED"):
            badge = f"{Colors.YELLOW}{r.status}{Colors.RESET}"
        else:
            badge = f"{Colors.RED}FAILED{Colors.RESET}"
            all_passed = False

        duration_str = f"{r.duration_s:.2f}s" if r.duration_s > 0 else "-"
        detail = f" ({r.error_message})" if r.error_message else ""
        print(f"  • {r.name:<28} [{badge}] {duration_str}{detail}")

    print(
        f"{Colors.BOLD}{Colors.CYAN}-----------------------------------------------------{Colors.RESET}"
    )

    if not all_passed:
        print(f"{Colors.RED}{Colors.BOLD}Pipeline FAILED!{Colors.RESET}\n")
        return 1

    print(f"{Colors.GREEN}{Colors.BOLD}All pipeline stages succeeded!{Colors.RESET}\n")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run MHD Tracker CI pipeline stages locally."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions that would be executed without running them.",
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=[s["id"] for s in STAGES],
        help="Execute only a specific pipeline stage.",
    )
    parser.add_argument(
        "--skip-backend", action="store_true", help="Skip all backend stages."
    )
    parser.add_argument(
        "--skip-frontend", action="store_true", help="Skip all frontend stages."
    )
    parser.add_argument(
        "--skip-site", action="store_true", help="Skip site assembly stage."
    )

    args = parser.parse_args()
    exit_code = run_pipeline(
        dry_run=args.dry_run,
        selected_stage=args.stage,
        skip_backend=args.skip_backend,
        skip_frontend=args.skip_frontend,
        skip_site=args.skip_site,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
