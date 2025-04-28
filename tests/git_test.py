from unittest.mock import patch

from src.jade.git import *

def test_get_previous_commit():
    # Mock output of the `git rev-parse HEAD~1` command
    mock_output = "a3912c84e9f1b7c0037f283ed14021ba9bed5362"

    # Prepare the mock CompletedProcess response
    mock_result = subprocess.CompletedProcess(
        args=["git", "rev-parse", "HEAD~1"], returncode=0, stdout=mock_output, stderr=""
    )

    # Mock subprocess.run to return the mocked output
    with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
        result = get_previous_commit(1)  # Call the function being tested

        # Assertions to check the behavior
        mock_subprocess.assert_called_once_with(
            ["git", "rev-parse", "HEAD~1"],
            capture_output=True,
            text=True,
        )
        # Expected result based on the mock output
        assert result == "a3912c84e9f1b7c0037f283ed14021ba9bed5362"

def test_get_previous_commit_with_n():
    # Mock output of the `git rev-parse HEAD~3` command
    mock_output = "9961f321e9f1b7c0037f283ed14021ba9bed5362"

    # Prepare the mock CompletedProcess response
    mock_result = subprocess.CompletedProcess(
        args=["git", "rev-parse", "HEAD~3"], returncode=0, stdout=mock_output, stderr=""
    )

    # Mock subprocess.run to return the mocked output
    with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
        result = get_previous_commit(3)  # Call the function being tested

        # Assertions to check the behavior
        mock_subprocess.assert_called_once_with(
            ["git", "rev-parse", "HEAD~3"],
            capture_output=True,
            text=True,
        )
        # Expected result based on the mock output
        assert result == "9961f321e9f1b7c0037f283ed14021ba9bed5362"

def test_get_branch_head():
    # Mock output of the `git rev-parse main` command
    mock_output = "e74f546d5ff6481337cee804403985962440319f"

    # Prepare the mock CompletedProcess response
    mock_result = subprocess.CompletedProcess(
        args=["git", "rev-parse", "main"], returncode=0, stdout=mock_output, stderr=""
    )

    # Mock subprocess.run to return the mocked output
    with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
        result = get_branch_head("main")  # Call the function being tested

        # Assertions to check the behavior
        mock_subprocess.assert_called_once_with(
            ["git", "rev-parse", "main"],
            capture_output=True,
            text=True,
        )
        # Expected result based on the mock output
        assert result == "e74f546d5ff6481337cee804403985962440319f"

def test_get_diff_files():
    # Mock output of the `git diff --name-only` command
    mock_output = """
real-time-composite-app/src/main/java/com/bidfx/composite/quality/MetricsAggregator.java
""".strip()

    # Prepare the mock CompletedProcess response
    mock_result = subprocess.CompletedProcess(
        args=["git", "diff", "--name-only"], returncode=0, stdout=mock_output, stderr=""
    )

    # Mock subprocess.run to return the mocked output
    with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
        base_commit = "e74f546d5ff6481337cee804403985962440319f"
        result = get_affected_files(base_commit)  # Call the function being tested

        # Assertions to check the behavior
        mock_subprocess.assert_called_once_with(
            ["git", "diff", "--name-only", base_commit, "HEAD"],
            capture_output=True,
            text=True,
        )
        # Expected result based on the mock output
        assert result == [
            "real-time-composite-app/src/main/java/com/bidfx/composite/quality/MetricsAggregator.java"
        ]

def test_get_diff_output():
    mock_output = (
        "diff --git a/real-time-composite-app/src/main/java/com/bidfx/composite/quality/MetricsAggregator.java "
        "b/real-time-composite-app/src/main/java/com/bidfx/composite/quality/MetricsAggregator.java\n"
        "index 51ddf454..8d013d9b 100644\n"
        "--- a/real-time-composite-app/src/main/java/com/bidfx/composite/quality/MetricsAggregator.java\n"
        "+++ b/real-time-composite-app/src/main/java/com/bidfx/composite/quality/MetricsAggregator.java\n"
        "@@ -84,0 +85,4 @@ public class MetricsAggregator implements CompositeSubscriber\n"
        "+        if (nextIntervalMillis == 0)\n"
        "+        {\n"
        "+            nextIntervalMillis = intervalMillis;\n"
        "+        }\n"
    )

    # Mock the subprocess.run response
    mock_result = subprocess.CompletedProcess(
        args=[
            "git",
            "-c", "diff.algorithm=histogram",
            "-c", "core.pager=",
            "diff",
            "-U0",
            "--no-color",
            "--ignore-all-space",
            "e74f546d",
            "HEAD",
        ],
        returncode=0,
        stdout=mock_output,
        stderr="",
    )

    # Mock subprocess.run to return your mock_output when called
    with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
        base_commit = "e74f546d"
        result = get_git_diff(base_commit)

        # Assertions to ensure the function works as expected
        mock_subprocess.assert_called_once_with(
            [
                "git",
                "-c", "diff.algorithm=histogram",
                "-c", "core.pager=",
                "diff",
                "-U0",
                "--no-color",
                "--ignore-all-space",
                base_commit,
                "HEAD",
            ],
            capture_output=True,
            text=True,
        )
        assert result == mock_output
