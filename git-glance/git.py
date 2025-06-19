import subprocess
from pathlib import Path

def run_git_command(path: str, args: list[str]) -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=path,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {result.stderr.strip()}")
    return result.stdout.strip()

def is_git_repo(path: str) -> bool:
    try:
        output = run_git_command(path, ["rev-parse", "--is-inside-work-tree"])
        return output == "true"
    except RuntimeError:
        return False
    

def fetch_repo(path: str) -> None:
    try:
        run_git_command(path, ["fetch"])
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to fetch repo at {path}: {e}")

def get_repo_status(path: str) -> dict:
    path_obj = Path(path).expanduser().resolve()
    status = {
        "path": Path(path).expanduser().resolve(),
        "branch": "",
        "uncomitted": 0,
        "unpushed": 0,
        "needs_pull": False
    }

    try:
        status["branch"] = run_git_command(path, ["rev-parse", "--abbrev-ref", "HEAD"])
        uncommitted_output = run_git_command(path, ["status", "--porcelain"])
        status["uncomitted"] = len(uncommitted_output.splitlines()) if uncommitted_output else 0

        try:
            unpushed = run_git_command(path, ["rev-list", "--count", "@{u}..HEAD"])
            status["unpushed"] = int(unpushed)
        except RuntimeError:
            status["unpushed"] = 0
        
        try:
            needs_pull = run_git_command(path, ["rev-list", "--count", "HEAD..@{u}"])
            status["needs_pull"] = int(needs_pull) > 0
        except RuntimeError:
            status["needs_pull"] = False

    except RuntimeError as e:
        status["error"] = str(e)

    return status