#!/usr/bin/env python3
"""Test runner script for AI Manga Generation Backend."""

import argparse
import asyncio
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# Add app to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRunner:
    """Enhanced test runner with reporting and filtering capabilities."""
    
    def __init__(self):
        self.test_root = Path(__file__).parent
        self.app_root = self.test_root.parent
        self.reports_dir = self.test_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_unit_tests(self, verbose: bool = False, coverage: bool = True) -> int:
        """Run unit tests."""
        print("🧪 Running Unit Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_root / "unit"),
            "-m", "unit",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html:htmlcov/unit",
                "--cov-report=term-missing"
            ])
        
        return self._run_command(cmd, "unit_tests")
    
    def run_integration_tests(self, verbose: bool = False) -> int:
        """Run integration tests."""
        print("🔗 Running Integration Tests...")
        
        cmd = [
            "python", "-m", "pytest", 
            str(self.test_root / "integration"),
            "-m", "integration",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "integration_tests")
    
    def run_e2e_tests(self, verbose: bool = False) -> int:
        """Run end-to-end tests."""
        print("🚀 Running End-to-End Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_root / "e2e"),
            "-m", "e2e",
            "--tb=short",
            "--timeout=300"  # 5 minute timeout for E2E
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "e2e_tests")
    
    def run_performance_tests(self, verbose: bool = False) -> int:
        """Run performance tests."""
        print("⚡ Running Performance Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_root / "performance"),
            "-m", "performance",
            "--tb=short",
            "--benchmark-only",
            "--benchmark-json=" + str(self.reports_dir / "benchmark_results.json")
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "performance_tests")
    
    def run_security_tests(self, verbose: bool = False) -> int:
        """Run security tests."""
        print("🔒 Running Security Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_root / "security"),
            "-m", "security",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "security_tests")
    
    def run_all_tests(self, verbose: bool = False, fast: bool = False) -> Dict[str, int]:
        """Run all test suites."""
        print("🎯 Running All Test Suites...")
        
        results = {}
        
        # Unit tests (always run)
        results["unit"] = self.run_unit_tests(verbose, coverage=not fast)
        
        if not fast:
            # Integration tests
            results["integration"] = self.run_integration_tests(verbose)
            
            # E2E tests  
            results["e2e"] = self.run_e2e_tests(verbose)
            
            # Performance tests
            results["performance"] = self.run_performance_tests(verbose)
            
            # Security tests
            results["security"] = self.run_security_tests(verbose)
        
        # Generate summary report
        self._generate_summary_report(results)
        
        return results
    
    def run_specific_test(self, test_path: str, verbose: bool = False) -> int:
        """Run a specific test file or test function."""
        print(f"🎯 Running Specific Test: {test_path}")
        
        cmd = [
            "python", "-m", "pytest",
            test_path,
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "specific_test")
    
    def run_failed_tests(self, verbose: bool = False) -> int:
        """Re-run only failed tests from last run."""
        print("🔄 Re-running Failed Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "--lf",  # Last failed
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "failed_tests")
    
    def run_coverage_report(self) -> int:
        """Generate comprehensive coverage report."""
        print("📊 Generating Coverage Report...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_root),
            "--cov=app",
            "--cov-report=html:htmlcov/complete",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term",
            "--cov-fail-under=80",
            "--quiet"
        ]
        
        result = self._run_command(cmd, "coverage_report")
        
        if result == 0:
            print(f"📊 Coverage report generated: {self.app_root / 'htmlcov' / 'complete' / 'index.html'}")
        
        return result
    
    def run_parallel_tests(self, workers: int = 4, verbose: bool = False) -> int:
        """Run tests in parallel using pytest-xdist."""
        print(f"⚡ Running Tests in Parallel ({workers} workers)...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_root),
            f"-n{workers}",
            "--tb=short",
            "--dist=loadscope"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "parallel_tests")
    
    def run_smoke_tests(self) -> int:
        """Run quick smoke tests."""
        print("💨 Running Smoke Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_root / "unit"),
            "-k", "test_initialization or test_creation or test_basic",
            "--tb=short",
            "--maxfail=5"
        ]
        
        return self._run_command(cmd, "smoke_tests")
    
    def lint_tests(self) -> int:
        """Lint test code quality."""
        print("🧹 Linting Test Code...")
        
        # Run flake8 on tests
        cmd = ["flake8", str(self.test_root), "--count", "--statistics"]
        flake8_result = self._run_command(cmd, "flake8_tests")
        
        # Run mypy on tests
        cmd = ["mypy", str(self.test_root), "--ignore-missing-imports"]
        mypy_result = self._run_command(cmd, "mypy_tests")
        
        return max(flake8_result, mypy_result)
    
    def _run_command(self, cmd: List[str], test_type: str) -> int:
        """Run a command and capture output."""
        print(f"Executing: {' '.join(cmd)}")
        
        # Set up environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.app_root)
        
        try:
            # Run command
            result = subprocess.run(
                cmd,
                cwd=self.app_root,
                env=env,
                capture_output=False,
                text=True
            )
            
            print(f"✅ {test_type} completed with exit code: {result.returncode}")
            return result.returncode
            
        except subprocess.CalledProcessError as e:
            print(f"❌ {test_type} failed with exit code: {e.returncode}")
            return e.returncode
        
        except Exception as e:
            print(f"❌ {test_type} failed with error: {e}")
            return 1
    
    def _generate_summary_report(self, results: Dict[str, int]) -> None:
        """Generate a summary report of test results."""
        report_file = self.reports_dir / "test_summary.json"
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "results": results,
            "total_suites": len(results),
            "passed_suites": sum(1 for code in results.values() if code == 0),
            "failed_suites": sum(1 for code in results.values() if code != 0),
            "overall_status": "PASS" if all(code == 0 for code in results.values()) else "FAIL"
        }
        
        with open(report_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY REPORT")
        print("="*60)
        print(f"Total Test Suites: {summary['total_suites']}")
        print(f"Passed: {summary['passed_suites']}")
        print(f"Failed: {summary['failed_suites']}")
        print(f"Overall Status: {summary['overall_status']}")
        print("="*60)
        
        for suite, code in results.items():
            status = "✅ PASS" if code == 0 else "❌ FAIL"
            print(f"{suite:<15}: {status}")
        
        print(f"\nDetailed report: {report_file}")


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="AI Manga Generation Test Runner")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--parallel", "-p", type=int, default=0, help="Run tests in parallel")
    parser.add_argument("--lint", action="store_true", help="Lint test code")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    parser.add_argument("--failed", action="store_true", help="Re-run failed tests")
    parser.add_argument("--test", help="Run specific test")
    
    # Test suite selection
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--unit", action="store_true", help="Run unit tests only")
    group.add_argument("--integration", action="store_true", help="Run integration tests only")
    group.add_argument("--e2e", action="store_true", help="Run E2E tests only")  
    group.add_argument("--performance", action="store_true", help="Run performance tests only")
    group.add_argument("--security", action="store_true", help="Run security tests only")
    group.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Handle specific operations
    if args.lint:
        return runner.lint_tests()
    
    if args.coverage:
        return runner.run_coverage_report()
    
    if args.smoke:
        return runner.run_smoke_tests()
    
    if args.failed:
        return runner.run_failed_tests(args.verbose)
    
    if args.test:
        return runner.run_specific_test(args.test, args.verbose)
    
    if args.parallel > 0:
        return runner.run_parallel_tests(args.parallel, args.verbose)
    
    # Handle test suite selection
    if args.unit:
        return runner.run_unit_tests(args.verbose)
    elif args.integration:
        return runner.run_integration_tests(args.verbose)
    elif args.e2e:
        return runner.run_e2e_tests(args.verbose)
    elif args.performance:
        return runner.run_performance_tests(args.verbose)
    elif args.security:
        return runner.run_security_tests(args.verbose)
    elif args.all or not any([args.unit, args.integration, args.e2e, args.performance, args.security]):
        results = runner.run_all_tests(args.verbose, args.fast)
        return 0 if all(code == 0 for code in results.values()) else 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())