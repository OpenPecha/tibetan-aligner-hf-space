import tempfile
from pathlib import Path

from github_utils import clone_repo, commit_to_orphan_branch, get_branches, repo_exists


def test_repo_exists():
    assert repo_exists("TM0731") == True


def test_clone_repo():
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        tm_path = clone_repo("TM0731", output_dir)
        assert tm_path.exists() == True


def create_tm_dir(path: Path):
    path.mkdir(exist_ok=True, parents=True)
    bo_file = path / "bo.txt"
    bo_file.write_text("text")
    en_file = path / "en.txt"
    en_file.write_text("text")
    readme_file = path / "README.md"
    readme_file.write_text("text")
    return path


def test_commit_to_orphan_branch():
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        tm_path = clone_repo("TM0731", output_dir)
        next_version = "v1"
        tm_files_path = create_tm_dir((output_dir / "TM0731-files"))
        commit_to_orphan_branch(
            tm_path, next_version, tm_files_path.iterdir(), "added alignment"
        )
        print(tm_files_path)


def test_get_branches():
    branches = get_branches("TM0731")
    assert branches[0]["name"] == "main"
