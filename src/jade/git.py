import subprocess


def get_previous_commit(n: int = 1) -> str:
    """
    Get the hash of the nth previous commit from HEAD.

    Args:
        n (int): Number of commits to go back from HEAD. Default is 1.

    Returns:
        str: The commit hash
    """
    cmd = ["git", "rev-parse", f"HEAD~{n}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Git rev-parse failed: {result.stderr.strip()}")

    return result.stdout.strip()


def get_branch_head(branch: str) -> str:
    """
    Get the commit hash of the HEAD of a branch.

    Args:
        branch (str): Name of the branch

    Returns:
        str: The commit hash of the branch HEAD
    """
    cmd = ["git", "rev-parse", branch]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Git rev-parse failed: {result.stderr.strip()}")

    return result.stdout.strip()


def get_affected_files(base_commit: str, target_commit: str = "HEAD") -> list[str]:
    cmd = ["git", "diff", "--name-only", base_commit, target_commit]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Git diff failed: {result.stderr.strip()}")

    return result.stdout.strip().splitlines()


def get_git_diff(base_commit: str, target_commit: str = "HEAD") -> str:
    cmd = [
        "git",
        "-c", "diff.algorithm=histogram",
        "-c", "core.pager=",
        "diff",
        "-U0",
        "--no-color",
        "--ignore-all-space",
        base_commit,
        target_commit,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Git diff failed: {result.stderr.strip()}")
    return result.stdout
