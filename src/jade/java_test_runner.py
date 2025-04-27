"""
Java Test Runner Module

This module provides functionality to run Java tests that have been identified as impacted
by changes to specific methods in the codebase. It works in conjunction with the
JavaTestAnalyzer to execute only the tests that are affected by code changes.

The approach:
1. Takes a list of impacted tests (fully qualified test method names)
2. Locates the corresponding test files
3. Executes the tests using a Java test runner (e.g., JUnit)
4. Reports the test results
"""

import os
import subprocess
import re
import shutil
import logging
from typing import Dict, List, Set, Optional, Tuple, Union

def run_subprocess(cmd: List[str], cwd: str, error_msg: str) -> Tuple[bool, str, str]:
    """
    Run a subprocess command and handle errors.

    Args:
        cmd (List[str]): Command to run
        cwd (str): Working directory
        error_msg (str): Error message prefix

    Returns:
        Tuple[bool, str, str]: (success, stdout, stderr)
    """
    try:
        process = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )

        if process.returncode != 0:
            logging.error(f"{error_msg}: {process.stderr}")
            return False, process.stdout, process.stderr

        return True, process.stdout, process.stderr
    except Exception as e:
        logging.error(f"{error_msg}: {e}")
        return False, "", str(e)


class JavaTestRunner:
    """
    Runs Java tests that have been identified as impacted by code changes.
    """

    def __init__(self, project_dir: str, test_dir: str = None, build_tool: str = "maven"):
        """
        Initialize the JavaTestRunner.

        Args:
            project_dir (str): Root directory of the Java project
            test_dir (str, optional): Directory containing Java test files. If not provided,
                                     will use standard Maven/Gradle test directory structure
            build_tool (str, optional): Build tool used by the project ('maven', 'gradle', or 'java')
                                       Use 'java' for projects without Maven or Gradle
        """
        self.project_dir = project_dir
        self.build_tool = build_tool.lower()

        # If test_dir is not provided, use standard directory based on build tool
        if test_dir is None:
            if self.build_tool == "maven":
                self.test_dir = os.path.join(project_dir, "src", "test", "java")
            elif self.build_tool == "gradle":
                self.test_dir = os.path.join(project_dir, "src", "test", "java")
            elif self.build_tool == "java":
                self.test_dir = os.path.join(project_dir, "test")
            else:
                raise ValueError(f"Unsupported build tool: {build_tool}. Use 'maven', 'gradle', or 'java'.")
        else:
            self.test_dir = test_dir

    def run_impacted_tests(self, impacted_tests: List[str]) -> Dict[str, bool]:
        """
        Run the impacted tests and return the results.

        Args:
            impacted_tests (List[str]): List of fully qualified test method names to run

        Returns:
            Dict[str, bool]: Dictionary mapping test names to their pass/fail status
        """
        results = {}

        # Group tests by class to minimize test runs
        tests_by_class = self._group_tests_by_class(impacted_tests)

        for class_name, methods in tests_by_class.items():
            class_results = self._run_test_class(class_name, methods)
            results.update(class_results)

        return results

    def _group_tests_by_class(self, test_names: List[str]) -> Dict[str, List[str]]:
        """
        Group test methods by their class name.

        Args:
            test_names (List[str]): List of fully qualified test method names

        Returns:
            Dict[str, List[str]]: Dictionary mapping class names to lists of test methods
        """
        tests_by_class = {}

        for test_name in test_names:
            # Split the test name into package, class, and method
            parts = test_name.split(".")
            if len(parts) < 2:
                print(f"Warning: Invalid test name format: {test_name}")
                continue

            method_name = parts[-1]
            class_name = ".".join(parts[:-1])

            if class_name not in tests_by_class:
                tests_by_class[class_name] = []

            tests_by_class[class_name].append(method_name)

        return tests_by_class

    def _run_test_class(self, class_name: str, methods: List[str]) -> Dict[str, bool]:
        """
        Run tests from a specific class.

        Args:
            class_name (str): Fully qualified class name
            methods (List[str]): List of test method names to run

        Returns:
            Dict[str, bool]: Dictionary mapping test names to their pass/fail status
        """
        results = {}

        # Convert class name to file path
        file_path = self._class_name_to_file_path(class_name)
        if not file_path or not os.path.exists(file_path):
            print(f"Warning: Could not find test file for class {class_name}")
            for method in methods:
                results[f"{class_name}.{method}"] = False
            return results

        # Run the tests based on the build tool
        if self.build_tool == "maven":
            cmd_results = self._run_maven_tests(class_name, methods)
        elif self.build_tool == "gradle":
            cmd_results = self._run_gradle_tests(class_name, methods)
        elif self.build_tool == "java":
            cmd_results = self._run_java_tests(class_name, methods, file_path)
        else:
            print(f"Error: Unsupported build tool {self.build_tool}")
            for method in methods:
                results[f"{class_name}.{method}"] = False
            return results

        # Parse the results
        for method in methods:
            test_name = f"{class_name}.{method}"
            if test_name in cmd_results:
                results[test_name] = cmd_results[test_name]
            else:
                # If we couldn't find the result, assume failure
                results[test_name] = False

        return results

    def _class_name_to_file_path(self, class_name: str) -> Optional[str]:
        """
        Convert a fully qualified class name to a file path.

        Args:
            class_name (str): Fully qualified class name (e.g., com.example.MyTest)

        Returns:
            Optional[str]: Path to the Java file, or None if not found
        """
        # Replace dots with directory separators and add .java extension
        relative_path = class_name.replace(".", os.path.sep) + ".java"

        # Look for the file in the test directory
        file_path = os.path.join(self.test_dir, relative_path)

        if os.path.exists(file_path):
            return file_path

        # If not found, try to search for it
        for root, _, files in os.walk(self.test_dir):
            for file in files:
                if file == os.path.basename(relative_path):
                    return os.path.join(root, file)

        return None

    def _run_maven_tests(self, class_name: str, methods: List[str]) -> Dict[str, bool]:
        """
        Run tests using Maven.

        Args:
            class_name (str): Fully qualified class name
            methods (List[str]): List of test method names to run

        Returns:
            Dict[str, bool]: Dictionary mapping test names to their pass/fail status
        """
        results = {}

        # Build the Maven command to run specific tests
        test_methods = [f"{class_name}#{method}" for method in methods]
        test_string = ",".join(test_methods)

        cmd = ["mvn", "test", "-Dtest=" + test_string]

        # Run the command
        success, stdout, stderr = run_subprocess(
            cmd, 
            self.project_dir, 
            "Error running Maven tests"
        )

        # Parse the output to determine which tests passed/failed
        for method in methods:
            test_name = f"{class_name}.{method}"
            if success and f"Tests run: 1, Failures: 0, Errors: 0" in stdout:
                results[test_name] = True
            else:
                results[test_name] = False
                if not success:
                    logging.error(f"Test {test_name} failed: {stderr}")

        return results

    def _run_gradle_tests(self, class_name: str, methods: List[str]) -> Dict[str, bool]:
        """
        Run tests using Gradle.

        Args:
            class_name (str): Fully qualified class name
            methods (List[str]): List of test method names to run

        Returns:
            Dict[str, bool]: Dictionary mapping test names to their pass/fail status
        """
        results = {}

        # Build the Gradle command to run specific tests
        test_filter = f"{class_name}"
        if methods:
            method_filters = [f"{method}" for method in methods]
            test_filter = f"{class_name}.{{{','.join(method_filters)}}}"

        cmd = ["gradle", "test", f"--tests", test_filter]

        # Run the command
        success, stdout, stderr = run_subprocess(
            cmd, 
            self.project_dir, 
            "Error running Gradle tests"
        )

        # Parse the output to determine which tests passed/failed
        for method in methods:
            test_name = f"{class_name}.{method}"
            if success and "SUCCESS" in stdout and "FAILED" not in stdout:
                results[test_name] = True
            else:
                results[test_name] = False
                if not success:
                    logging.error(f"Test {test_name} failed: {stderr}")

        return results

    def _create_temp_dir(self) -> Tuple[str, str]:
        """
        Create a temporary directory for compiled classes and find the source directory.

        Returns:
            Tuple[str, str]: (temp_dir, src_dir)
        """
        # Create a temporary directory for compiled classes
        temp_dir = os.path.join(self.project_dir, "temp_classes")
        os.makedirs(temp_dir, exist_ok=True)

        # Find the src directory (assuming standard Java project structure)
        src_dir = os.path.join(self.project_dir, "src")
        if not os.path.exists(src_dir):
            src_dir = self.project_dir

        return temp_dir, src_dir

    def _compile_test_file(self, file_path: str, temp_dir: str, src_dir: str) -> bool:
        """
        Compile a Java test file.

        Args:
            file_path (str): Path to the Java test file
            temp_dir (str): Directory for compiled classes
            src_dir (str): Source directory

        Returns:
            bool: True if compilation succeeded, False otherwise
        """
        # Compile the test file
        compile_cmd = [
            "javac", 
            "-d", temp_dir,
            "-cp", f"{temp_dir};{src_dir}",
            file_path
        ]

        success, _, stderr = run_subprocess(
            compile_cmd,
            self.project_dir,
            "Error compiling test file"
        )

        if not success:
            logging.error(f"Failed to compile {file_path}: {stderr}")

        return success

    def _run_single_test(self, class_name: str, method: str, temp_dir: str, src_dir: str) -> bool:
        """
        Run a single Java test.

        Args:
            class_name (str): Fully qualified class name
            method (str): Test method name
            temp_dir (str): Directory with compiled classes
            src_dir (str): Source directory

        Returns:
            bool: True if the test passed, False otherwise
        """
        # Run the test using JUnit
        run_cmd = [
            "java",
            "-cp", f"{temp_dir};{src_dir}",
            "org.junit.runner.JUnitCore",
            f"{class_name}#{method}"
        ]

        success, stdout, stderr = run_subprocess(
            run_cmd,
            self.project_dir,
            f"Error running test {class_name}.{method}"
        )

        # Check if the test passed
        if success and "OK" in stdout:
            return True
        else:
            if not success:
                logging.error(f"Test {class_name}.{method} failed: {stderr}")
            return False

    def _run_java_tests(self, class_name: str, methods: List[str], file_path: str) -> Dict[str, bool]:
        """
        Run tests using direct Java commands (javac/java) for projects without Maven or Gradle.

        This method compiles the test file and runs it with JUnit directly.

        Args:
            class_name (str): Fully qualified class name
            methods (List[str]): List of test method names to run
            file_path (str): Path to the Java test file

        Returns:
            Dict[str, bool]: Dictionary mapping test names to their pass/fail status
        """
        results = {}
        temp_dir = None

        try:
            # Create temporary directory and find source directory
            temp_dir, src_dir = self._create_temp_dir()

            # Compile the test file
            if not self._compile_test_file(file_path, temp_dir, src_dir):
                # Compilation failed, mark all tests as failed
                for method in methods:
                    results[f"{class_name}.{method}"] = False
                return results

            # Run each test method
            for method in methods:
                test_name = f"{class_name}.{method}"
                results[test_name] = self._run_single_test(class_name, method, temp_dir, src_dir)

        except Exception as e:
            logging.error(f"Error running Java tests: {e}")
            for method in methods:
                results[f"{class_name}.{method}"] = False

        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    logging.warning(f"Failed to clean up temporary directory: {e}")

        return results


def run_impacted_tests(project_dir: str, impacted_tests: List[str], 
                      test_dir: str = None, build_tool: str = "maven") -> Dict[str, bool]:
    """
    Run the impacted tests and return the results.

    Args:
        project_dir (str): Root directory of the Java project
        impacted_tests (List[str]): List of fully qualified test method names to run
        test_dir (str, optional): Directory containing Java test files
        build_tool (str, optional): Build tool used by the project ('maven', 'gradle', or 'java')
                                   Use 'java' for projects without Maven or Gradle

    Returns:
        Dict[str, bool]: Dictionary mapping test names to their pass/fail status
    """
    runner = JavaTestRunner(project_dir, test_dir, build_tool)
    return runner.run_impacted_tests(impacted_tests)


def run_impacted_tests_from_analyzer_output(project_dir: str, analyzer_output: Dict[str, List[str]],
                                          test_dir: str = None, build_tool: str = "maven") -> Dict[str, bool]:
    """
    Run tests impacted by changes based on the output from JavaTestAnalyzer.

    Args:
        project_dir (str): Root directory of the Java project
        analyzer_output (Dict[str, List[str]]): Output from JavaTestAnalyzer.get_impacted_tests()
        test_dir (str, optional): Directory containing Java test files
        build_tool (str, optional): Build tool used by the project ('maven', 'gradle', or 'java')
                                   Use 'java' for projects without Maven or Gradle

    Returns:
        Dict[str, bool]: Dictionary mapping test names to their pass/fail status
    """
    # Flatten the list of impacted tests
    all_impacted_tests = set()
    for tests in analyzer_output.values():
        all_impacted_tests.update(tests)

    # Run the tests
    return run_impacted_tests(project_dir, list(all_impacted_tests), test_dir, build_tool)
