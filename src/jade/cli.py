"""
Command Line Interface for JADE (Java Analyzer for Detecting Effects)

This module provides a command-line interface for the JADE tool, which analyzes
Java code changes and identifies which tests are impacted by those changes.
"""

import argparse
import os
import sys
import logging
from typing import Dict, List, Optional, Set, Tuple

from . import git
from . import java_test_analyzer
from . import java_test_runner
from . import java_parser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="JADE: Java Analyzer for Detecting Effects",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Commit comparison options
    parser.add_argument("-c", "--commits-back", type=int, help="Compare HEAD to the Nth previous commit")
    parser.add_argument("--branch", action="append", help="Branch to compare (can be specified twice)")
    parser.add_argument("--commit", action="append", help="Commit hash to compare (can be specified twice)")

    # Output options
    parser.add_argument("--tests-only", action="store_true", help="Only show impacted tests, not methods")
    parser.add_argument("--run-tests", action="store_true", help="Run the impacted tests")
    parser.add_argument("--output-file", help="Save the analysis results to a file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    # Project options
    parser.add_argument("--project-dir", default=".", help="Java project directory (default: current directory)")
    parser.add_argument("--test-dir", help="Test directory (default: src/test/java)")
    parser.add_argument("--build-tool", default="maven", choices=["maven", "gradle", "java"],
                        help="Build tool (maven, gradle, java)")

    return parser.parse_args()


def get_comparison_commits(args) -> Tuple[str, str]:
    """
    Determine which commits to compare based on command-line arguments.

    Returns:
        Tuple[str, str]: (base_commit, target_commit)
    """
    # Default to comparing with HEAD
    target_commit = "HEAD"

    # Case 1: jade -c N (compare HEAD to the Nth previous commit)
    if args.commits_back:
        base_commit = git.get_previous_commit(args.commits_back)
        return base_commit, target_commit

    # Case 2: Two branches specified (compare the HEADs of two branches)
    if args.branch and len(args.branch) == 2:
        base_commit = git.get_branch_head(args.branch[0])
        target_commit = git.get_branch_head(args.branch[1])
        return base_commit, target_commit

    # Case 3: One branch specified (compare HEAD to the HEAD of another branch)
    if args.branch and len(args.branch) == 1:
        base_commit = git.get_branch_head(args.branch[0])
        return base_commit, target_commit

    # Case 4: Two commits specified (compare two specific commits)
    if args.commit and len(args.commit) == 2:
        base_commit = args.commit[0]
        target_commit = args.commit[1]
        return base_commit, target_commit

    # Case 5: One commit specified (compare HEAD to a specific commit)
    if args.commit and len(args.commit) == 1:
        base_commit = args.commit[0]
        return base_commit, target_commit

    # Case 6: Branch and commit specified (compare the HEAD of a branch to a specific commit)
    if args.branch and len(args.branch) == 1 and args.commit and len(args.commit) == 1:
        base_commit = args.commit[0]
        target_commit = git.get_branch_head(args.branch[0])
        return base_commit, target_commit

    # Default: compare HEAD to the previous commit
    base_commit = git.get_previous_commit(1)
    return base_commit, target_commit


def get_changed_methods(base_commit: str, target_commit: str, project_dir: str) -> List[str]:
    """
    Get the list of methods that have changed between two commits.

    Args:
        base_commit (str): Base commit hash
        target_commit (str): Target commit hash
        project_dir (str): Java project directory

    Returns:
        List[str]: List of fully qualified method names that have changed
    """
    try:
        # Get the diff between the two commits
        diff_output = git.get_git_diff(base_commit, target_commit)

        # Get the list of affected files
        affected_files = git.get_affected_files(base_commit, target_commit)

        # Filter for Java files only
        java_files = [f for f in affected_files if f.endswith(".java")]

        if not java_files:
            logging.warning("No Java files were changed between the commits.")
            return []

        # Use java_parser to identify changed methods
        try:
            # Get the full paths for the Java files
            full_paths = [os.path.join(project_dir, f) for f in java_files]

            # Log the files being analyzed
            logging.debug(f"Files analyzed: {', '.join(full_paths)}")

            # Parse the impacted objects and methods
            impacted_data = java_parser.parse_impacted_objects_and_methods(diff_output, full_paths)

            # Log the impacted data for debugging
            logging.debug(f"Impacted data: {impacted_data}")

            # Extract the changed methods
            changed_methods = []
            for file_path, data in impacted_data.items():
                # Get the package and class name from the file path
                file_name = os.path.basename(file_path)
                class_name = file_name.replace(".java", "")

                # Add the impacted methods
                for method in data.get("impacted_methods", []):
                    changed_methods.append(f"{class_name}.{method}")

                # Add the impacted constructors
                for constructor in data.get("impacted_constructors", []):
                    changed_methods.append(f"{class_name}.{constructor}")

            if not changed_methods:
                logging.warning("No changed methods were identified.")
                # Don't fall back to placeholder method in verbose mode
                if logging.getLogger().level <= logging.DEBUG:
                    return []
                else:
                    logging.warning("Falling back to placeholder method.")
                    return ["com.example.SomeClass.someMethod"]  # Placeholder

            return changed_methods

        except Exception as e:
            logging.error(f"Error parsing Java files: {e}")
            # Don't fall back to placeholder method in verbose mode
            if logging.getLogger().level <= logging.DEBUG:
                return []
            else:
                logging.warning("Falling back to placeholder method.")
                return ["com.example.SomeClass.someMethod"]  # Placeholder

    except Exception as e:
        logging.error(f"Error getting changed methods: {e}")
        return []


def main():
    """Main entry point for the CLI."""
    try:
        args = parse_args()

        # Set logging level to DEBUG if verbose mode is enabled
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Verbose mode enabled")

        # Determine which commits to compare
        try:
            base_commit, target_commit = get_comparison_commits(args)
            logging.info(f"Comparing {base_commit} to {target_commit}")
        except Exception as e:
            logging.error(f"Error determining commits to compare: {e}")
            return 1

        # Get the list of methods that have changed
        changed_methods = get_changed_methods(base_commit, target_commit, args.project_dir)
        if not changed_methods:
            logging.warning("No changed methods were identified.")

        # Set up the test directory
        test_dir = args.test_dir
        if not test_dir:
            if args.build_tool in ["maven", "gradle"]:
                test_dir = os.path.join(args.project_dir, "src", "test", "java")
            else:  # java
                test_dir = os.path.join(args.project_dir, "test")

        # Analyze the tests
        try:
            analyzer = java_test_analyzer.analyze_java_tests(test_dir, args.output_file)
        except Exception as e:
            logging.error(f"Error analyzing tests: {e}")
            return 1

        # Identify impacted tests
        try:
            impacted_tests = java_test_analyzer.identify_impacted_tests(analyzer, changed_methods)
        except Exception as e:
            logging.error(f"Error identifying impacted tests: {e}")
            return 1

        # Display the results
        if args.tests_only:
            # Only show the impacted tests
            all_tests = set()
            for tests in impacted_tests.values():
                all_tests.update(tests)

            if all_tests:
                logging.info("\nImpacted tests:")
                for test in sorted(all_tests):
                    logging.info(f"  {test}")
            else:
                logging.warning("No impacted tests were identified.")
        else:
            # Show both changed methods and impacted tests
            if impacted_tests:
                logging.info("\nChanged methods and impacted tests:")
                for method, tests in impacted_tests.items():
                    logging.info(f"\n{method}:")
                    for test in tests:
                        logging.info(f"  {test}")
            else:
                logging.warning("No impacted tests were identified.")

        # Run the tests if requested
        if args.run_tests:
            if not any(tests for tests in impacted_tests.values()):
                logging.warning("No tests to run.")
            else:
                logging.info("\nRunning impacted tests...")
                try:
                    results = java_test_runner.run_impacted_tests_from_analyzer_output(
                        args.project_dir, impacted_tests, test_dir, args.build_tool
                    )

                    # Display the test results
                    if results:
                        logging.info("\nTest results:")
                        passed_count = sum(1 for passed in results.values() if passed)
                        failed_count = len(results) - passed_count

                        for test, passed in results.items():
                            status = "PASSED" if passed else "FAILED"
                            log_func = logging.info if passed else logging.error
                            log_func(f"  {test}: {status}")

                        logging.info(f"\nSummary: {passed_count} passed, {failed_count} failed")
                    else:
                        logging.warning("No test results were returned.")
                except Exception as e:
                    logging.error(f"Error running tests: {e}")
                    return 1

        return 0
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
