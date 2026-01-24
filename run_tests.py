"""
Test runner and utilities for ARCTL.

Provides:
- Simple test execution
- Benchmark runner
- Test report generation
- CI/CD integration
"""

import sys
import unittest
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime


class TestRunner:
    """Unified test runner for all test suites"""
    
    def __init__(self, test_dir: Path = None):
        """
        Initialize test runner.
        
        Args:
            test_dir: Directory containing tests (defaults to current tests/)
        """
        if test_dir is None:
            test_dir = Path(__file__).parent
        
        self.test_dir = test_dir
        self.results: Dict = {}
    
    def run_unit_tests(self) -> bool:
        """
        Run unit tests only.
        
        Returns:
            True if all tests passed
        """
        print("\n" + "=" * 80)
        print("RUNNING UNIT TESTS")
        print("=" * 80)
        
        loader = unittest.TestLoader()
        suite = loader.discover(str(self.test_dir), pattern='test_core.py')
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.results['unit'] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
        
        return result.wasSuccessful()
    
    def run_integration_tests(self) -> bool:
        """
        Run integration tests only.
        
        Returns:
            True if all tests passed
        """
        print("\n" + "=" * 80)
        print("RUNNING INTEGRATION TESTS")
        print("=" * 80)
        
        loader = unittest.TestLoader()
        suite = loader.discover(str(self.test_dir), pattern='test_integration.py')
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.results['integration'] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
        
        return result.wasSuccessful()
    
    def run_all_tests(self) -> bool:
        """
        Run all unit and integration tests.
        
        Returns:
            True if all tests passed
        """
        unit_ok = self.run_unit_tests()
        integration_ok = self.run_integration_tests()
        
        return unit_ok and integration_ok
    
    def run_benchmarks(self) -> None:
        """Run performance benchmarks"""
        print("\n" + "=" * 80)
        print("RUNNING BENCHMARKS")
        print("=" * 80)
        
        try:
            from tests.benchmarks import run_all_benchmarks
            run_all_benchmarks()
        except ImportError as e:
            print(f"❌ Failed to import benchmarks: {e}")
    
    def print_summary(self) -> None:
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        for suite_name, stats in self.results.items():
            status = "✅ PASSED" if stats['success'] else "❌ FAILED"
            print(f"\n{suite_name.upper()}: {status}")
            print(f"  Tests run:  {stats['tests_run']}")
            print(f"  Failures:   {stats['failures']}")
            print(f"  Errors:     {stats['errors']}")
        
        # Overall status
        all_passed = all(s['success'] for s in self.results.values())
        print("\n" + "-" * 80)
        if all_passed:
            print("✅ ALL TESTS PASSED")
        else:
            print("❌ SOME TESTS FAILED")
        
        return all_passed
    
    def export_results(self, filepath: Path) -> None:
        """
        Export results to JSON (for CI/CD integration).
        
        Args:
            filepath: Path to save JSON results
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'overall_success': all(s['success'] for s in self.results.values())
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Results exported to {filepath}")


def main():
    """Main entry point for test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run ARCTL tests and benchmarks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py              # Run all tests
  python run_tests.py --unit       # Run unit tests only
  python run_tests.py --bench      # Run benchmarks only
  python run_tests.py --export results.json  # Export results
        """
    )
    
    parser.add_argument(
        '--unit',
        action='store_true',
        help='Run unit tests only'
    )
    
    parser.add_argument(
        '--integration',
        action='store_true',
        help='Run integration tests only'
    )
    
    parser.add_argument(
        '--bench',
        action='store_true',
        help='Run benchmarks only'
    )
    
    parser.add_argument(
        '--export',
        type=str,
        help='Export results to JSON file'
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Default: run all if no specific option
    if not (args.unit or args.integration or args.bench):
        runner.run_all_tests()
        runner.print_summary()
    else:
        if args.unit:
            runner.run_unit_tests()
        if args.integration:
            runner.run_integration_tests()
        if args.bench:
            runner.run_benchmarks()
        
        if not args.bench:  # benchmarks have their own output
            runner.print_summary()
    
    # Export if requested
    if args.export:
        runner.export_results(Path(args.export))
    
    # Exit with appropriate code
    sys.exit(0 if runner.results.get('success', True) else 1)


if __name__ == '__main__':
    main()
