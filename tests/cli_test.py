"""
Tests for the CLI module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.jade.cli import parse_args, get_comparison_commits, get_changed_methods, main


@pytest.fixture
def mock_git():
    """Fixture to mock git functions."""
    with patch("src.jade.cli.git") as mock_git:
        # Mock get_previous_commit
        mock_git.get_previous_commit.return_value = "abc123"
        
        # Mock get_branch_head
        mock_git.get_branch_head.return_value = "def456"
        
        # Mock get_git_diff
        mock_git.get_git_diff.return_value = "diff output"
        
        # Mock get_affected_files
        mock_git.get_affected_files.return_value = ["file1.java", "file2.java"]
        
        yield mock_git


@pytest.fixture
def mock_java_test_analyzer():
    """Fixture to mock java_test_analyzer functions."""
    with patch("src.jade.cli.java_test_analyzer") as mock_analyzer:
        # Mock analyze_java_tests
        mock_analyzer_instance = MagicMock()
        mock_analyzer.analyze_java_tests.return_value = mock_analyzer_instance
        
        # Mock identify_impacted_tests
        mock_analyzer.identify_impacted_tests.return_value = {
            "com.example.SomeClass.someMethod": ["com.example.SomeClassTest.testSomeMethod"]
        }
        
        yield mock_analyzer


@pytest.fixture
def mock_java_test_runner():
    """Fixture to mock java_test_runner functions."""
    with patch("src.jade.cli.java_test_runner") as mock_runner:
        # Mock run_impacted_tests_from_analyzer_output
        mock_runner.run_impacted_tests_from_analyzer_output.return_value = {
            "com.example.SomeClassTest.testSomeMethod": True
        }
        
        yield mock_runner


def test_parse_args():
    """Test parsing command-line arguments."""
    with patch("sys.argv", ["jade", "-c", "1"]):
        args = parse_args()
        assert args.commits_back == 1
        assert args.project_dir == "."
        assert args.build_tool == "maven"
        assert not args.tests_only
        assert not args.run_tests


def test_get_comparison_commits_with_commits_back(mock_git):
    """Test get_comparison_commits with -c option."""
    args = MagicMock()
    args.commits_back = 1
    args.branch = None
    args.commit = None
    
    base_commit, target_commit = get_comparison_commits(args)
    
    mock_git.get_previous_commit.assert_called_once_with(1)
    assert base_commit == "abc123"
    assert target_commit == "HEAD"


def test_get_comparison_commits_with_branch(mock_git):
    """Test get_comparison_commits with --branch option."""
    args = MagicMock()
    args.commits_back = None
    args.branch = ["feature"]
    args.commit = None
    
    base_commit, target_commit = get_comparison_commits(args)
    
    mock_git.get_branch_head.assert_called_once_with("feature")
    assert base_commit == "def456"
    assert target_commit == "HEAD"


def test_get_comparison_commits_with_two_branches(mock_git):
    """Test get_comparison_commits with two --branch options."""
    args = MagicMock()
    args.commits_back = None
    args.branch = ["feature1", "feature2"]
    args.commit = None
    
    base_commit, target_commit = get_comparison_commits(args)
    
    mock_git.get_branch_head.assert_any_call("feature1")
    mock_git.get_branch_head.assert_any_call("feature2")
    assert base_commit == "def456"
    assert target_commit == "def456"


def test_get_changed_methods(mock_git):
    """Test get_changed_methods."""
    base_commit = "abc123"
    target_commit = "def456"
    project_dir = "."
    
    changed_methods = get_changed_methods(base_commit, target_commit, project_dir)
    
    mock_git.get_git_diff.assert_called_once_with(base_commit, target_commit)
    mock_git.get_affected_files.assert_called_once_with(base_commit, target_commit)
    assert changed_methods == ["com.example.SomeClass.someMethod"]  # Placeholder value


def test_main_with_tests_only(mock_git, mock_java_test_analyzer, mock_java_test_runner):
    """Test main function with --tests-only option."""
    with patch("sys.argv", ["jade", "-c", "1", "--tests-only"]):
        with patch("builtins.print") as mock_print:
            main()
            
            # Check that the correct functions were called
            mock_git.get_previous_commit.assert_called_once_with(1)
            mock_java_test_analyzer.analyze_java_tests.assert_called_once()
            mock_java_test_analyzer.identify_impacted_tests.assert_called_once()
            
            # Check that run_impacted_tests_from_analyzer_output was not called
            mock_java_test_runner.run_impacted_tests_from_analyzer_output.assert_not_called()
            
            # Check that the correct output was printed
            mock_print.assert_any_call("\nImpacted tests:")


def test_main_with_run_tests(mock_git, mock_java_test_analyzer, mock_java_test_runner):
    """Test main function with --run-tests option."""
    with patch("sys.argv", ["jade", "-c", "1", "--run-tests"]):
        with patch("builtins.print") as mock_print:
            main()
            
            # Check that the correct functions were called
            mock_git.get_previous_commit.assert_called_once_with(1)
            mock_java_test_analyzer.analyze_java_tests.assert_called_once()
            mock_java_test_analyzer.identify_impacted_tests.assert_called_once()
            
            # Check that run_impacted_tests_from_analyzer_output was called
            mock_java_test_runner.run_impacted_tests_from_analyzer_output.assert_called_once()
            
            # Check that the correct output was printed
            mock_print.assert_any_call("\nRunning impacted tests...")
            mock_print.assert_any_call("\nTest results:")