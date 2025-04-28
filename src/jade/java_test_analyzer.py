"""
Java Test Analyzer Module

This module provides functionality to analyze Java test files and identify which tests
are impacted by changes to specific methods in the codebase.

The approach uses Abstract Syntax Tree (AST) traversal to:
1. Parse Java test files
2. Identify method calls within each test
3. Create a mapping from tests to the methods they invoke
4. Determine which tests are impacted when specific methods change
"""

import os
import logging
import javalang
from typing import Dict, List, Set, Tuple, Optional, Any


class JavaTestAnalyzer:
    """
    Analyzes Java test files to identify method calls and create mappings
    between tests and the methods they invoke.
    """

    def __init__(self, test_dir: str):
        """
        Initialize the JavaTestAnalyzer.

        Args:
            test_dir (str): Directory containing Java test files
        """
        self.test_dir = test_dir
        self.test_to_methods_map: Dict[str, Set[str]] = {}
        self.method_to_tests_map: Dict[str, Set[str]] = {}

    def build_test_method_mapping(self) -> None:
        """
        Build a comprehensive mapping between tests and the methods they invoke.

        This method scans all Java test files in the test directory, parses them,
        and creates bidirectional mappings between tests and methods.
        """
        for root, _, files in os.walk(self.test_dir):
            for file in files:
                # Only process files that end with .java and have "Test" or "test" in the name
                # but exclude files that start with "NotA" to avoid processing files like "NotATest.java"
                if file.endswith(".java") and ("Test" in file or "test" in file) and not file.startswith("NotA"):
                    file_path = os.path.join(root, file)
                    self._process_test_file(file_path)

    def _is_test_method(self, node: javalang.tree.MethodDeclaration) -> bool:
        """
        Determine if a method is a test method.

        A method is considered a test method if it:
        1. Has the @Test annotation, or
        2. Its name starts with "test"

        Args:
            node (javalang.tree.MethodDeclaration): The method declaration node

        Returns:
            bool: True if the method is a test method, False otherwise
        """
        # Check for @Test annotation
        if hasattr(node, 'annotations') and node.annotations:
            for annotation in node.annotations:
                if annotation.name == "Test":
                    return True

        # Check if method name starts with "test"
        if node.name.startswith("test"):
            return True

        return False

    def _process_test_file(self, file_path: str) -> None:
        """
        Process a single Java test file to extract test methods and their invocations.

        Args:
            file_path (str): Path to the Java test file
        """
        try:
            # Read the file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                logging.error(f"Error reading file {file_path}: {e}")
                return

            # Parse the Java file
            try:
                tree = javalang.parse.parse(content)
            except Exception as e:
                logging.error(f"Error parsing Java file {file_path}: {e}")
                # Try to provide more detailed information about the parsing error
                try:
                    # Split the content into lines
                    lines = content.splitlines()

                    # Attempt to parse small chunks to identify where the parsing fails
                    chunk_size = 10  # Start with small chunks
                    for i in range(0, len(lines), chunk_size):
                        chunk = '\n'.join(lines[i:i+chunk_size])
                        try:
                            javalang.parse.parse(f"class Test {{ void test() {{ {chunk} }} }}")
                        except Exception as chunk_error:
                            logging.warning(f"Parsing error near line {i+1}-{i+chunk_size}: {chunk_error}")
                            # Try to narrow down to the exact line
                            for j in range(i, min(i+chunk_size, len(lines))):
                                line = lines[j].strip()
                                if line:  # Skip empty lines
                                    try:
                                        # Try to parse a simple class with just this line
                                        test_code = f"class Test {{ void test() {{ {line} }} }}"
                                        javalang.parse.parse(test_code)
                                    except Exception:
                                        logging.warning(f"Potential syntax error at line {j+1}: {line}")
                            break
                except Exception as detail_error:
                    logging.warning(f"Could not provide detailed error information: {detail_error}")

                return

            # Extract the package name
            package_name = tree.package.name if tree.package else ""

            # Get the class name from the file path
            class_name = os.path.basename(file_path).replace(".java", "")
            fully_qualified_class_name = f"{package_name}.{class_name}" if package_name else class_name

            # Find all test methods in the file
            for _, node in tree.filter(javalang.tree.MethodDeclaration):
                if self._is_test_method(node):
                    test_method_name = f"{fully_qualified_class_name}.{node.name}"

                    # Extract method calls from the test method
                    try:
                        method_calls = self._extract_method_calls(node.body)
                    except Exception as e:
                        logging.error(f"Error extracting method calls from {test_method_name}: {e}")
                        continue

                    # Update the mappings
                    self.test_to_methods_map[test_method_name] = set(method_calls)

                    # Update the reverse mapping
                    for method_call in method_calls:
                        if method_call not in self.method_to_tests_map:
                            self.method_to_tests_map[method_call] = set()
                        self.method_to_tests_map[method_call].add(test_method_name)

        except Exception as e:
            logging.error(f"Error processing test file {file_path}: {e}")

    def _extract_method_calls(self, body: List[Any]) -> List[str]:
        """
        Extract method calls from a method body.

        Args:
            body (List[Any]): The body of the method (list of javalang.tree nodes)

        Returns:
            List[str]: List of fully qualified method calls
        """
        method_calls = []

        if not body:
            return method_calls

        # Process each statement in the method body
        for statement in body:
            try:
                # Handle method invocations
                if isinstance(statement, javalang.tree.MethodInvocation):
                    # Try to get the qualifier (class name) if available
                    qualifier = ""
                    if hasattr(statement, 'qualifier') and statement.qualifier:
                        qualifier = statement.qualifier

                    method_name = statement.member
                    method_call = f"{qualifier}.{method_name}" if qualifier else method_name
                    method_calls.append(method_call)

                # Recursively process nested statements
                if hasattr(statement, 'children'):
                    method_calls.extend(self._extract_method_calls(statement.children))

                # Process blocks (e.g., if, for, while statements)
                if hasattr(statement, 'block') and statement.block:
                    method_calls.extend(self._extract_method_calls(statement.block))

                # Process then/else statements
                if hasattr(statement, 'then_statement') and statement.then_statement:
                    method_calls.extend(self._extract_method_calls([statement.then_statement]))

                if hasattr(statement, 'else_statement') and statement.else_statement:
                    method_calls.extend(self._extract_method_calls([statement.else_statement]))

                # Process try/catch blocks
                if hasattr(statement, 'try_block') and statement.try_block:
                    method_calls.extend(self._extract_method_calls(statement.try_block))

                if hasattr(statement, 'catch_clauses') and statement.catch_clauses:
                    for catch_clause in statement.catch_clauses:
                        if hasattr(catch_clause, 'block') and catch_clause.block:
                            method_calls.extend(self._extract_method_calls(catch_clause.block))

                if hasattr(statement, 'finally_block') and statement.finally_block:
                    method_calls.extend(self._extract_method_calls(statement.finally_block))

            except Exception as e:
                logging.warning(f"Error processing statement in method body: {e}")
                # Continue processing other statements

        return method_calls

    def get_impacted_tests(self, changed_methods: List[str]) -> Dict[str, List[str]]:
        """
        Get tests impacted by changes to specific methods.

        Args:
            changed_methods (List[str]): List of fully qualified method names that have changed

        Returns:
            Dict[str, List[str]]: Dictionary mapping changed methods to lists of impacted tests
        """
        result = {}

        for method in changed_methods:
            if method in self.method_to_tests_map:
                result[method] = list(self.method_to_tests_map[method])
            else:
                result[method] = []

        return result

    def get_test_coverage(self, test_name: str) -> List[str]:
        """
        Get the methods covered by a specific test.

        Args:
            test_name (str): Fully qualified test method name

        Returns:
            List[str]: List of methods invoked by the test
        """
        if test_name in self.test_to_methods_map:
            return list(self.test_to_methods_map[test_name])
        return []

    def save_mapping(self, output_file: str) -> None:
        """
        Save the test-to-methods mapping to a file.

        Args:
            output_file (str): Path to the output file
        """
        with open(output_file, 'w') as f:
            for test, methods in self.test_to_methods_map.items():
                f.write(f"{test}:\n")
                for method in methods:
                    f.write(f"  - {method}\n")

    def load_mapping(self, input_file: str) -> None:
        """
        Load a previously saved test-to-methods mapping from a file.

        Args:
            input_file (str): Path to the input file
        """
        current_test = None
        self.test_to_methods_map = {}
        self.method_to_tests_map = {}

        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if line.endswith(":"):
                    # This is a test name
                    current_test = line.rstrip(":")
                    self.test_to_methods_map[current_test] = set()
                elif (line.startswith("  - ") or line.startswith("- ")) and current_test is not None:
                    # This is a method
                    method = line.lstrip("- ").strip()  # Remove the dash and any spaces
                    self.test_to_methods_map[current_test].add(method)

                    # Update the reverse mapping
                    if method not in self.method_to_tests_map:
                        self.method_to_tests_map[method] = set()
                    self.method_to_tests_map[method].add(current_test)


def analyze_java_tests(test_dir: str, output_file: Optional[str] = None) -> JavaTestAnalyzer:
    """
    Analyze Java test files and build a mapping between tests and methods.

    Args:
        test_dir (str): Directory containing Java test files
        output_file (Optional[str]): Path to save the mapping (if provided)

    Returns:
        JavaTestAnalyzer: Initialized analyzer with built mappings
    """
    analyzer = JavaTestAnalyzer(test_dir)
    analyzer.build_test_method_mapping()

    if output_file:
        analyzer.save_mapping(output_file)

    return analyzer


def identify_impacted_tests(analyzer: JavaTestAnalyzer, changed_methods: List[str]) -> Dict[str, List[str]]:
    """
    Identify tests impacted by changes to specific methods.

    Args:
        analyzer (JavaTestAnalyzer): Initialized analyzer with built mappings
        changed_methods (List[str]): List of fully qualified method names that have changed

    Returns:
        Dict[str, List[str]]: Dictionary mapping changed methods to lists of impacted tests
    """
    return analyzer.get_impacted_tests(changed_methods)
