import subprocess
from unittest.mock import patch

from src.jade.git import *


def test_get_diff_output():
    # Mock the subprocess.run response
    mock_output = "diff --git a/File1.java b/File1.java\n@ -1,1 +1,1 @ class Test {}\n"
    mock_result = subprocess.CompletedProcess(
        args=["git", "diff"], returncode=0, stdout=mock_output, stderr=""
    )

    with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
        base_commit = "main"
        result = get_diff_output(base_commit)

        # Assertions
        mock_subprocess.assert_called_once_with(
            ["git", "diff", "--unified=0", base_commit, "HEAD", "--", "*.java"],
            capture_output=True,
            text=True,
        )
        assert result == mock_output

