import subprocess


def get_diff_output(base_commit: str) -> str:
    cmd = ["git", "diff", "--unified=0", base_commit, "HEAD", "--", "*.java"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout