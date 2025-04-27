"""
Tests for the Java Test Runner module.
"""

import os
import pytest
from unittest.mock import patch, mock_open, MagicMock, call
from src.jade.java_test_runner import JavaTestRunner, run_impacted_tests, run_impacted_tests_from_analyzer_output

@pytest.fixture
def mock_subprocess(monkeypatch):
    """Fixture to mock subprocess.run"""
    mock_run = MagicMock()

    # Configure the mock to return a successful result by default
    mock_process = MagicMock()
    mock_process.stdout = "Tests run: 1, Failures: 0, Errors: 0, Skipped: 0"
    mock_process.returncode = 0
    mock_run.return_value = mock_process

    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run

@pytest.fixture
def mock_file_exists(monkeypatch):
    """Fixture to mock os.path.exists"""
    def mock_exists(path):
        # Simulate that test files exist
        if path.endswith(".java"):
            return True
        return False

    monkeypatch.setattr("os.path.exists", mock_exists)
    return mock_exists

@pytest.fixture
def mock_walk(monkeypatch):
    """Fixture to mock os.walk"""
    def mock_os_walk(directory):
        # Return a simple directory structure
        return [
            (os.path.join(directory, "com", "example"), [], ["MyTest.java", "OtherTest.java"])
        ]

    monkeypatch.setattr("os.walk", mock_os_walk)
    return mock_os_walk

def test_init():
    """Test initialization of JavaTestRunner"""
    # Test with default parameters
    runner = JavaTestRunner("/project")
    assert runner.project_dir == "/project"
    assert runner.build_tool == "maven"
    assert runner.test_dir.endswith(os.path.join("src", "test", "java"))

    # Test with custom parameters
    runner = JavaTestRunner("/project", "/custom/test/dir", "gradle")
    assert runner.project_dir == "/project"
    assert runner.test_dir == "/custom/test/dir"
    assert runner.build_tool == "gradle"

    # Test with java build tool
    runner = JavaTestRunner("/project", build_tool="java")
    assert runner.project_dir == "/project"
    assert runner.build_tool == "java"
    assert runner.test_dir.endswith(os.path.join("test"))

    # Test with unsupported build tool
    with pytest.raises(ValueError):
        JavaTestRunner("/project", build_tool="unsupported")

def test_group_tests_by_class():
    """Test grouping test methods by class"""
    runner = JavaTestRunner("/project")

    # Test with valid test names
    test_names = [
        "com.example.MyTest.testMethod1",
        "com.example.MyTest.testMethod2",
        "com.example.OtherTest.testMethod"
    ]

    result = runner._group_tests_by_class(test_names)

    assert "com.example.MyTest" in result
    assert "com.example.OtherTest" in result
    assert len(result["com.example.MyTest"]) == 2
    assert "testMethod1" in result["com.example.MyTest"]
    assert "testMethod2" in result["com.example.MyTest"]
    assert len(result["com.example.OtherTest"]) == 1
    assert "testMethod" in result["com.example.OtherTest"]

    # Test with invalid test name
    test_names = ["invalid"]
    result = runner._group_tests_by_class(test_names)
    assert len(result) == 0

def test_class_name_to_file_path(mock_file_exists):
    """Test converting class name to file path"""
    runner = JavaTestRunner("/project", "/test/dir")

    # Test with a class name that maps to an existing file
    file_path = runner._class_name_to_file_path("com.example.MyTest")
    assert file_path is not None
    assert file_path.endswith(os.path.join("com", "example", "MyTest.java"))

    # Test with a class name that doesn't map to an existing file
    # This should still return a path since our mock_file_exists returns True for all .java files
    file_path = runner._class_name_to_file_path("com.nonexistent.Test")
    assert file_path is not None

def test_run_maven_tests(mock_subprocess):
    """Test running tests with Maven"""
    runner = JavaTestRunner("/project")

    # Configure the mock to return a successful result
    mock_subprocess.return_value.stdout = "Tests run: 1, Failures: 0, Errors: 0, Skipped: 0"

    # Run a test
    results = runner._run_maven_tests("com.example.MyTest", ["testMethod"])

    # Check that subprocess.run was called with the correct arguments
    mock_subprocess.assert_called_once()
    args, kwargs = mock_subprocess.call_args
    assert args[0] == ["mvn", "test", "-Dtest=com.example.MyTest#testMethod"]
    assert kwargs["cwd"] == "/project"

    # Check the results
    assert "com.example.MyTest.testMethod" in results
    assert results["com.example.MyTest.testMethod"] is True

    # Test with a failing test
    mock_subprocess.reset_mock()
    mock_subprocess.return_value.stdout = "Tests run: 1, Failures: 1, Errors: 0, Skipped: 0"

    results = runner._run_maven_tests("com.example.MyTest", ["testMethod"])
    assert results["com.example.MyTest.testMethod"] is False

    # Test with multiple methods
    mock_subprocess.reset_mock()
    mock_subprocess.return_value.stdout = "Tests run: 2, Failures: 0, Errors: 0, Skipped: 0"

    results = runner._run_maven_tests("com.example.MyTest", ["testMethod1", "testMethod2"])
    assert "com.example.MyTest.testMethod1" in results
    assert "com.example.MyTest.testMethod2" in results

def test_run_gradle_tests(mock_subprocess):
    """Test running tests with Gradle"""
    runner = JavaTestRunner("/project", build_tool="gradle")

    # Configure the mock to return a successful result
    mock_subprocess.return_value.stdout = "SUCCESS"

    # Run a test
    results = runner._run_gradle_tests("com.example.MyTest", ["testMethod"])

    # Check that subprocess.run was called with the correct arguments
    mock_subprocess.assert_called_once()
    args, kwargs = mock_subprocess.call_args
    assert args[0] == ["gradle", "test", "--tests", "com.example.MyTest.{testMethod}"]
    assert kwargs["cwd"] == "/project"

    # Check the results
    assert "com.example.MyTest.testMethod" in results
    assert results["com.example.MyTest.testMethod"] is True

    # Test with a failing test
    mock_subprocess.reset_mock()
    mock_subprocess.return_value.stdout = "FAILED"

    results = runner._run_gradle_tests("com.example.MyTest", ["testMethod"])
    assert results["com.example.MyTest.testMethod"] is False

    # Test with multiple methods
    mock_subprocess.reset_mock()
    mock_subprocess.return_value.stdout = "SUCCESS"

    results = runner._run_gradle_tests("com.example.MyTest", ["testMethod1", "testMethod2"])
    assert "com.example.MyTest.testMethod1" in results
    assert "com.example.MyTest.testMethod2" in results

def test_run_impacted_tests(mock_subprocess, mock_file_exists):
    """Test running impacted tests"""
    runner = JavaTestRunner("/project")

    # Configure the mock to return a successful result
    mock_subprocess.return_value.stdout = "Tests run: 1, Failures: 0, Errors: 0, Skipped: 0"

    # Run impacted tests
    impacted_tests = [
        "com.example.MyTest.testMethod1",
        "com.example.MyTest.testMethod2",
        "com.example.OtherTest.testMethod"
    ]

    results = runner.run_impacted_tests(impacted_tests)

    # Check that subprocess.run was called twice (once for each class)
    assert mock_subprocess.call_count == 2

    # Check the results
    assert len(results) == 3
    assert results["com.example.MyTest.testMethod1"] is True
    assert results["com.example.MyTest.testMethod2"] is True
    assert results["com.example.OtherTest.testMethod"] is True

def test_run_impacted_tests_helper(mock_subprocess, mock_file_exists):
    """Test the run_impacted_tests helper function"""
    # Configure the mock to return a successful result
    mock_subprocess.return_value.stdout = "Tests run: 1, Failures: 0, Errors: 0, Skipped: 0"

    # Run impacted tests
    impacted_tests = [
        "com.example.MyTest.testMethod1",
        "com.example.MyTest.testMethod2"
    ]

    results = run_impacted_tests("/project", impacted_tests)

    # Check that subprocess.run was called
    mock_subprocess.assert_called()

    # Check the results
    assert len(results) == 2
    assert results["com.example.MyTest.testMethod1"] is True
    assert results["com.example.MyTest.testMethod2"] is True

def test_run_impacted_tests_from_analyzer_output(mock_subprocess, mock_file_exists):
    """Test the run_impacted_tests_from_analyzer_output helper function"""
    # Configure the mock to return a successful result
    mock_subprocess.return_value.stdout = "Tests run: 1, Failures: 0, Errors: 0, Skipped: 0"

    # Create analyzer output
    analyzer_output = {
        "com.example.ClassA.methodA": ["com.example.MyTest.testMethod1"],
        "com.example.ClassB.methodB": ["com.example.MyTest.testMethod2", "com.example.OtherTest.testMethod"]
    }

    results = run_impacted_tests_from_analyzer_output("/project", analyzer_output)

    # Check that subprocess.run was called
    mock_subprocess.assert_called()

    # Check the results
    assert len(results) == 3
    assert results["com.example.MyTest.testMethod1"] is True
    assert results["com.example.MyTest.testMethod2"] is True
    assert results["com.example.OtherTest.testMethod"] is True

def test_run_test_class_file_not_found():
    """Test running tests when the test file is not found"""
    runner = JavaTestRunner("/project")

    # Mock _class_name_to_file_path to return None
    runner._class_name_to_file_path = MagicMock(return_value=None)

    results = runner._run_test_class("com.example.MyTest", ["testMethod"])

    # Check that the test is marked as failed
    assert results["com.example.MyTest.testMethod"] is False

def test_run_test_class_unsupported_build_tool():
    """Test running tests with an unsupported build tool"""
    runner = JavaTestRunner("/project")

    # Mock _class_name_to_file_path to return a valid path
    runner._class_name_to_file_path = MagicMock(return_value="/path/to/test.java")

    # Set an unsupported build tool
    runner.build_tool = "unsupported"

    results = runner._run_test_class("com.example.MyTest", ["testMethod"])

    # Check that the test is marked as failed
    assert results["com.example.MyTest.testMethod"] is False

def test_run_maven_tests_exception(mock_subprocess):
    """Test handling exceptions when running Maven tests"""
    runner = JavaTestRunner("/project")

    # Configure the mock to raise an exception
    mock_subprocess.side_effect = Exception("Command failed")

    results = runner._run_maven_tests("com.example.MyTest", ["testMethod"])

    # Check that the test is marked as failed
    assert results["com.example.MyTest.testMethod"] is False

def test_run_gradle_tests_exception(mock_subprocess):
    """Test handling exceptions when running Gradle tests"""
    runner = JavaTestRunner("/project", build_tool="gradle")

    # Configure the mock to raise an exception
    mock_subprocess.side_effect = Exception("Command failed")

    results = runner._run_gradle_tests("com.example.MyTest", ["testMethod"])

    # Check that the test is marked as failed
    assert results["com.example.MyTest.testMethod"] is False

def test_run_java_tests(mock_subprocess, mock_file_exists):
    """Test running tests with direct Java commands"""
    runner = JavaTestRunner("/project", build_tool="java")

    # Configure the mock to return a successful result for compilation
    compile_process = MagicMock()
    compile_process.returncode = 0
    compile_process.stdout = ""

    # Configure the mock to return a successful result for test execution
    run_process = MagicMock()
    run_process.returncode = 0
    run_process.stdout = "OK (1 test)"

    # Set up the mock to return different results for different calls
    mock_subprocess.side_effect = [compile_process, run_process]

    # Run a test
    results = runner._run_java_tests("com.example.MyTest", ["testMethod"], "/path/to/MyTest.java")

    # Check that subprocess.run was called twice (once for compile, once for run)
    assert mock_subprocess.call_count == 2

    # Check the first call (compile)
    compile_args, compile_kwargs = mock_subprocess.call_args_list[0]
    assert compile_args[0][0] == "javac"
    assert "/path/to/MyTest.java" in compile_args[0]

    # Check the second call (run)
    run_args, run_kwargs = mock_subprocess.call_args_list[1]
    assert run_args[0][0] == "java"
    assert "org.junit.runner.JUnitCore" in run_args[0]
    assert "com.example.MyTest#testMethod" in run_args[0]

    # Check the results
    assert "com.example.MyTest.testMethod" in results
    assert results["com.example.MyTest.testMethod"] is True

    # Test with a failing test
    mock_subprocess.reset_mock()

    # Configure the mock to return a successful result for compilation
    compile_process = MagicMock()
    compile_process.returncode = 0
    compile_process.stdout = ""

    # Configure the mock to return a failing result for test execution
    run_process = MagicMock()
    run_process.returncode = 1
    run_process.stdout = "FAILURES!!!"

    # Set up the mock to return different results for different calls
    mock_subprocess.side_effect = [compile_process, run_process]

    results = runner._run_java_tests("com.example.MyTest", ["testMethod"], "/path/to/MyTest.java")
    assert results["com.example.MyTest.testMethod"] is False

    # Test with compilation failure
    mock_subprocess.reset_mock()

    # Configure the mock to return a failing result for compilation
    compile_process = MagicMock()
    compile_process.returncode = 1
    compile_process.stderr = "Compilation error"

    # Set up the mock to return the failing compilation result
    mock_subprocess.side_effect = [compile_process]

    results = runner._run_java_tests("com.example.MyTest", ["testMethod"], "/path/to/MyTest.java")
    assert results["com.example.MyTest.testMethod"] is False

def test_run_java_tests_exception(mock_subprocess):
    """Test handling exceptions when running Java tests"""
    runner = JavaTestRunner("/project", build_tool="java")

    # Configure the mock to raise an exception
    mock_subprocess.side_effect = Exception("Command failed")

    results = runner._run_java_tests("com.example.MyTest", ["testMethod"], "/path/to/MyTest.java")

    # Check that the test is marked as failed
    assert results["com.example.MyTest.testMethod"] is False

def test_run_impacted_tests_with_java(mock_subprocess, mock_file_exists):
    """Test running impacted tests with Java build tool"""
    runner = JavaTestRunner("/project", build_tool="java")

    # Configure the mock to return a successful result for compilation
    compile_process = MagicMock()
    compile_process.returncode = 0
    compile_process.stdout = ""

    # Configure the mock to return a successful result for test execution
    run_process = MagicMock()
    run_process.returncode = 0
    run_process.stdout = "OK (1 test)"

    # Set up the mock to return different results for different calls
    mock_subprocess.side_effect = [compile_process, run_process, compile_process, run_process]

    # Run impacted tests
    impacted_tests = [
        "com.example.MyTest.testMethod1",
        "com.example.OtherTest.testMethod"
    ]

    results = runner.run_impacted_tests(impacted_tests)

    # Check the results
    assert len(results) == 2
    assert results["com.example.MyTest.testMethod1"] is True
    assert results["com.example.OtherTest.testMethod"] is True
